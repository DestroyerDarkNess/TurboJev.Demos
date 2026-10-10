# TurboJev 0.33.0 published-package checks

These records use public registry packages, not workspace SDK binaries.
The model is Qwen3 0.6B Q4_K_M; its SHA-256 is retained in each JSON report.
Native execution was on Windows x64. Cross-compilation and package assets
are checked separately; they do not prove execution on x86 or ARM64.

- Numeric extraction returned reference 12345 and amount 12.34 in Python,
  TypeScript/Node, .NET and Rust.
- Python, .NET and Rust Dice runs returned the same selected faces and matched
  probabilities within 1e-15 for budgets 1, auto and 8. No host-generated face or
  uniform distribution substitutes for inference. The full 720-layout run was
  not executed.
- Node's seeded Dice example sampled a face from the actual model distribution.
- Hierarchical generation returned billing/refund and skipped the unrelated
  support branch. Structured generation extracted both source invoice rows.
- The structured prompt explicitly tells the model to inspect the current
  array. The earlier vague prompt repeated an item, correctly producing an
  error with partial usage. The ordinal priority remained a model judgment;
  its high priority for an overdue invoice is not counted as ground-truth success.
- Snake is a three-turn API smoke run, not a navigation benchmark. All movements
  are the returned model choices. It reached the turn limit without eating food.

Some measurements overlap compilation or other inference. Do not use these
latencies as a controlled performance comparison. CPU and GPU results are
identified in each report. Browser module URLs and syntax were checked, and the
worker contracts have unit coverage; browser model accuracy was not rerun here.

`build-all.ps1` passed with registry packages: all three Python wheels downloaded,
.NET published for win-x86/win-x64/win-arm64, npm installed from its lockfiles,
and Rust checked for i686/x86_64/aarch64 Windows MSVC targets. Python source
compilation also passed. The 37 public registry checks are in `registries.json`.
