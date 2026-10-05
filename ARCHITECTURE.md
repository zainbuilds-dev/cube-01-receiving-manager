# Architecture

## Overview

The application is a local-first MVP with a React/Vite operator interface and a FastAPI backend. A receiving record is created from one purchase-order line and one or more carton/product images. The backend creates per-check results, applies a deterministic policy, and stores the result with its supporting evidence.

## Request and decision flow

1. The frontend submits purchase-order details to `POST /api/records` with a bearer token identifying one of the demo organizations.
2. Images are uploaded to `POST /api/records/{id}/images`. The backend validates supported image content and size, calculates SHA-256, and stores files locally. Organization-scoped database rows link images to records.
3. `POST /api/records/{id}/inspect` loads the images. Image quality is assessed deterministically, barcodes are decoded locally when available, and usable images are sent to the configured Groq vision model. Extraction receives the image and observation prompt, not the purchase-order expectation.
4. All usable, uncached images for the receiving record are sent in indexed Groq requests of up to three images each, with configured model retries/fallbacks. The provider combines results and the response must contain exactly one observation per input image index. Image errors are retained in the record. If no usable observations are available, all checks return `UNCERTAIN` and the record is held for review.
5. Ten check modules evaluate identity, colour, variant, quantity, carton count, carton damage, unit damage, units per carton, missing components, and other quality. The decision engine is deterministic: configured critical failures produce `FAIL`, unresolved critical checks produce `UNCERTAIN`, and all critical checks passing produces `PASS`.
6. The evidence builder stores the subject, image metadata, checks, receiving summary, outcome, inspection status, overrides, and a content hash. The frontend displays records, check evidence, quality information, and supports human overrides.

## Components

| Component | Location | Responsibility |
|---|---|---|
| HTTP API and workflow | `backend/app/main.py` | Intake, uploads, inspection, records, exports, images, and overrides |
| Authentication | `backend/app/auth.py` | Resolves static demo bearer tokens to organizations |
| Persistence | `backend/app/db.py`, `backend/app/storage.py` | SQLite metadata and local content-addressed image storage |
| Extraction | `backend/app/extraction/` | Prompt construction, local barcode tier, Groq provider, retries, and cache |
| Image quality | `backend/app/quality.py` | Deterministic quality gate; thresholds remain provisional |
| Checks | `backend/app/checks/` | Ten independent check results with evidence and uncertainty |
| Decision policy | `backend/app/decision/` | Pure deterministic aggregation of check results |
| Evidence and summary | `backend/app/evidence.py`, `backend/app/summary.py` | Structured record, receiving summary, and SHA-256 content hash |
| Operator UI | `frontend/src/` | Intake, record list, results, evidence, and human review |

## Data and trust boundaries

- SQLite tables include the organization identifier in their primary keys and queries filter by organization. This is application-level isolation, not database-enforced row-level security. The repository engineering rule requiring enabled and forced RLS is therefore not met by this SQLite MVP.
- Organization tokens are static demo credentials. The frontend contains the demo choices; this is not production authentication or a secret boundary.
- Images and the SQLite database are local runtime data. Production deployment would need controlled object storage, retention policy, backup, and tenant-enforced authorization.
- The SHA-256 content hash detects changes relative to a known record serialization. It does not provide immutable storage, trusted timestamping, or proof of capture identity.
- Groq is invoked in one or more requests per receiving record for its usable images; deterministic checks share those observations rather than making additional model calls.
- Model observations can be incomplete or incorrect. `UNCERTAIN` is preserved for insufficient evidence and extraction failure; operators can override a completed decision with an audit entry.

## Local service boundaries

The API listens on port 8000 by default. Vite listens on port 5173 and proxies `/api` and `/health` to the API. Local SQLite and image paths are selected from `RCV_DATA_DIR`; extraction cache location can be set with `RCV_CACHE_DIR`. Groq configuration uses `GROQ_API_KEY`, `GROQ_MODEL`, and optional `GROQ_FALLBACK_MODELS` environment variables.