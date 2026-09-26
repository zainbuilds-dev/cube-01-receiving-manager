# zainbuilds-dev - Receiving Manager

Working submission index for the `zainbuilds-dev` fork. The official guide says the fork is the development repository and the final submission is made through the official form; this folder is an additional, template-formatted index, not form submission confirmation.

## Project source

The implementation remains at the repository root to avoid maintaining duplicate source copies:

- [Headless backend](../../backend/)
- [Frontend](../../frontend/)
- [Backend tests](../../backend/tests/)
- [Sample receiving data](../../data/)

## Expected layout and status

| Face | Deliverable | Status |
|---|---|---|
| 1 | [Customer letter](01-customer-letter.md), [PR/FAQ](02-prfaq.md), [one-pager](03-one-pager.md) | Drafts; customer discovery and targets pending |
| 2 | [CLAUDE.md](CLAUDE.md) | Drafted from repository engineering rules |
| 3 | [Headless agent](agent/README.md) | Backend exists at `../../backend`; held-out fixtures/evaluation pending |
| 4 | [Eval report](eval-report.md) | Method outline only; no measured results yet |
| 5 | Evidence record page | Backend record builder and tests exist; operator-facing evidence page not verified |
| 6 | [Cross-pod contract](contract/evidence-record.md) | Draft from current schema; not agreed with other pods |
| - | [Architecture](architecture.md) | Drafted from current implementation |
| - | [Build brief](build-brief.md), [build log](build-log.md) | Current scope and known gaps recorded |

## Kill condition

Proposed, pending validation with operators: any check that produces a false PASS on the held-out evaluation set stays out of automatic acceptance and is routed for human review.

## Before final submission

Complete customer discovery, confirm the kill condition and metric targets, run a held-out evaluation with two independent labellers, document per-check false positives and false negatives, agree the evidence contract with the other pods, and follow the official submission-form process.
