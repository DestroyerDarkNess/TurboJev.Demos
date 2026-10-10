import { TurboJev } from "@turbojev/node";
import { runDemo } from "./demo.mjs";

await runDemo((options) => TurboJev.load(options), process.argv.slice(2), "JavaScript / Node");
