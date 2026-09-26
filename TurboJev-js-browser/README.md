# TurboJev browser demo

A no-build HTML and vanilla JavaScript example. It loads TurboJev's published browser worker and WebAssembly package from jsDelivr. Use the Runtime menu to choose Transformers.js with ONNX models or llama.cpp WASM with GGUF models. Both run locally in the browser.

Choose an ONNX or GGUF model from the Model menu after selecting its runtime. The GGUF option is Qwen3 0.6B Q4_K_M, downloaded directly from Hugging Face. CPU/WebAssembly is selected by default; choose WebGPU to request the browser's GPU explicitly. The demo does not switch devices if WebGPU is unavailable.

## Run locally

Serve this directory over localhost or HTTPS; browser module workers and WebAssembly do not work from a `file://` URL.

```powershell
cd TurboJev-js-browser
py -m http.server 4174
```

Open <http://localhost:4174>. Select **Load model**, wait for the file progress bar to finish, then evaluate a message. The elapsed time measures inference only, after the model is loaded.

## CDN sources

- `@turbojev/web@0.28.6/worker.js` from jsDelivr
- `@turbojev/runtime-transformersjs@0.28.6` and Transformers.js from esm.sh
- the demo's small llama.cpp WASM adapter, plus `@wllama/wllama@3.6.1` from jsDelivr
- `@turbojev/wasm@0.28.6` from esm.sh (the module loads its adjacent WASM binary)

TurboJev itself comes from the latest published `@turbojev/web` and `@turbojev/wasm` packages. The demo requires no Rust toolchain, package installation, or build step.
