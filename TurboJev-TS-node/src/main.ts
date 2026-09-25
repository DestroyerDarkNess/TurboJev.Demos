import { createWriteStream, existsSync, mkdirSync, renameSync, rmSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { Readable, Transform } from "node:stream";
import { pipeline } from "node:stream/promises";
import { performance } from "node:perf_hooks";
import { TurboJev } from "@turbojev/node";

const modelUrl = "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/main/Qwen_Qwen3-0.6B-Q4_K_M.gguf?download=true";
async function getModel(): Promise<string> {
  if (process.env.TURBOJEV_MODEL) return process.env.TURBOJEV_MODEL;
  const directory = join(homedir(), ".cache", "turbojev");
  const cache = join(directory, "Qwen3-0.6B-Q4_K_M.gguf");
  if (existsSync(cache)) return cache;
  mkdirSync(directory, { recursive: true });
  const temporary = `${cache}.part`;
  const response = await fetch(modelUrl);
  if (!response.ok || !response.body) throw new Error(`Model download failed: HTTP ${response.status}`);
  const total = Number(response.headers.get("content-length")) || 0;
  let received = 0;
  const progress = new Transform({ transform(chunk: Buffer, _encoding, callback) {
    received += chunk.length;
    if (total) {
      const ratio = Math.min(1, received / total);
      const width = 28;
      process.stdout.write(`\rQwen3 0.6B [${"█".repeat(Math.round(ratio * width)).padEnd(width, "─")}] ${(ratio * 100).toFixed(1)}%  ${(received / 2**20).toFixed(0)} / ${(total / 2**20).toFixed(0)} MB`);
    } else process.stdout.write(`\rDownloading Qwen3 0.6B: ${(received / 2**20).toFixed(0)} MB`);
    callback(null, chunk);
  }});
  try {
    await pipeline(Readable.fromWeb(response.body as any), progress, createWriteStream(temporary));
    process.stdout.write("\n");
    renameSync(temporary, cache);
    return cache;
  } catch (error) {
    rmSync(temporary, { force: true });
    process.stdout.write("\n");
    throw error;
  }
}
const model = await getModel();
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
