# TurboJev 0.30.1 registry validation

These runs use public npm, PyPI or NuGet packages, not a local TurboJev build.
`packages.json` verifies all eight npm packages, three PyPI wheels, the NuGet
package and its three Windows native destinations, and 27 crates.io packages.
NuGet's repository signature changes the archive bytes; the complete unsigned
payload matches the locally tested package. The separate browser CDN check
verifies asset downloads, not browser inference.

| Run | Model | Observed result |
|---|---|---|
| Node typed fields | Qwen3 0.6B Q4_K_M | Integer 7, dependent boolean true, conditional field skipped |
| Node and TypeScript introductory demos | Qwen3 0.6B Q4_K_M | Three typed answers; ticket routed to shipping |
| Fair die | Qwen3 0.6B Q4_K_M | Probability sums equal 1; KL from uniform: 5.7107 for one ordering, 0.1188 for `auto`, 0.8674 for eight sampled orderings |
| Receipt, all 14 fields | Qwen3.5 2B Q4_K_M + F16 projector | 10/13 reference labels match; 588.489 s evaluation |
| US receipt, all 16 fields | Same vision model/projector | 11/15 reference labels match; 177.319 s evaluation |
| Snake compatibility smoke | Qwen3 0.6B Q4_K_M | Three model-selected moves, no host-selected moves; stopped at the turn limit |

Receipt mismatches are retained. The first example missed the third item's
spelling, subtotal and dependent discount percentage. The US example missed
table, currency and dependent tax/per-person amounts. Unscored expense notes
can also contain errors. These small-model results do not establish perfect
OCR or arithmetic. Expected labels are compared after inference.

The Python, simple Python and C# introductory demos also executed successfully.
The Rust introductory example compiled and printed its portable contract; it
does not perform model inference. `build-all.ps1` downloaded all three PyPI
wheels and built .NET x86/x64/ARM64 outputs from nuget.org, then built the
Node/TypeScript/Rust projects. `.nupkg.metadata` confirms the isolated .NET
cache's nuget.org source.

Execution was on Windows x64. Cross-architecture builds and registry artifacts
do not establish physical x86/ARM64 execution. Source portability does not
mean Linux/macOS native wheels are published. Native compilation and other
machine activity overlapped some runs, so raw times are functional-run
measurements, not isolated performance comparisons. The three-turn Snake run
does not qualify navigation accuracy or food-reaching ability.
