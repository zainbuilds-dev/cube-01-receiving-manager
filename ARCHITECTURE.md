
# Architecture — Receiving Manager

## Overview
INPUT → VALIDATION → QUALITY GATE → EXTRACTION (blind VLM + local barcode)
→ CHECKS (deterministic) → DECISION (deterministic policy) → EVIDENCE RECORD
→ UI / EXPORT. The AI never decides anything: models produce *claims with
provenance*; deterministic code evaluates checks; a versioned policy decides.

## Components
- **Frontend** — React/TS/Vite, three screens: record intake (PO + photos),
  record list with review-queue filter, results view (decision banner,
  receiving summary, per-check evidence, override panel, JSON export).
  Org switcher (Alpha/Bravo) attaches bearer tokens.
- **Backend** — FastAPI + SQLite (WAL). All endpoints org-scoped via
  `require_org`.
- **Quality gate** (`app/quality.py`) — deterministic, PIL-only: edge energy
  (sharpness proxy), brightness, resolution → ACCEPTABLE / DEGRADED / REJECTED.
  Runs BEFORE the VLM call: rejected photos never consume quota and never
  produce claims.
- **Extraction** (`app/extraction/`) — provider abstraction (`base.py`); Gemini
  provider with a model fallback chain (primary → configured fallbacks) for
  429/503 resilience; content-hash response cache above the provider;
  pyzbar barcode/QR decoding (optional, degrades gracefully). Prompt v2 is
  versioned (`observe_carton@v2`) and the VLM is blind to the PO.
- **Checks** (`app/checks/`) — 10 pure functions over (PO line, observations,
  policy): no LLM calls inside checks. Evidence-strength hierarchy for
  identity: Tier 1 barcode (0.95) > Tier 2 label text (0.9) > visual only
  (never sufficient for identity PASS).
- **Decision engine** (`app/decision/`) — pure function + versioned
  `policy.json` (v1.2.0): any critical FAIL → FAIL/EXCEPTION; else any
  critical UNCERTAIN → UNCERTAIN/HOLD_FOR_REVIEW; else PASS/ACCEPT.
  NOT_APPLICABLE checks are excluded from aggregation (out of scope for this
  PO). `other_quality` is advisory (recorded as a quality flag, does not
  block).
- **Evidence records** (`app/evidence.py`) — schema v1.1.0 with images (+
  quality results), checks (verdict/confidence/evidence/model_version/
  latency/uncertainty_reason), `receiving_summary` (stage contract vocabulary:
  identity_match, carton_damage, unit_damage, cartons_received,
  units_per_carton_counted, qty_received, quality_flags), outcome, overrides,
  and a SHA-256 content hash over the canonical record. The hash supports
  integrity verification of the record as produced — not a tamper-evident or
  anchored ledger.
- **Human override** — `POST /api/records/{id}/override`: appends
  {override_by, override_reason, original_decision, new_decision, timestamp}
  to the record; the machine decision is preserved inside the entry.
  Cross-org override attempts → 404.

## Data flow (one inspection)
1. POST /api/records (PO validated by Pydantic; RCV-XXXX per-org sequence)
2. POST images (magic-byte validation, size cap, content-addressed storage,
   per-org dedupe)
3. POST inspect: per image → quality gate → (if not rejected) cached-or-live
   VLM observation + local barcode decode → claims with provenance
4. Checks evaluate over the aggregate; conflicting reliable counts →
   UNCERTAIN/CONFLICTING_EVIDENCE (never silently resolved)
5. Policy decides; summary maps checks to the stage contract
   (qty_received = cartons × units_per_carton when factors are known)
6. Evidence record hashed and stored; if extraction failed for all images or
   all photos were rejected → fail open: PENDING_REVIEW, all checks
   UNCERTAIN with reason; the capture is never lost and the operator is
   never blocked.

## AI model routing
| Task | Method | Why |
|---|---|---|
| Barcode/QR → SKU | pyzbar (local, deterministic) | Machine-readable codes are read, not guessed |
| SKU/variant/colour label text | VLM reads; deterministic string match vs PO | Only the *reading* needs AI; comparison must not |
| Visual colour | VLM observation + lighting reliability self-report; label text outranks visual | Colour under bad lighting is unreliable |
| Counting | VLM structured count + visibility self-assessment; overage provable from partial view, shortage is not | VLM counting is the weakest link — we encode its failure modes |
| Damage | VLM per-image reports (type/target/location/severity/confidence) | Presence is provable from one image; absence requires visibility |
| Components | Only assessed when packaging is open AND contents visible | "Not visible is not missing" |

Model versions are recorded per check (`model_version`) along with prompt
version and latency.

## Security
- Upload validation by magic bytes (not extensions), 10 MB cap, 8-image cap,
  hex-only image-hash route (path traversal impossible).
- Tenancy: app-layer forced scoping — every tenant-table query carries org_id;
  enforced via a repository-style data layer and **adversarial tests**
  (org B sees zero rows; cross-org record 404; cross-org image 404).
  This is NOT database-level RLS (SQLite has none); a Postgres RLS migration
  path is the documented production step.
- Static demo tokens; production would use operator auth. No secrets in the
  repository (`.env` gitignored).

## Failure handling
| Failure | Behavior |
|---|---|
| VLM 429/503 | Retry with backoff → fallback model chain → per-image error recorded; if all fail: fail-open PENDING_REVIEW |
| Schema violation | Retry (model may self-correct) → per-image error; no fabricated claims |
| Blurry/dark/tiny photo | Quality gate REJECTs before any VLM call; check-level UNCERTAIN/LOW_IMAGE_QUALITY |
| Conflicting reliable counts | UNCERTAIN/CONFLICTING_EVIDENCE with both sides as evidence |
| Sealed packaging | Components UNCERTAIN — never FAIL from invisibility |
| Operator disagreement | Override recorded with full audit trail; original decision preserved |

## Design decisions (and rejected alternatives)
- Deterministic policy over LLM judgment — auditable, testable in
  milliseconds, no prompt-drift in decisions.
- SQLite over Postgres — zero-config reproducibility; RLS path documented.
- One VLM call per image (0 per check) — organizer batching rule satisfied;
  cached by content hash so re-inspection and eval re-runs cost nothing.
- QR-vs-label conflict: Tier-1 barcode wins (documented behavior). Conflict
  detection between tiers is future work; noted honestly.
