// Application-owned demo code using the published TurboJev package.
import {
  createReadStream,
  createWriteStream,
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { open } from "node:fs/promises";
import { createHash } from "node:crypto";
import { homedir, platform, arch } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Readable, Transform } from "node:stream";
import { pipeline } from "node:stream/promises";
import { performance } from "node:perf_hooks";

const root = dirname(fileURLToPath(import.meta.url));
const cache = join(homedir(), ".cache", "turbojev");
const visionBase =
  "https://huggingface.co/unsloth/Qwen3.5-2B-GGUF/resolve/f6d5376be1edb4d416d56da11e5397a961aca8ae/";
const help = `Usage: npm start -- [ticket|fields|structured|hierarchical|discover-categories|dice|limits|fair-die|receipt|receipt-us] [options]
  --device cpu|gpu       CPU by default; no device fallback
  --model PATH           Compatible GGUF (TURBOJEV_MODEL also works for text)
  --mmproj PATH          Matching vision projector; requires --model
  --image PATH           Required for receipt-us; receipt has a bundled photo
  --fields a,b           Receipt subset, including dependencies
  --max-tokens N         Generated output bound per field, default 64
  --reference-labels     Compare against the original receipt's labels
  --all-permutations     Fair die: also evaluate 720 orderings (slow)
  --output PATH          JSON report, default result-<example>.json`;

export function parseOptions(args) {
  const options = {
    example: "ticket",
    device: "cpu",
    maxTokens: 64,
    referenceLabels: false,
    allPermutations: false,
  };
  if (args[0] && !args[0].startsWith("-")) options.example = args.shift();
  while (args.length) {
    const name = args.shift();
    if (name === "--reference-labels") {
      options.referenceLabels = true;
      continue;
    }
    if (name === "--all-permutations") {
      options.allPermutations = true;
      continue;
    }
    const keys = {
      "--device": "device",
      "--model": "model",
      "--mmproj": "mmproj",
      "--image": "image",
      "--fields": "fields",
      "--output": "output",
      "--max-tokens": "maxTokens",
    };
    if (!keys[name] || !args[0] || args[0].startsWith("--"))
      throw Error(`Invalid option or missing value: ${name}`);
    options[keys[name]] = args.shift();
  }
  options.maxTokens = Number(options.maxTokens);
  options.vision = ["receipt", "receipt-us"].includes(options.example);
  if (
    ![
      "ticket",
      "fields",
      "structured",
      "hierarchical",
      "discover-categories",
      "dice",
      "limits",
      "fair-die",
      "receipt",
      "receipt-us",
    ].includes(options.example)
  )
    throw Error("Unknown example.");
  if (!["cpu", "gpu"].includes(options.device)) throw Error("Device must be cpu or gpu.");
  if (!Number.isInteger(options.maxTokens) || options.maxTokens < 1 || options.maxTokens > 32768)
    throw Error("max-tokens must be 1–32768.");
  if (
    !options.vision &&
    (options.image || options.fields || options.mmproj || options.referenceLabels)
  )
    throw Error("Image, fields, projector and reference labels are receipt options.");
  if (options.example === "receipt-us" && !options.image)
    throw Error("receipt-us requires --image PATH.");
  if (options.vision && Boolean(options.model) !== Boolean(options.mmproj))
    throw Error("Custom vision models require both --model and --mmproj.");
  if (options.allPermutations && options.example !== "fair-die")
    throw Error("all-permutations is a fair-die option.");
  return options;
}

