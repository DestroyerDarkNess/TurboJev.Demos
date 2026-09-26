const $ = (id) => document.getElementById(id);
const modelCatalog = {
  transformers: [
    { id: "onnx-community/Qwen3-0.6B-ONNX", name: "Qwen3 · 0.6B · ONNX" },
    { id: "onnx-community/Qwen2.5-0.5B-Instruct", name: "Qwen2.5 · 0.5B · ONNX" },
  ],
  llamacpp: [
    { id: "Qwen/Qwen3-0.6B-GGUF", name: "Qwen3 · 0.6B · Q8_0 · GGUF", url: "https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf" },
  ],
};
const examples = {
  account: {
    state: "A customer says a password reset succeeded, but every login attempt still returns ‘account locked’. Two unlock emails were requested and neither arrived.",
    question: "Which queue should handle this request?",
    options: ["Account access support", "Billing support", "Close as resolved"],
  },
  email: {
    state: "An email claims to be from the payroll team and says the recipient’s salary payment will be suspended today. It comes from payroll-review@outlook.com and links to a non-company sign-in page asking for a password and verification code.",
    question: "How should this email be classified?",
    options: ["Legitimate", "Spam", "Phishing"],
  },
};
const worker = new Worker("./worker-bootstrap.js", { type: "module" });
const pending = new Map();
let nextId = 1;
let engineReady = false;
let busy = false;
let activeFile = "";
let benchmark = null;

function updateModelChoices() {
  const runtime = $("runtime").value;
  const models = modelCatalog[runtime];
  $("model").replaceChildren(...models.map((model) => {
    const option = new Option(model.name, model.id);
    if (model.url) option.dataset.url = model.url;
    return option;
  }));
  $("runtime-detail").textContent = runtime === "llamacpp"
    ? "GGUF models · llama.cpp WebAssembly, with optional WebGPU."
    : "ONNX models · Transformers.js WebAssembly or WebGPU.";
}

// esm.sh serves the published wasm-bindgen module and its adjacent .wasm binary.
const wasmCdn = "https://esm.sh/@turbojev/wasm@0.29.1/es2022";

