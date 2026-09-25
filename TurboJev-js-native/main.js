import { performance } from "node:perf_hooks";
import { TurboJev } from "@turbojev/node";

const model = process.env.TURBOJEV_MODEL ??
  "hf://bartowski/Qwen_Qwen3-0.6B-GGUF/Qwen_Qwen3-0.6B-Q4_K_M.gguf";
const engine = await TurboJev.load({ model, nGpuLayers: 0, nThreads: 4 });
try {
  const start = performance.now();
  const result = await engine.evaluate({
    state: { ticket: "My package arrived broken. Please send a replacement." },
    questions: {
      team: {
        type: "choice",
        instructions: "Which team should handle this ticket?",
        criteria: { billing: "Payments and refunds", technical: "Bugs and outages", shipping: "Delivery problems" },
      },
      urgency: {
        type: "score",
        instructions: "How urgent is this ticket?",
        criteria: ["Can wait", "This week", "Today"],
      },
      wantsRefund: { type: "noul", instructions: "Does the customer ask for a refund?" },
    },
  });
  console.log(JSON.stringify(result, null, 2));
  console.log(`Elapsed: ${((performance.now() - start) / 1000).toFixed(2)} s`);
} finally {
  await engine.close();
}
