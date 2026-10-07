import { TurboJev, type EvaluationRequest, type GenerateRequest } from "@turbojev/node";
import { runDemo } from "../../node_demo_common.mjs";

await runDemo(async options => {
  const engine = await TurboJev.load(options);
  return {
    evaluate: request => engine.evaluate(request as EvaluationRequest),
    generate: request => engine.generate(request as GenerateRequest),
    close: () => engine.close(),
  };
}, process.argv.slice(2), "TypeScript / Node");