worker.addEventListener("message", ({ data }) => {
  if (data.type === "progress") {
    if (engineReady) return;
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
  $("runtime").disabled = value || engineReady;
  $("model").disabled = value || engineReady;
  $("device").disabled = value || engineReady;
  $("compare").disabled = value || !engineReady || $("runtime").value !== "llamacpp";
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
    const runtime = $("runtime").value;
    const selectedModel = $("model").selectedOptions[0];
    const model = selectedModel.value;
    const descriptor = await call("load", {
      model,
      runtimeModuleUrl: new URL("./runtime.js", import.meta.url).href,
      wasmModuleUrl: `${wasmCdn}/wasm.mjs`,
      workerUrl: new URL("./worker-bootstrap.js", import.meta.url).href,
      runtimeOptions: {
        backend: runtime,
        modality: "text",
        device,
        dtype: "q4",
        ...(runtime === "llamacpp" ? { modelUrl: selectedModel.dataset.url, modelLabel: selectedModel.textContent } : {}),
      },
    });
    engineReady = true;
    $("runtime-state").textContent = "Ready";
    $("runtime-detail").textContent = `${descriptor.model} · ${runtime === "llamacpp" ? "llama.cpp WASM" : "Transformers.js"} · ${device === "wasm" ? "CPU" : "WebGPU"}`;
    $("load-progress").hidden = true;
    $("empty").hidden = false;
    $("result").hidden = true;
    $("compare").disabled = runtime !== "llamacpp";
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
    $("compare").disabled = true;
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
  const question = $("question").value.trim();
  const options = $("choices").value.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
  if (!state) return fail(new Error("Enter the decision context."));
  if (!question) return fail(new Error("Enter a question for the model."));
  if (options.length < 2) return fail(new Error("Provide at least two possible answers."));
  if (new Set(options).size !== options.length) return fail(new Error("Each possible answer must be unique."));

  setBusy(true);
  $("empty").hidden = true;
  $("result").hidden = true;
  $("runtime-state").textContent = "Evaluating";
  $("runtime-detail").textContent = "Scoring the supplied choices…";
  const started = performance.now();
  try {
    const criteria = Object.fromEntries(options.map((option) => [option, option]));
    const response = await call("evaluate", {
      request: {
        state: { message: state },
        questions: {
          route: {
            type: "choice",
            instructions: question,
            criteria,
          },
        },
      },
    });
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

$("compare").addEventListener("click", async () => {
  if (!engineReady || busy || $("runtime").value !== "llamacpp") return;
  clearError();
  const input = readDecision();
  if (!input) return;
  setBusy(true);
  $("comparison").hidden = false;
  $("comparison-status").textContent = "Running TurboJev, then the SemIf direct-readout reference…";
  $("turbo-result").textContent = "Running…";
  $("semif-result").textContent = "Waiting…";
  $("turbo-time").textContent = "—";
  $("semif-time").textContent = "—";
  const device = $("device").value;
  let referenceWorker;
  try {
    const turboRuns = [];
    for (let run = 0; run < 3; run++) {
      const started = performance.now();
      const response = await evaluateDecision(input);
      turboRuns.push({ response, elapsedMs: performance.now() - started });
    }
    const turboMs = median(turboRuns.map((run) => run.elapsedMs));
    renderComparisonSide("turbo", turboRuns.at(-1).response, turboMs);
    $("comparison-status").textContent = "TurboJev finished; releasing its model before loading SemIf’s reference runtime…";
    await call("close");
    engineReady = false;
    referenceWorker = new Worker("./semif-worker.js", { type: "module" });
    const reference = await runSemIfReference(referenceWorker, input, modelCatalog.llamacpp[0].url, device, 3);
    referenceWorker.terminate();
    referenceWorker = undefined;
    renderComparisonSide("semif", reference, reference.elapsedMs);
    const ratio = turboMs / reference.elapsedMs;
    $("comparison-ratio").textContent = ratio >= 1
      ? `SemIf direct readout was ${ratio.toFixed(2)}× faster.`
      : `TurboJev was ${(1 / ratio).toFixed(2)}× faster than SemIf’s direct readout.`;
    $("comparison-status").textContent = "Median of 3 runs per engine. Same Qwen3 0.6B Q8_0 GGUF, state, question, options, and device; each engine formats its own prompt. Model load and warmup are excluded. TurboJev ran first.";
    await loadTurboAgain();
    $("comparison-status").textContent += " TurboJev is ready again.";
  } catch (error) {
    referenceWorker?.terminate();
    if (engineReady) await call("close").catch(() => {});
    fail(error);
    $("comparison-status").textContent = "Comparison stopped. See the error above; load TurboJev again before another run.";
    engineReady = false;
    $("load").disabled = false;
    $("unload").disabled = true;
    $("evaluate").disabled = true;
    $("compare").disabled = true;
  } finally {
    setBusy(false);
  }
});

function readDecision() {
  const state = $("state").value.trim();
  const question = $("question").value.trim();
  const options = $("choices").value.split(/\r?\n/).map((value) => value.trim()).filter(Boolean);
  if (!state) { fail(new Error("Enter the decision context.")); return null; }
  if (!question) { fail(new Error("Enter a question for the model.")); return null; }
  if (options.length < 2) { fail(new Error("Provide at least two possible answers.")); return null; }
  if (new Set(options).size !== options.length) { fail(new Error("Each possible answer must be unique.")); return null; }
  return { state, question, options };
}

async function evaluateDecision({ state, question, options }) {
  const criteria = Object.fromEntries(options.map((option) => [option, option]));
  return call("evaluate", {
    request: { state: { message: state }, questions: { route: { type: "choice", instructions: question, criteria } } },
  });
}

function runSemIfReference(referenceWorker, input, modelUrl, device, runCount) {
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => reject(new Error("SemIf reference runtime timed out.")), 180000);
    const runs = [];
    referenceWorker.addEventListener("message", ({ data }) => {
      if (data.type === "progress") {
        $("comparison-status").textContent = `Loading SemIf reference model: ${Math.round(data.progress)}%`;
      } else if (data.type === "ready") {
        $("comparison-status").textContent = `SemIf model ready; measuring ${runCount} direct readouts…`;
        referenceWorker.postMessage({ type: "evaluate", input });
      } else if (data.type === "result") {
        runs.push(data.result);
        if (runs.length < runCount) {
          $("comparison-status").textContent = `SemIf direct readout ${runs.length + 1} of ${runCount}…`;
          referenceWorker.postMessage({ type: "evaluate", input });
        } else {
          clearTimeout(timeout);
          resolve({ ...runs.at(-1), elapsedMs: median(runs.map((run) => run.elapsedMs)) });
        }
      } else if (data.type === "error") {
        clearTimeout(timeout);
        reject(new Error(data.message));
      }
    });
    referenceWorker.addEventListener("error", (event) => {
      clearTimeout(timeout);
      reject(new Error(event.message || "SemIf reference worker failed."));
    });
    referenceWorker.postMessage({ type: "load", modelUrl, device });
  });
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

function renderComparisonSide(side, response, elapsed) {
  const answer = response.answers?.route;
  const probabilities = Object.entries(answer?.probabilities || response.probabilities || {});
  const choice = answer?.choice || response.choice;
  $(`${side}-time`).textContent = `${(elapsed / 1000).toFixed(3)} s`;
  $(`${side}-result`).replaceChildren();
  const title = document.createElement("strong");
  title.textContent = choice || "No selected answer";
  $(`${side}-result`).append(title);
  for (const [label, probability] of probabilities.sort((a, b) => b[1] - a[1])) {
    const row = document.createElement("p");
    row.textContent = `${label}: ${(Number(probability) * 100).toFixed(1)}%`;
    $(`${side}-result`).append(row);
  }
}

async function loadTurboAgain() {
  $("comparison-status").textContent += " Reloading TurboJev model…";
  const selectedModel = $("model").selectedOptions[0];
  await call("load", {
    model: selectedModel.value,
    runtimeModuleUrl: new URL("./runtime.js", import.meta.url).href,
    wasmModuleUrl: `${wasmCdn}/wasm.mjs`,
    workerUrl: new URL("./worker-bootstrap.js", import.meta.url).href,
    runtimeOptions: {
      backend: "llamacpp", modality: "text", device: $("device").value, dtype: "q4",
      modelUrl: selectedModel.dataset.url, modelLabel: selectedModel.textContent,
    },
  });
  engineReady = true;
  $("load-progress").hidden = true;
  $("runtime-state").textContent = "Ready";
  $("runtime-detail").textContent = `${selectedModel.textContent} · llama.cpp WASM · ${$("device").value === "wasm" ? "CPU" : "WebGPU"}`;
}

document.querySelectorAll("[data-example]").forEach((button) => button.addEventListener("click", () => {
  const example = examples[button.dataset.example];
  $("state").value = example.state;
  $("question").value = example.question;
  $("choices").value = example.options.join("\n");
}));

function renderResult(response, elapsed) {
  const answer = response.answers?.route;
  if (!answer || answer.type !== "choice") throw new Error("TurboJev returned no choice answer.");
  const probabilities = Object.entries(answer.probabilities || {}).sort((a, b) => b[1] - a[1]);
  $("selected").textContent = answer.choice;
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

$("runtime").addEventListener("change", updateModelChoices);
updateModelChoices();
