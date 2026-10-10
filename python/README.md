# Python demos

Each folder is independent and uses TurboJev 0.33.0 from PyPI. Install its own
requirements and run its entry point. No demo imports or invokes another demo.

```sh
cd incident
python -m pip install -r requirements.txt
python main.py --device gpu
```

CPU is the default. All text demos use Qwen3 0.6B GGUF unless you pass another
model. Downloads show progress and share only the user's model cache.

## Workflow

| Demo | What it demonstrates |
| --- | --- |
| [incident](incident/README.md) | Evaluate incident severity, then decide whether to roll back, then draft a status message using both earlier answers. |
| [email-triage](email-triage/README.md) | Classify an email and run only its invoice, meeting or application follow-up. Inspect skipped to see branches that never ran. |
| [new-category](new-category/README.md) | Choose an existing expense category or new. Name a new category only when the model selects new. |
| [category-tree](category-tree/README.md) | Select a product department, then classify within that department. Other department branches are skipped. |
| [standup](standup/README.md) | Extract the names of people present at a standup into a model-generated array. The absent participant must not be included. |
| [expense-audit](expense-audit/README.md) | Extract expense rows, check their sum and policy violations with model reasoning, then decide approval and write a note. The host does not calculate the sum or choose the violations. |

## Thinking

| Demo | What it demonstrates |
| --- | --- |
| [letter-count](letter-count/README.md) | Compare letter counting in hello and strawberry with per-field automatic reasoning and integer probability distributions. |
| [date-order](date-order/README.md) | Compare mixed-format dates with automatic reasoning and a distribution over the two original date strings. |

## Probability

| Demo | What it demonstrates |
| --- | --- |
| [support-ticket](support-ticket/README.md) | Return queue, urgency and refund-intent distributions, plus a short support summary. |
| [sure-refund](sure-refund/README.md) | Extract a refund amount only when the billing category passes the confidence threshold. It demonstrates a conditional field, without issuing a refund. |
| [fair-die](fair-die/README.md) | Inspect the six-face model distribution and compare option-order budgets. No host-generated roll or uniform distribution replaces the model. |
| [identical-resumes](identical-resumes/README.md) | Score identical resumes in both candidate orders. Inspect keyed distributions and confidence; do not assume that every model gives exactly 50/50. |

## Other examples

- [snake](snake/README.md): repeated model-selected movement.
- [simple](simple/README.md): original Jev-style ticket decisions.
- [typed-fields](typed-fields/README.md): general typed and structured examples.
- [receipt](receipt/README.md) and [receipt-us](receipt-us/README.md): image extraction.

See each folder's README for commands, supported package targets and actual limits.
