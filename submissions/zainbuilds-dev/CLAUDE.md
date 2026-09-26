# Durable Project Constraints

These constraints apply to code, evaluations, demos, and written claims in this project.

## Hard rules

- Never invent observations, evidence, customer feedback, evaluation results, or cross-pod agreement.
- Preserve `UNCERTAIN` as a first-class result. Do not silently convert it to PASS.
- Keep model observations blind to purchase-order expectations when performing extraction.
- Bind each decision to the evidence and checks that support it.
- Record operator overrides with the original decision, replacement decision, and reason; do not discard them.
- Treat the record content hash as an integrity aid only. Do not call the record immutable, tamper-proof, or externally anchored.
- Do not commit `.env` files, credentials, tokens, or other secrets.
- Keep tenant data isolated and never expose another organization's records or images.
- On model errors or timeouts, preserve the capture and produce an appropriate pending/review state; do not block the receiving operator.
- Use authoritative sources for operational or marketplace requirements; do not infer current rules from model memory or synthetic sample data.

## Language to avoid unless independently proven

Do not claim production readiness, customer validation, accuracy, savings, fraud prevention, immutable evidence, or cross-pod interoperability without documented evidence supporting the specific claim.
