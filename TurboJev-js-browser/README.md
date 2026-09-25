# TurboJev browser demo

A no-build HTML and vanilla JavaScript example. It loads TurboJev's published browser worker and WebAssembly package from jsDelivr, and the Transformers.js runtime through esm.sh. Model files are downloaded from Hugging Face by Transformers.js and cached by the browser.

The default model is Qwen3 0.6B. CPU/WebAssembly is selected by default; choose WebGPU to request the browser's GPU explicitly. The demo does not switch devices if WebGPU is unavailable.

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
- `@turbojev/wasm@0.28.6` from esm.sh (the module loads its adjacent WASM binary)

All dependencies are version-pinned CDN packages. The demo requires no Rust toolchain, package installation, or build step.
