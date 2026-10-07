mod models;
mod native;

use base64::{engine::general_purpose::STANDARD, Engine as _};
use clap::Parser;
use serde_json::{json, Value};
use std::{
    collections::HashSet,
    fs,
    path::{Path, PathBuf},
    time::Instant,
};

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
const ROOT: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/..");
const VISION: &str = "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/f6d5376be1edb4d416d56da11e5397a961aca8ae/";

#[derive(Parser)]
#[command(about = "Published TurboJev typed decisions and real GGUF inference; no local SDK build")]
struct Options {
    #[arg(default_value="ticket", value_parser=["ticket","fields","fair-die","receipt","receipt-us"])]
    example: String,
    #[arg(long,default_value="cpu",value_parser=["cpu","gpu"])]
    device: String,
    #[arg(long)]
    model: Option<PathBuf>,
    #[arg(long)]
    mmproj: Option<PathBuf>,
    #[arg(long)]
    image: Option<PathBuf>,
    #[arg(long)]
    fields: Option<String>,
    #[arg(long)]
    reference_labels: bool,
    #[arg(long)]
    all_permutations: bool,
    #[arg(long, default_value_t=64, value_parser=clap::value_parser!(u32).range(1..=32768))]
    max_tokens: u32,
    #[arg(long)]
    output: Option<PathBuf>,
    /// Directory containing the matching public-package C ABI and its dependencies.
    #[arg(long)]
    native_dir: Option<PathBuf>,
}
impl Options {
    fn vision(&self) -> bool {
        matches!(self.example.as_str(), "receipt" | "receipt-us")
    }
}
fn read_json(path: impl AsRef<Path>) -> Result<Value> {
    Ok(serde_json::from_slice(&fs::read(path)?)?)
}
fn runtime(options: &Options) -> Result<PathBuf> {
    let name = if cfg!(windows) {
        "turbojev_capi.dll"
    } else if cfg!(target_os = "macos") {
        "libturbojev_capi.dylib"
    } else {
        "libturbojev_capi.so"
    };
    if let Some(directory) = &options.native_dir {
        return Ok(directory.join(name).canonicalize()?);
    }
    if !cfg!(windows) {
        return Err("No Linux/macOS native package published for 0.30.1; provide --native-dir from a matching registry package".into());
    }
    let rid = match std::env::consts::ARCH {
        "x86" => "win-x86",
        "x86_64" => "win-x64",
        "aarch64" => "win-arm64",
        _ => return Err("No matching published architecture".into()),
    };
    for folder in [
        ".artifacts/nuget-registry/turbojev/0.30.1",
        ".artifacts/rust-native/0.30.1",
    ] {
        let path = Path::new(ROOT)
            .join(folder)
            .join("runtimes")
            .join(rid)
            .join("native")
            .join(name);
        if path.is_file() {
            return Ok(path.canonicalize()?);
        }
    }
    let status = std::process::Command::new("powershell.exe")
        .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-File"])
        .arg(Path::new(env!("CARGO_MANIFEST_DIR")).join("setup-native.ps1"))
        .status()?;
    if !status.success() {
        return Err("Registry runtime installation failed".into());
    }
    Ok(Path::new(ROOT)
        .join(".artifacts/rust-native/0.30.1/runtimes")
        .join(rid)
        .join("native")
        .join(name)
        .canonicalize()?)
}
fn request(options: &Options, report: &mut Value) -> Result<Option<Value>> {
    if !options.vision()
        && (options.image.is_some()
            || options.fields.is_some()
            || options.mmproj.is_some()
            || options.reference_labels)
    {
        return Err("Image options require a receipt example".into());
    }
    if options.all_permutations && options.example != "fair-die" {
        return Err("all-permutations requires fair-die".into());
    }
    if options.example == "fair-die" {
        return Ok(None);
    }
    if !options.vision() {
        let mut value = read_json(
            Path::new(ROOT)
                .join("demo-requests")
                .join(format!("{}.json", options.example)),
        )?;
        if options.example == "fields" {
            value["text_max_tokens"] = json!(options.max_tokens);
            value["numeric_max_tokens"] = json!(options.max_tokens);
        }
        return Ok(Some(value));
    }
    if options.model.is_some() != options.mmproj.is_some() {
        return Err("Custom vision models require both --model and --mmproj".into());
    }
    let folder = Path::new(ROOT).join(format!("{}-python", options.example));
    let image = match &options.image {
        Some(p) => p.canonicalize()?,
        None if options.example == "receipt" => folder.join("receipt.jpg").canonicalize()?,
        _ => return Err("receipt-us requires --image PATH".into()),
    };
    let length = fs::metadata(&image)?.len();
    if length == 0 || length > 24 * 1024 * 1024 {
        return Err("Image must be nonempty and at most 24 MiB".into());
    }
    let mut questions = read_json(folder.join("questions.json"))?;
    if let Some(fields) = &options.fields {
        let mut names: HashSet<String> = fields.split(',').map(|s| s.trim().to_owned()).collect();
        if names.iter().any(|name| questions.get(name).is_none()) {
            return Err("Unknown receipt field".into());
        }
        loop {
            let before = names.len();
            for name in names.clone() {
                if let Some(deps) = questions[&name]["depends_on"].as_array() {
                    for dep in deps {
                        names.insert(dep.as_str().ok_or("Invalid dependency")?.to_owned());
                    }
                }
            }
            if before == names.len() {
                break;
            }
        }
        questions
            .as_object_mut()
            .ok_or("Invalid question map")?
            .retain(|name, _| names.contains(name));
    }
    report["image"] = json!(image);
    report["image_sha256"] = json!(models::hash(&image)?);
    report["fields"] = json!(questions
        .as_object()
        .ok_or("Invalid question map")?
        .keys()
        .collect::<Vec<_>>());
    report["subset"] = json!(options.fields.is_some());
    report["max_tokens"] = json!(options.max_tokens);
    report["thinking"] = json!(false);
    Ok(Some(
        json!({"context":{"contract":"turbojev.media.v1","modality":"image","text":"Read the attached photo of a restaurant receipt.","base64":STANDARD.encode(fs::read(image)?)},"questions":questions,"thinking":false,"text_max_tokens":options.max_tokens,"numeric_max_tokens":options.max_tokens}),
    ))
}
fn compare(options: &Options, report: &mut Value) -> Result<()> {
    let use_labels = options.reference_labels
        || options.example == "receipt"
            && report["image_sha256"].as_str()
                == Some(&models::hash(
                    &Path::new(ROOT).join("receipt-python/receipt.jpg"),
                )?);
    let reference = if use_labels {
        read_json(Path::new(ROOT).join(format!("{}-python/expected.json", options.example)))?
    } else {
        json!({})
    };
    let mut expected = json!({});
    let mut matches = json!({});
    for field in report["fields"].as_array().ok_or("Missing fields")? {
        let name = field.as_str().ok_or("Invalid field")?;
        if let Some(wanted) = reference.get(name) {
            let actual = &report["response"]["result"][name];
            let matched = match (actual.as_f64(), wanted.as_f64()) {
                (Some(a), Some(b)) => (a - b).abs() <= 1e-6f64.max(b.abs() * 1e-6),
                _ => actual == wanted,
            };
            expected[name] = wanted.clone();
            matches[name] = json!(matched);
        }
    }
    report["expected"] = expected;
    report["matches"] = matches;
    Ok(())
}
fn run(options: &Options, report: &mut Value) -> Result<()> {
    let input = request(options, report)?;
    let configured = options.model.clone().or_else(|| {
        if options.vision() {
            None
        } else {
            std::env::var_os("TURBOJEV_MODEL").map(PathBuf::from)
        }
    });
    let model = if let Some(path) = configured {
        models::gguf(&path)?
    } else if options.vision() {
        models::download(
            "Qwen3.5-2B-Q4_K_M.gguf",
            &format!("{VISION}Qwen3.5-2B-Q4_K_M.gguf"),
            1280835840,
            None,
        )?
    } else {
        models::download("Qwen3-0.6B-Q4_K_M.gguf","https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf",484220320,Some("9acfc1e001311f34b4252001b626f2e466d592a42065f66571bff3790d4e1b14"))?
    };
    let projector = if options.vision() {
        Some(if let Some(path) = &options.mmproj {
            models::gguf(path)?
        } else {
            models::download(
                "Qwen3.5-2B-mmproj-F16.gguf",
                &format!("{VISION}mmproj-F16.gguf"),
                668227264,
                None,
            )?
        })
    } else {
        None
    };
    let native_path = runtime(options)?;
    report["model"] = json!(model);
    report["model_sha256"] = json!(models::hash(&model)?);
    if let Some(path) = &projector {
        report["mmproj"] = json!(path);
        report["mmproj_sha256"] = json!(models::hash(path)?);
    }
    report["native_library"] = json!(native_path);
    report["native_sha256"] = json!(models::hash(&native_path)?);
    let start = Instant::now();
    // evaluate: cyclic averages extra rotations. generate: permutations controls enum orderings.
    let engine = native::Engine::open(
        &native_path,
        &json!({"model":model,"mmproj":projector,"device":options.device,"nCtx":8192,"nSeqMax":1,"nThreads":4,"nThreadsBatch":4,"execution":{"orderRobustness":"none"}}),
    )?;
    report["load_seconds"] = json!(start.elapsed().as_secs_f64());
    if options.example == "fair-die" {
        let labels = ["one", "two", "three", "four", "five", "six"];
        let mut budgets = vec![json!(1), json!("auto"), json!(8)];
        if options.all_permutations {
            budgets.push(json!("all"));
        }
        report["runs"] = json!({});
        report["seed"] = json!(42);
        report["ground_truth"] = Value::Object(
            labels
                .iter()
                .map(|name| (name.to_string(), json!(1. / 6.)))
                .collect(),
        );
        for budget in budgets {
            println!("Evaluating permutation budget {budget}…");
            let value = json!({"context":"A single roll of a fair die.","seed":42,"questions":{"roll":{"type":"string","enum":labels,"instructions":"What number will come up on a single roll of a fair six-sided die?","permutations":budget,"return_probabilities":true}}});
            let _: turbojev::schema::fields::GenerateRequest =
                serde_json::from_value(value.clone())?;
            let start = Instant::now();
            let response = engine.call(&value, true)?;
            let seconds = start.elapsed().as_secs_f64();
            let probabilities = response["result"]["roll"]["probabilities"]
                .as_object()
                .ok_or("Missing probabilities")?;
            let values = labels
                .iter()
                .map(|name| {
                    probabilities
                        .get(*name)
                        .and_then(Value::as_f64)
                        .ok_or("Missing label probability")
                })
                .collect::<std::result::Result<Vec<_>, _>>()?;
            if probabilities.len() != 6
                || values
                    .iter()
                    .any(|p| !p.is_finite() || !(0. ..=1.).contains(p))
                || (values.iter().sum::<f64>() - 1.).abs() > 1e-9
            {
                return Err("Invalid model distribution".into());
            }
            let divergence = if values.iter().all(|p| *p > 0.) {
                Some(
                    values
                        .iter()
                        .map(|p| ((1. / 6.) / p).ln() / 6.)
                        .sum::<f64>(),
                )
            } else {
                None
            };
            let key = budget
                .as_str()
                .map(str::to_owned)
                .unwrap_or_else(|| budget.to_string());
            report["runs"][&key] = json!({"response":response,"seconds":seconds,"kl_uniform_to_prediction":divergence});
            println!("{}", serde_json::to_string_pretty(&report["runs"][&key])?);
        }
    } else {
        let input = input.ok_or("Missing request")?;
        if options.example != "ticket" {
            let _: turbojev::schema::fields::GenerateRequest =
                serde_json::from_value(input.clone())?;
        }
        println!(
            "Evaluating {}; image inference may take several minutes.",
            options.example
        );
        let start = Instant::now();
        report["response"] = engine.call(&input, options.example != "ticket")?;
        report["evaluation_seconds"] = json!(start.elapsed().as_secs_f64());
        if options.vision() {
            compare(options, report)?;
        }
        println!("{}", serde_json::to_string_pretty(&report["response"])?);
    }
    engine.close()?;
    Ok(())
}
fn main() -> Result<()> {
    let options = Options::parse();
    let mut report = json!({"example":options.example,"package_version":"0.30.1","language":"Rust","platform":std::env::consts::OS,"architecture":std::env::consts::ARCH,"device":options.device});
    let outcome = run(&options, &mut report);
    report["ok"] = json!(outcome.is_ok());
    report["error"] = outcome
        .as_ref()
        .err()
        .map_or(Value::Null, |error| json!(error.to_string()));
    let output = options
        .output
        .clone()
        .unwrap_or_else(|| PathBuf::from(format!("result-{}.json", options.example)));
    if let Some(parent) = output.parent().filter(|p| !p.as_os_str().is_empty()) {
        fs::create_dir_all(parent)?;
    }
    fs::write(
        &output,
        format!("{}\n", serde_json::to_string_pretty(&report)?),
    )?;
    println!("Report saved: {}", output.display());
    outcome
}
