# Architecture

## Flow

1. The API receives a purchase order and image references for an intake record.
2. The extraction service observes each image without the PO expectation.
3. Check modules compare the observations with the purchase-order line and emit per-check verdicts with confidence and evidence.
4. The deterministic decision engine combines check outcomes under the configured policy.
5. The evidence builder serializes the PO, image references, checks, outcome, status, and metadata, then computes a SHA-256 content hash.
6. The frontend presents intake records and per-check results for operator review.

## Components

- Backend source: [`backend/app/`](../../backend/app/)
- Check modules: [`backend/app/checks/`](../../backend/app/checks/)
- Decision policy: [`backend/app/decision/`](../../backend/app/decision/)
- Extraction providers: [`backend/app/extraction/`](../../backend/app/extraction/)
- Frontend: [`frontend/src/`](../../frontend/src/)
- Tests: [`backend/tests/`](../../backend/tests/)

## Trust boundaries and limitations

Extraction output is model-generated and may be wrong. A verdict is not proof by itself; retain the evidence and uncertainty reason for review. The content hash detects changes relative to a known serialized record but does not provide immutable storage, trusted timestamping, or identity attestation. Tenant isolation, pending behavior on model errors, and production storage controls must be verified before deployment claims.
