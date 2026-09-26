# Evidence Record Contract (Draft)

**Status:** Local-schema draft only. This has not been agreed with other pods and must not be described as interoperable yet.

## Current record envelope

The backend evidence builder emits these top-level fields:

| Field | Current meaning |
|---|---|
| `record_id` | Receiving record identifier |
| `schema_version` | Version from backend configuration |
| `organization_id`, `client_id` | Tenant/client context |
| `agent` | Agent name and version |
| `subject` | PO number, supplier, and line items |
| `captured_at` | Capture timestamp |
| `operator_label` | Currently initialized to null |
| `images` | Image evidence references/provenance supplied by the workflow |
| `checks` | Per-check results and evidence items |
| `outcome` | Decision-engine output |
| `overrides` | Operator overrides; currently initialized as an empty list |
| `status` | Record status; currently initialized as `ACTIVE` |
| `content_hash` | SHA-256 over the sorted, compact JSON record before this hash field is added |

## Check result

A check result contains `check_key`, `verdict`, `confidence`, `detail`, `evidence`, `model_version`, and `latency_ms`, with optional `uncertainty_reason`. Current verdicts include `PASS`, `FAIL`, `UNCERTAIN`, and `NOT_APPLICABLE`. Evidence items may include a type, image ID, quote, description, and strength.

## Interoperability decisions still needed

Agree field names and types, identifier ownership, timestamp format, image-reference access controls, verdict semantics, schema versioning, override representation, hash canonicalization, and privacy/retention expectations with downstream pods. Do not treat this draft as a shared contract until those decisions are reviewed and accepted.