export async function hashFile(path) {
  const hash = createHash("sha256");
  for await (const chunk of createReadStream(path)) hash.update(chunk);
  return hash.digest("hex");
}
async function isGguf(path) {
  if (!existsSync(path)) return false;
  const handle = await open(path, "r");
  try {
    const buffer = Buffer.alloc(4);
    await handle.read(buffer, 0, 4, 0);
    return buffer.toString() === "GGUF";
  } finally {
    await handle.close();
  }
}
async function download(name, url, size, sha) {
  mkdirSync(cache, { recursive: true });
  const path = join(cache, name);
  const valid = async (file) =>
    (await isGguf(file)) &&
    statSync(file).size === size &&
    (!sha || (await hashFile(file)) === sha);
  if (await valid(path)) {
    console.log(`Model cache hit: ${name}`);
    return path;
  }
  const partial = `${path}.part`;
  console.log(`Downloading ${name}…`);
  const response = await fetch(url);
  if (!response.ok || !response.body) throw Error(`Download failed: HTTP ${response.status}`);
  const contentLength = Number(response.headers.get("content-length"));
  if (contentLength && contentLength !== size) throw Error("Unexpected model size.");
  let received = 0,
    previous = 0;
  const started = performance.now();
  const progress = new Transform({
    transform(chunk, _encoding, callback) {
      received += chunk.length;
      if (received > size) return callback(Error("Download exceeds expected size."));
      const now = performance.now();
      if (now - previous > 200 || received === size) {
        previous = now;
        const ratio = received / size,
          speed = received / Math.max((now - started) / 1000, 0.001);
        const filled = Math.floor(ratio * 28);
        process.stdout.write(
          `\r[${"█".repeat(filled)}${"─".repeat(28 - filled)}] ${(ratio * 100).toFixed(1)}% ${(received / 2 ** 20).toFixed(1)}/${(size / 2 ** 20).toFixed(1)} MiB ${(speed / 2 ** 20).toFixed(1)} MiB/s ETA ${((size - received) / speed).toFixed(0)}s   `,
        );
      }
      callback(null, chunk);
    },
  });
  try {
    await pipeline(Readable.fromWeb(response.body), progress, createWriteStream(partial));
    if (!(await valid(partial))) throw Error("Incomplete or invalid model download.");
    renameSync(partial, path);
    return path;
  } catch (error) {
    rmSync(partial, { force: true });
    throw error;
  } finally {
    process.stdout.write("\n");
  }
}
export async function modelPaths(options) {
  const configured = options.model || (!options.vision && process.env.TURBOJEV_MODEL);
  if (configured) {
    const model = resolve(configured),
      mmproj = options.mmproj ? resolve(options.mmproj) : undefined;
    if (!(await isGguf(model)) || (mmproj && !(await isGguf(mmproj))))
      throw Error("Provide readable GGUF files.");
    return { model, ...(mmproj ? { mmproj } : {}) };
  }
  if (options.vision)
    return {
      model: await download(
        "Qwen3.5-2B-Q4_K_M.gguf",
        visionBase + "Qwen3.5-2B-Q4_K_M.gguf",
        1280835840,
      ),
      mmproj: await download(
        "Qwen3.5-2B-mmproj-F16.gguf",
        visionBase + "mmproj-F16.gguf",
        668227264,
      ),
    };
  return {
    model: await download(
      "Qwen3-0.6B-Q4_K_M.gguf",
      "https://huggingface.co/bartowski/Qwen_Qwen3-0.6B-GGUF/resolve/60b85c0e3d8fe0f6474f406922a26d12aca4550d/Qwen_Qwen3-0.6B-Q4_K_M.gguf",
      484220320,
      "9acfc1e001311f34b4252001b626f2e466d592a42065f66571bff3790d4e1b14",
    ),
  };
}
const readJson = (file) => JSON.parse(readFileSync(file, "utf8"));
export function makeRequest(options, record) {
  if (options.example === "fair-die") return null;
  if (!options.vision) {
    const request = readJson(join(root, "data/requests", `${options.example}.json`));
    if (options.example === "fields")
      Object.assign(request, {
        text_max_tokens: options.maxTokens,
        numeric_max_tokens: options.maxTokens,
      });
    return request;
  }
  const folder = join(root, `data/${options.example}`);
  const image = resolve(options.image || join(folder, "receipt.jpg"));
  if (!existsSync(image) || statSync(image).size <= 0 || statSync(image).size > 24 * 2 ** 20)
    throw Error("Provide a nonempty image of at most 24 MiB.");
  let questions = readJson(join(folder, "questions.json"));
  if (options.fields) {
    const names = new Set(options.fields.split(",").map((x) => x.trim()));
    for (const name of names) if (!questions[name]) throw Error(`Unknown receipt field: ${name}`);
    for (const name of names) for (const dep of questions[name].depends_on || []) names.add(dep);
    questions = Object.fromEntries(Object.entries(questions).filter(([name]) => names.has(name)));
  }
  Object.assign(record, {
    image,
    fields: Object.keys(questions),
    subset: Boolean(options.fields),
    max_tokens: options.maxTokens,
    thinking: false,
  });
  return {
    context: {
      contract: "turbojev.media.v1",
      modality: "image",
      text: "Read the attached photo of a restaurant receipt.",
      base64: readFileSync(image).toString("base64"),
    },
    questions,
    thinking: false,
    text_max_tokens: options.maxTokens,
    numeric_max_tokens: options.maxTokens,
  };
}
export async function compareLabels(options, record, response) {
  record.image_sha256 = await hashFile(record.image);
  const useLabels =
    options.referenceLabels ||
    (options.example === "receipt" &&
      record.image_sha256 === (await hashFile(join(root, "data/receipt", "receipt.jpg"))));
  const reference = useLabels
    ? readJson(join(root, `data/${options.example}`, "expected.json"))
    : {};
  record.expected = {};
  record.matches = {};
  for (const name of record.fields) {
    if (!(name in reference)) continue;
    const expected = reference[name],
      actual = response.result[name];
    record.expected[name] = expected;
    record.matches[name] =
      typeof actual === typeof expected &&
      (typeof expected === "number"
        ? Math.abs(actual - expected) <= Math.max(1e-6, Math.abs(expected) * 1e-6)
        : actual === expected);
  }
  if (Object.keys(record.matches).length)
    console.log(
      `Reference labels: ${Object.values(record.matches).filter(Boolean).length}/${Object.keys(record.matches).length}`,
    );
}
export async function runDemo(load, args, language) {
  if (args.includes("--help") || args.includes("-h")) {
    console.log(help);
    return;
  }
  let options;
  try {
    options = parseOptions([...args]);
  } catch (error) {
    console.error(`${error.message}\n${help}`);
    process.exitCode = 2;
    return;
  }
  const record = {
    example: options.example,
    package_version: "0.33.0",
    language,
    platform: platform(),
    architecture: arch(),
    device: options.device,
  };
  let engine;
  try {
    const request = makeRequest(options, record);
    const models = await modelPaths(options);
    Object.assign(record, models, { model_sha256: await hashFile(models.model) });
    if (models.mmproj) record.mmproj_sha256 = await hashFile(models.mmproj);
    let started = performance.now();
    engine = await load({
      ...models,
      device: options.device,
      nCtx: 8192,
      nSeqMax: 1,
      nThreads: 4,
      nThreadsBatch: 4,
      // evaluate: "balanced" averages canonical choice probabilities; "cyclic" averages rotation logits.
      // Both cost extra passes and preserve ordered scores. generate: use permutations.
      execution: { orderRobustness: "none" },
    });
    record.load_seconds = (performance.now() - started) / 1000;
    if (options.example === "fair-die") {
      const labels = ["one", "two", "three", "four", "five", "six"];
      Object.assign(record, {
        seed: 42,
        ground_truth: Object.fromEntries(labels.map((label) => [label, 1 / 6])),
        runs: {},
      });
      for (const budget of [1, "auto", 8, ...(options.allPermutations ? ["all"] : [])]) {
        console.log(`Evaluating permutation budget ${budget}…`);
        started = performance.now();
        const response = await engine.generate({
          context: "A single roll of a fair die.",
          mode: "argmax",
          temperature: 1,
          seed: 42,
          questions: {
            roll: {
              type: "string",
              enum: labels,
              instructions: "What number will come up on a single roll of a fair six-sided die?",
              permutations: budget,
              return_probabilities: true,
            },
          },
        });
        const seconds = (performance.now() - started) / 1000;
        const p = response.result.roll.probabilities,
          values = Object.values(p);
        if (
          Object.keys(p).length !== 6 ||
          labels.some((label) => !(label in p)) ||
          values.some((x) => !Number.isFinite(x) || x < 0 || x > 1) ||
          Math.abs(values.reduce((a, b) => a + b, 0) - 1) > 1e-9
        )
          throw Error("Invalid model distribution.");
        record.runs[budget] = {
          response,
          seconds,
          kl_uniform_to_prediction: values.every((x) => x > 0)
            ? values.reduce((sum, x) => sum + Math.log(1 / 6 / x) / 6, 0)
            : null,
        };
        console.log(JSON.stringify(record.runs[budget], null, 2));
      }
    } else {
      console.log(
        options.vision
          ? `Reading ${record.fields.length} fields; image inference may take minutes.`
          : "Evaluating…",
      );
      started = performance.now();
      record.response =
        options.example === "ticket"
          ? await engine.evaluate(request)
          : await engine.generate(request);
      record.evaluation_seconds = (performance.now() - started) / 1000;
      if (options.vision) await compareLabels(options, record, record.response);
      console.log(JSON.stringify(record.response, null, 2));
      console.log(`Evaluation: ${record.evaluation_seconds.toFixed(3)}s`);
    }
    record.ok = true;
    record.error = null;
  } catch (error) {
    record.ok = false;
    record.error = error.message;
    console.error(error);
    process.exitCode = 2;
  } finally {
    if (engine)
      try {
        await engine.close();
      } catch (error) {
        record.ok = false;
        record.error = error.message;
        process.exitCode = 2;
      }
    const output = resolve(options.output || `result-${options.example}.json`);
    mkdirSync(dirname(output), { recursive: true });
    writeFileSync(output, JSON.stringify(record, null, 2) + "\n");
    console.log(`Report saved: ${output}`);
  }
}
