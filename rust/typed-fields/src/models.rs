use sha2::{Digest, Sha256};
use std::{
    fs::{self, File},
    io::{Read, Write},
    path::{Path, PathBuf},
    time::Instant,
};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
pub fn hash(path: &Path) -> Result<String> {
    let mut input = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = vec![0; 1024 * 1024];
    loop {
        let count = input.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}
pub fn gguf(path: &Path) -> Result<PathBuf> {
    let mut magic = [0; 4];
    File::open(path)?.read_exact(&mut magic)?;
    if magic != *b"GGUF" {
        return Err("Not a GGUF file".into());
    }
    Ok(path.canonicalize()?)
}
pub fn download(name: &str, url: &str, size: u64, expected_hash: Option<&str>) -> Result<PathBuf> {
    let home = std::env::var_os("USERPROFILE")
        .or_else(|| std::env::var_os("HOME"))
        .ok_or("No user home directory")?;
    let directory = PathBuf::from(home).join(".cache/turbojev");
    fs::create_dir_all(&directory)?;
    let path = directory.join(name);
    if gguf(&path).is_ok()
        && fs::metadata(&path)?.len() == size
        && expected_hash.is_none_or(|expected| hash(&path).is_ok_and(|actual| actual == expected))
    {
        println!("Model cache hit: {name}");
        return Ok(path);
    }
    let temporary = path.with_extension("gguf.part");
    let result = (|| -> Result<()> {
        #[cfg(windows)]
        let agent = ureq::AgentBuilder::new()
            .tls_connector(std::sync::Arc::new(native_tls::TlsConnector::new()?))
            .build();
        #[cfg(not(windows))]
        let agent = ureq::Agent::new();
        let mut source = agent.get(url).call()?.into_reader();
        let mut target = File::create(&temporary)?;
        let started = Instant::now();
        let mut previous = 0.;
        let mut received = 0u64;
        let mut buffer = vec![0; 1024 * 1024];
        loop {
            let count = source.read(&mut buffer)?;
            if count == 0 {
                break;
            }
            received += count as u64;
            if received > size {
                return Err("Download exceeds expected size".into());
            }
            target.write_all(&buffer[..count])?;
            let elapsed = started.elapsed().as_secs_f64();
            if elapsed - previous > 0.2 || received == size {
                previous = elapsed;
                let ratio = received as f64 / size as f64;
                let speed = received as f64 / elapsed.max(0.001);
                let filled = (ratio * 28.) as usize;
                print!(
                    "\r[{}{}] {:.1}% {:.0}/{:.0} MiB {:.1} MiB/s ETA {:.0}s   ",
                    "#".repeat(filled),
                    "-".repeat(28 - filled),
                    ratio * 100.,
                    received as f64 / 1048576.,
                    size as f64 / 1048576.,
                    speed / 1048576.,
                    (size - received) as f64 / speed
                );
                std::io::stdout().flush()?;
            }
        }
        drop(target);
        println!();
        if received != size {
            return Err("Incomplete model download".into());
        }
        gguf(&temporary)?;
        if let Some(expected) = expected_hash {
            if hash(&temporary)? != expected {
                return Err("Model SHA-256 mismatch".into());
            }
        }
        fs::rename(&temporary, &path)?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    result?;
    Ok(path)
}
