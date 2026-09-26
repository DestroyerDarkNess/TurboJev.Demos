const MODEL_WASM = "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/wasm/wllama.wasm";
const MODEL_RUNTIME = "https://cdn.jsdelivr.net/npm/@wllama/wllama@3.6.1/esm/index.js";
const MODEL_LABEL_BASE = 32;
let engine;

function send(type, data = {}) { self.postMessage({ type, ...data }); }
const labelsFor = (count) => Array.from({ length: count }, (_, index) => String.fromCharCode(65 + index));
function softmax(values) {
  const maximum = Math.max(...values);
  const exponents = values.map((value) => Math.exp(value - maximum));
  const total = exponents.reduce((sum, value) => sum + value, 0);
  return exponents.map((value) => value / total);
}

async function load({ modelUrl, device }) {
  const { Wllama, LoggerWithoutDebug } = await import(MODEL_RUNTIME);
  engine = new Wllama({ default: MODEL_WASM }, { logger: LoggerWithoutDebug, suppressNativeLog: true, parallelDownloads: 4 });
  await engine.loadModelFromUrl(modelUrl, {
    n_ctx: 2048,
    n_batch: 512,
    n_gpu_layers: device === "webgpu" ? 999 : 0,
    cache_prompt: false,
    progressCallback: ({ loaded, total }) => send("progress", { progress: total ? loaded / total * 100 : 0 }),
  });
  const warmup = await engine.createChatCompletion({
    messages: [{ role: "user", content: "Reply with the single word ready." }],
    max_tokens: 1,
    temperature: 0,
    cache_prompt: false,
    chat_template_kwargs: { enable_thinking: false },
  });
  if (!warmup?.choices?.length) throw new Error("SemIf reference warmup returned no completion.");
  send("ready");
}

async function evaluate({ state, question, options }) {
  const labels = labelsFor(options.length);
  const optionBlock = options.map((option, index) => `${labels[index]}. ${option}`).join("\n");
  const prompt = `State:\n${state}\n\nQuestion:\n${question}\n\nAllowed options:\n${optionBlock}\n\nReply with exactly one option letter from: ${labels.join(", ")}.`;
  const started = performance.now();
  const grammar = `root ::= ${labels.map((label) => `"${label}"`).join(" | ")}`;
  const response = await engine.createChatCompletion({
    messages: [
      { role: "system", content: "Make the requested decision from the supplied state. Follow the output format exactly." },
      { role: "user", content: prompt },
    ],
    max_tokens: 1,
    temperature: 1,
    top_k: 0,
    top_p: 1,
    logprobs: true,
    top_logprobs: 20,
    logit_bias: Object.fromEntries(labels.map((label, index) => [String(MODEL_LABEL_BASE + index), 100])),
    grammar,
    cache_prompt: false,
    chat_template_kwargs: { enable_thinking: false },
  });
  const entries = response.choices?.[0]?.logprobs?.content?.[0]?.top_logprobs ?? [];
  const logits = labels.map((label) => {
    const entry = entries.find((item) => item.token === label || (item.bytes?.length === 1 && item.bytes[0] === label.charCodeAt(0)));
    return Number(entry?.logprob);
  });
  if (logits.some((value) => !Number.isFinite(value))) throw new Error("SemIf reference did not return all candidate log-probabilities.");
  const probabilities = softmax(logits);
  const index = probabilities.indexOf(Math.max(...probabilities));
  send("result", { result: {
    elapsedMs: performance.now() - started,
    choice: options[index],
    probabilities: Object.fromEntries(options.map((option, i) => [option, probabilities[i]])),
  } });
}

self.addEventListener("message", async ({ data }) => {
  try {
    if (data.type === "load") await load(data);
    if (data.type === "evaluate") await evaluate(data.input);
  } catch (error) {
    send("error", { message: error?.message ?? String(error) });
  }
});
