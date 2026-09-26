const transformersRuntimeUrl = "https://esm.sh/@turbojev/runtime-transformersjs@0.28.6?deps=@huggingface/transformers@4.3.0";
const llamaRuntimeUrl = "https://cdn.jsdelivr.net/npm/@turbojev/runtime-llamacpp-wasm@0.28.6/src/index.js";

export async function createRuntime() {
  let runtime;

  return {
    async initialize(options) {
      const { createRuntime: create } = options.backend === "llamacpp"
        ? await import(llamaRuntimeUrl)
        : await import(transformersRuntimeUrl);
      runtime = await create();
      return runtime.initialize({
        ...options,
        progressCallback: (progress) => self.postMessage({ type: "progress", progress }),
      });
    },
    encodePrompt(...args) { return runtime.encodePrompt(...args); },
    encodePromptWithAnswer(...args) { return runtime.encodePromptWithAnswer(...args); },
    decodeTokens(...args) { return runtime.decodeTokens(...args); },
    scoreRuntimeBatch(...args) { return runtime.scoreRuntimeBatch(...args); },
    scoreDecisionBatch(...args) { return runtime.scoreDecisionBatch(...args); },
    setMedia(...args) { return runtime.setMedia?.(...args); },
    async close() { await runtime?.close?.(); runtime = undefined; },
  };
}
