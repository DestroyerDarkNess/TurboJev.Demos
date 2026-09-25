const runtimeUrl = "https://esm.sh/@turbojev/runtime-transformersjs@0.28.6?deps=@huggingface/transformers@4.3.0";

export async function createRuntime() {
  const { createRuntime: createTransformersRuntime } = await import(runtimeUrl);
  const runtime = await createTransformersRuntime();

  return {
    ...runtime,
    initialize(options) {
      return runtime.initialize({
        ...options,
        progressCallback: (progress) => self.postMessage({ type: "progress", progress }),
      });
    },
  };
}
