# Build Brief

## Goal

Prototype a Receiving Manager workflow that records a supplier delivery against purchase-order expectations, evaluates identity, quantity, visible damage, and variant, and preserves decision evidence for later review.

## Current implementation

- Backend service under [`backend/`](../../backend/) with extraction, four check modules, a deterministic decision engine, evidence-record generation, and tests.
- Frontend under [`frontend/`](../../frontend/) for record intake and per-check result review.
- The evidence record includes a schema version, subject/PO data, images, checks, outcome, override list, status, and a SHA-256 content hash.

## Boundaries and known gaps

- This is an MVP, not a validated production workflow.
- The current API enforces a single purchase-order line.
- No held-out image evaluation, two-labeller agreement, or per-check error rates are included yet.
- Customer discovery and cross-pod contract agreement are pending.
- The current content hash does not establish immutable or tamper-proof storage.
- The actual image fixture set and its licensing/provenance must be documented before evaluation.

## Next evidence needed

1. Define an evaluation protocol and label rubric with two independent labellers.
2. Gather representative, held-out receiving images with documented provenance.
3. Report per-check false positives, false negatives, uncertain cases, and failure modes.
4. Validate operator review behavior, failure/pending behavior, and evidence completeness.
5. Agree the record contract with downstream pods before claiming interoperability.
