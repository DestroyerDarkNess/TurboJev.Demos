import { TurboJev } from "@turbojev/node";
import { runDemo } from "../node_demo_common.mjs";

await runDemo((options) => TurboJev.load(options), process.argv.slice(2), "JavaScript / Node");
