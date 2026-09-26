# TurboJev browser demo

A no-build HTML and vanilla JavaScript example. It loads TurboJev's published browser worker and WebAssembly package from jsDelivr. Use the Runtime menu to choose Transformers.js with ONNX models or llama.cpp WASM with GGUF models. Both run locally in the browser.

The page starts with Qwen3 0.6B Q8_0 GGUF, the same pinned model file used by [SemIf (formerly OpenJev)](https://openjev.com/). Its **Account support** and **Email triage** presets match SemIf's editable examples. CPU/WebAssembly is selected by default; choose WebGPU to request the browser's GPU explicitly. The demo does not switch devices if WebGPU is unavailable.

After loading the GGUF, choose **Compare TurboJev with SemIf** to run the same state, question, and options through both engines. It displays the selections, option probabilities, and median decision time across three runs. TurboJev is unloaded before the SemIf reference runtime loads so they do not compete for memory. Model loading and warmup are excluded from decision time. The SemIf side reproduces its direct one-token candidate readout with wllama 3.6.1; this is a local reference comparison, not a request to the OpenJev/SemIf website. Browser, device, thermal state, and background load affect results.

## Run locally

Serve this directory over localhost or HTTPS; browser module workers and WebAssembly do not work from a `file://` URL.

```powershell
cd TurboJev-js-browser
py -m http.server 4174
```

Open <http://localhost:4174>. Select **Load model**, wait for the file progress bar to finish, then choose an example or enter your own state, question, and allowed answers. **Evaluate** measures TurboJev inference. **Compare TurboJev with SemIf** runs both paths sequentially against the same Q8_0 file and reports their inference times separately.

## CDN sources

- `@turbojev/web@0.29.1/worker.js` from jsDelivr
- `@turbojev/runtime-transformersjs@0.29.1` and Transformers.js from esm.sh
- `@turbojev/runtime-llamacpp-wasm@0.29.1` and `@wllama/wllama@3.6.1` from jsDelivr
- `@turbojev/wasm@0.29.1` from esm.sh (the module loads its adjacent WASM binary)
- `@wllama/wllama@3.6.1` from jsDelivr for the SemIf direct-readout reference

The two example prompts and the SemIf scoring procedure are based on the independent [SemIf browser lab](https://openjev.com/) and its [published implementation](https://github.com/TheoLeeCJ/SemIf-OpenJev). The comparison uses Qwen3-0.6B-Q8_0 at Hugging Face revision `23749fefcc72300e3a2ad315e1317431b06b590a` for both paths. Quantized candidate probabilities are conditional on the listed choices and are not calibrated confidence.

TurboJev itself comes from the latest published `@turbojev/web` and `@turbojev/wasm` packages. The demo requires no Rust toolchain, package installation, or build step.
