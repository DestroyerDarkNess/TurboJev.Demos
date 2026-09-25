const $ = (id) => document.getElementById(id);
const worker = new Worker("./worker-bootstrap.js", { type: "module" });
const pending = new Map();
let nextId = 1;
let engineReady = false;
let busy = false;
let activeFile = "";

// esm.sh serves the published wasm-bindgen module and its adjacent .wasm binary.
const wasmCdn = "https://esm.sh/@turbojev/wasm@0.28.6/es2022";

worker.addEventListener("message", ({ data }) => {
  if (data.type === "progress") {
    showDownloadProgress(data.progress);
    return;
  }
  if (data.type === "phase") {
    $("runtime-state").textContent = data.label;
    return;
  }
  const request = pending.get(data.id);
  if (!request) return;
  pending.delete(data.id);
  data.ok ? request.resolve(data.value) : request.reject(new Error(data.error));
});

worker.addEventListener("error", (event) => fail(new Error(event.message || "The browser worker stopped.")));

function call(op, args = {}) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    worker.postMessage({ id, op, args });
  });
}

function setBusy(value) {
  busy = value;
  $("load").disabled = value || engineReady;
  $("unload").disabled = value || !engineReady;
  $("evaluate").disabled = value || !engineReady;
  $("model").disabled = value || engineReady;
  $("device").disabled = value || engineReady;
}

function showDownloadProgress(data = {}) {
  const progress = Number.isFinite(data.progress) ? Math.max(0, Math.min(100, data.progress)) : 0;
  const file = data.file || data.name || data.status || "Preparing model files";
  if (file !== activeFile) activeFile = file;
  $("load-progress").hidden = false;
  $("progress").value = progress;
  $("progress-value").textContent = `${Math.round(progress)}%`;
  $("progress-label").textContent = data.status === "initiate" ? "Starting download" : "Downloading model files";
  $("progress-file").textContent = file;
}

function clearError() {
  $("error").hidden = true;
  $("error").textContent = "";
}

function fail(error) {
  $("runtime-state").textContent = "Error";
  $("runtime-detail").textContent = "The request stopped before a result was returned.";
  $("error").textContent = error.message || String(error);
  $("error").hidden = false;
}

$("load").addEventListener("click", async () => {
  if (busy) return;
  clearError();
  const device = $("device").value;
  if (device === "webgpu" && !navigator.gpu) {
    fail(new Error("WebGPU is unavailable in this browser. Select CPU explicitly to run on WebAssembly."));
    return;
  }
  setBusy(true);
  $("load-progress").hidden = false;
  $("progress").value = 0;
  $("progress-label").textContent = "Loading TurboJev and model runtime";
  $("progress-value").textContent = "0%";
  $("progress-file").textContent = "The model will be cached by your browser.";
  $("runtime-state").textContent = "Loading";
  $("runtime-detail").textContent = $("model").selectedOptions[0].textContent;
  try {
    const model = $("model").value;
    const descriptor = await call("load", {
      model,
      runtimeModuleUrl: new URL("./runtime.js", import.meta.url).href,
      wasmModuleUrl: `${wasmCdn}/wasm.mjs`,
      workerUrl: new URL("./worker-bootstrap.js", import.meta.url).href,
      runtimeOptions: { device, dtype: "q4" },
    });
    engineReady = true;
    $("runtime-state").textContent = "Ready";
    $("runtime-detail").textContent = `${descriptor.model} · ${device === "wasm" ? "WebAssembly CPU" : "WebGPU"}`;
    $("load-progress").hidden = true;
    $("empty").hidden = false;
    $("result").hidden = true;
  } catch (error) {
    fail(error);
  } finally {
    setBusy(false);
  }
});

$("unload").addEventListener("click", async () => {
  if (!engineReady || busy) return;
  setBusy(true);
  try {
    await call("close");
    engineReady = false;
    $("runtime-state").textContent = "Not loaded";
    $("runtime-detail").textContent = "Model files stay in your browser cache.";
    $("load-progress").hidden = true;
    $("empty").hidden = false;
    $("result").hidden = true;
  } catch (error) {
    fail(error);
  } finally {
    setBusy(false);
  }
});

$("evaluate").addEventListener("click", async () => {
  if (!engineReady || busy) return;
  clearError();
  const state = $("state").value.trim();
  const options = $("choices").value.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
  if (!state) return fail(new Error("Enter a message to evaluate."));
  if (options.length < 2) return fail(new Error("Provide at least two possible answers."));
  if (new Set(options).size !== options.length) return fail(new Error("Each possible answer must be unique."));

  setBusy(true);
  $("empty").hidden = true;
  $("result").hidden = true;
  $("runtime-state").textContent = "Evaluating";
  $("runtime-detail").textContent = "Scoring the supplied choices…";
  const started = performance.now();
  try {
    const response = await call("classify", { state, options });
    const elapsed = performance.now() - started;
    renderResult(response, elapsed);
    $("runtime-state").textContent = "Ready";
    $("runtime-detail").textContent = "Local inference complete.";
  } catch (error) {
    fail(error);
  } finally {
    setBusy(false);
  }
});

function renderResult(response, elapsed) {
  const probabilities = Object.entries(response.probabilities || {}).sort((a, b) => b[1] - a[1]);
  $("selected").textContent = response.choice;
  $("elapsed").textContent = `${(elapsed / 1000).toFixed(2)} s`;
  $("scores").replaceChildren(...probabilities.map(([label, value]) => {
    const row = document.createElement("div");
    row.className = "score-line";
    const name = document.createElement("span");
    name.textContent = label;
    const amount = document.createElement("b");
    amount.textContent = `${(value * 100).toFixed(1)}%`;
    const track = document.createElement("div");
    track.className = "score-track";
    const fill = document.createElement("div");
    fill.className = "score-fill";
    fill.style.width = `${Math.max(0, Math.min(100, value * 100))}%`;
    track.append(fill);
    row.append(name, amount, track);
    return row;
  }));
  $("empty").hidden = true;
  $("result").hidden = false;
}
