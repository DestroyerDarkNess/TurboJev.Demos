# TurboJev demos

Runnable examples using TurboJev **0.33.1 from public package registries and
CDNs**. Each demo has its own folder, source code, input data and run
instructions. Demos use the published SDK; they do not build TurboJev locally
or import another demo.

## Run a demo

Choose a language and run its example from the demo folder:

### Python

```powershell
cd python/simple
py -m pip install -r requirements.txt
py main.py
```

### JavaScript

```powershell
cd node/js/typed-workflows
npm ci
npm start -- ticket
```

### TypeScript

```powershell
cd node/ts/typed-workflows
npm ci
npm start -- ticket
```

### C# / .NET

```powershell
cd dotnet/csharp/typed-workflows
dotnet run -c Release -- ticket
```

### Rust

```powershell
cd rust/typed-fields
cargo run --release -- ticket
```

### Browser

```powershell
cd webpage/vanilla
py -m http.server 4174
```

Open <http://localhost:4174>. The page loads TurboJev from published CDN
packages.

## Choose an example

| Language | Examples and instructions |
| --- | --- |
| Python | [Workflow, probability, reasoning, Snake, typed fields and receipt demos](python/README.md) |
| JavaScript | [Node.js demo](node/js/typed-workflows/README.md) |
| TypeScript | [Node.js demo](node/ts/typed-workflows/README.md) |
| C# / .NET | [Typed decision and structured workflow demos](dotnet/csharp/typed-workflows/README.md) |
| Rust | [Typed decisions and structured fields](rust/typed-fields/README.md) |
| Browser | [Vanilla HTML and JavaScript](webpage/vanilla/README.md) |

Each demo README lists its commands, options, model requirements and platform support.

## Models and devices

Text demos download QJev3.5 0.8B v19c Q8_0 on first run and cache it under
`~/.cache/turbojev`. Downloads show progress and are reused by other demos. CPU
is the default; a demo requests GPU only when you pass `--device gpu`. Image
demos use a compatible vision GGUF and projector. Results show the model's
actual output, including mistakes.

Use a different local text model with `--model PATH` or `TURBOJEV_MODEL`, where
supported. Each demo README lists its exact options.

## Check the demos

On Windows, `build-all.ps1` checks package availability, builds the C# and
TypeScript projects, checks Rust targets and compiles Python files. It requires
Python, Node.js, Rust and .NET 8. Cross-compilation does not verify execution on
another CPU architecture.

```powershell
.\build-all.ps1
```

The [current validation records](validation/0.33.1/README.md) list the builds, package checks and real inference smoke runs. [Earlier results](validation/0.33.0/README.md) retain their original version, responses and timings. Attribution and third-party licenses are included with the relevant demos.
