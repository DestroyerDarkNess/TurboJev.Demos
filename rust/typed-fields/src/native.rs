//! Thin owner of the published C ABI; no scoring or model decisions occur here.
use libloading::Library;
use serde_json::Value;
use std::ffi::{c_char, c_void, CStr, CString};
use std::io::{Read, Write};
use std::path::Path;

/// Download only the matching runtime from the public NuGet package.
pub fn install(
    directory: &Path,
    rid: &str,
    version: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    let marker = directory.join(".installed");
    if marker.is_file() {
        return Ok(());
    }
    let url = format!(
        "https://api.nuget.org/v3-flatcontainer/turbojev/{version}/turbojev.{version}.nupkg"
    );
    #[cfg(windows)]
    let agent = ureq::AgentBuilder::new()
        .tls_connector(std::sync::Arc::new(native_tls::TlsConnector::new()?))
        .build();
    #[cfg(not(windows))]
    let agent = ureq::Agent::new();
    let response = agent.get(&url).call()?;
    let total = response
        .header("Content-Length")
        .and_then(|value| value.parse::<usize>().ok());
    let mut source = response.into_reader();
    let mut bytes = Vec::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let count = source.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        bytes.extend_from_slice(&buffer[..count]);
        if bytes.len() > 512 * 1024 * 1024 {
            return Err("Native package exceeds 512 MiB".into());
        }
        if let Some(total) = total {
            print!(
                "\rDownloading TurboJev native package: {:.1}%",
                bytes.len() as f64 * 100.0 / total.max(1) as f64
            );
            std::io::stdout().flush()?;
        }
    }
    println!();
    let mut archive = zip::ZipArchive::new(std::io::Cursor::new(bytes))?;
    let prefix = format!("runtimes/{rid}/native/");
    std::fs::create_dir_all(directory)?;
    let mut extracted = 0;
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let Some(name) = entry.name().strip_prefix(&prefix).map(str::to_owned) else {
            continue;
        };
        if name.is_empty() || name.contains(['/', '\\']) || name == ".." {
            continue;
        }
        let mut file = std::fs::File::create(directory.join(name))?;
        std::io::copy(&mut entry, &mut file)?;
        extracted += 1;
    }
    if extracted < 8 {
        return Err(format!("Published package lacks the complete {rid} runtime").into());
    }
    std::fs::write(marker, version)?;
    Ok(())
}

type Open = unsafe extern "C" fn(*const c_char, *mut *mut c_void) -> i32;
type Call = unsafe extern "C" fn(*mut c_void, *const c_char, *mut *mut c_char) -> i32;
type Close = unsafe extern "C" fn(*mut c_void) -> i32;
type Free = unsafe extern "C" fn(*mut c_char);
type LastError = unsafe extern "C" fn() -> *const c_char;

pub struct Engine {
    _library: Library,
    handle: *mut c_void,
    evaluate: Call,
    generate: Call,
    close: Close,
    free: Free,
    last_error: LastError,
}
impl Engine {
    pub fn open(path: &Path, options: &Value) -> Result<Self, Box<dyn std::error::Error>> {
        // Safety: signatures are the published UTF-8 C ABI; the library remains owned
        // until after handle close. All calls stay on the creating thread.
        unsafe {
            #[cfg(windows)]
            let library: Library = libloading::os::windows::Library::load_with_flags(
                path,
                0x00000100 | 0x00001000, // DLL_LOAD_DIR | DEFAULT_DIRS, including sibling dependencies
            )?
            .into();
            #[cfg(not(windows))]
            let library = Library::new(path)?;
            let open = *library.get::<Open>(b"tj_engine_open_json\0")?;
            let evaluate = *library.get::<Call>(b"tj_engine_evaluate_json\0")?;
            let generate = *library.get::<Call>(b"tj_engine_generate_json\0")?;
            let close = *library.get::<Close>(b"tj_engine_close\0")?;
            let free = *library.get::<Free>(b"tj_string_free\0")?;
            let last_error = *library.get::<LastError>(b"tj_last_error_message\0")?;
            let mut handle = std::ptr::null_mut();
            if open(CString::new(options.to_string())?.as_ptr(), &mut handle) != 0 {
                return Err(CStr::from_ptr(last_error())
                    .to_string_lossy()
                    .into_owned()
                    .into());
            }
            Ok(Self {
                _library: library,
                handle,
                evaluate,
                generate,
                close,
                free,
                last_error,
            })
        }
    }
    pub fn call(
        &self,
        request: &Value,
        generate: bool,
    ) -> Result<Value, Box<dyn std::error::Error>> {
        let input = CString::new(request.to_string())?;
        let mut output = std::ptr::null_mut();
        unsafe {
            let call = if generate {
                self.generate
            } else {
                self.evaluate
            };
            if call(self.handle, input.as_ptr(), &mut output) != 0 {
                return Err(CStr::from_ptr((self.last_error)())
                    .to_string_lossy()
                    .into_owned()
                    .into());
            }
            if output.is_null() {
                return Err("Native runtime returned a null output pointer".into());
            }
            let json = CStr::from_ptr(output).to_bytes().to_vec();
            (self.free)(output);
            Ok(serde_json::from_slice(&json)?)
        }
    }
    pub fn close(mut self) -> Result<(), Box<dyn std::error::Error>> {
        let status = unsafe { (self.close)(self.handle) };
        self.handle = std::ptr::null_mut();
        if status != 0 {
            return Err(unsafe {
                CStr::from_ptr((self.last_error)())
                    .to_string_lossy()
                    .into_owned()
            }
            .into());
        }
        Ok(())
    }
}
impl Drop for Engine {
    fn drop(&mut self) {
        if !self.handle.is_null() {
            unsafe {
                (self.close)(self.handle);
            }
        }
    }
}
