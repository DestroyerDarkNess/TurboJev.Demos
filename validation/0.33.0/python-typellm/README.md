# Python TypeLLM ports — TurboJev 0.33.0

All twelve original contexts and question schemas were retained from the source
pages, accessed 2026-10-10. They use the installed PyPI package and Qwen3 0.6B
Q4_K_M. Reports retain full requests, model hashes, responses, reasoning and times.
Native execution was Windows x64 with explicit Vulkan GPU. No host replacements
or mocked inference were used.

## Contract and packaging checks

- All twelve schemas compiled through the published SDK.
- All 24 explicit off/medium reasoning and one-permutation configurations compiled.
- Eleven default workflows returned responses. Expense audit exhausted the original
  low reasoning budget; its error and available usage remain in the report.
- Expense audit completed with explicit medium reasoning and one permutation.
  This changes the configuration and is not an automatic fallback.
- The copied incident folder ran outside the demo repository, without sibling code.
- Relocated Node/TypeScript/C#/Rust projects returned the same numeric extraction
  results. The updated build-all script passed its three-architecture checks.
- No SDK export was missing for these twelve examples. Reasoning/permutation
  overrides apply to supported scalar fields, not object-array property controls.

## Accuracy observations

Completion means a typed workflow executed, not that its answers were correct.
Do not compare these results with the private model accuracy on the source pages.

- Email triage returned invoice/1240 and skipped the two unrelated follow-ups.
- Category tree returned home_kitchen/coffee_tea.
- Support ticket returned billing, high urgency, refund intent and a summary.
- Sure refund returned billing and 49.
- Date order selected 07/06/2026, with DD/MM/YYYY stated in the context.
- Letter count returned hello=0 but strawberry=2 (the latter is wrong).
- Standup returned an empty attendee array (wrong).
- New category selected new but named it new, rather than a useful expense category.
- Incident chose high severity and rollback; its message omitted the rollback action.
- Identical resumes did not yield 50/50 distributions and remained sensitive to
  field/context differences. Averaging is not proof of fair hiring decisions.
- Medium expense audit missed rows and violations and approved inconsistently
  with its own adds_up=false answer. The model's recorded reasoning misinterpreted
  the policy and the boolean meaning; its high confidence was not calibrated.

The model's errors are not corrected in host code. Use --model with a stronger
compatible GGUF to investigate quality. Reasoning can cost substantial time:
letter-count selected high effort and repeated it over balanced layouts. Select
--permutations 1 explicitly to reduce inference calls. No speed claim is made;
some runs overlapped compilation or other inference.
