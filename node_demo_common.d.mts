export interface DemoLoadOptions {
  model: string; mmproj?: string; device: "cpu" | "gpu";
  nCtx: number; nSeqMax: number; nThreads: number; nThreadsBatch: number;
  execution: { orderRobustness: "none" | "cyclic" | "balanced" };
}
export interface DemoEngine {
  evaluate(request: unknown): Promise<unknown>;
  generate(request: unknown): Promise<unknown>;
  close(): Promise<void>;
}
export function runDemo(load: (options: DemoLoadOptions) => Promise<DemoEngine>, args: string[], language: string): Promise<void>;
