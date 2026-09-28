Receiving Manager — CUBE Buildathon (Sydon.AI × CodeQuesters)
An AI receiving-dock agent that verifies incoming shipments against a purchaseorder using receiving photographs — producing a PASS / FAIL / UNCERTAINdecision with per-check evidence, not a chatbot verdict.

Track: Receiving Manager · Round 2 · Solo build

The problem
At goods-receiving time, an operator has a PO and photos of what physicallyarrived. They must answer: did we receive exactly what was ordered, inacceptable visible condition? — without guessing, and without trusting asingle opaque model judgment.

What it does
Given a PO line (SKU, colour/variant spec, components, carton/quantity specs)and 1–8 receiving photographs, the agent runs 10 discrete checks:

SKU identity (barcode/QR tier → label-text tier), colour, variant, quantity(expected vs observed), carton count, carton damage, product damage, units percarton, missing components, other visible quality issues.

Each check returns PASS / FAIL / UNCERTAIN / NOT_APPLICABLE with evidenceitems (image, quote, strength), confidence, model version and latency. Adeterministic, versioned decision policy derives the overall decision —the LLM never decides.

Key design principles
UNCERTAIN is a first-class outcome with a machine-readable reasontaxonomy (INSUFFICIENT_EVIDENCE, OCCLUSION, CONFLICTING_EVIDENCE,LOW_IMAGE_QUALITY, EXTRACTION_FAILED). "Not visible is not missing";"not visible is not undamaged."
Extraction is blind to the PO. The VLM only reports observations;all comparisons are deterministic Python. Extraction claims cannot anchortoward the expected answer.
Fail-open. API errors or rejected photos still save the capture andproduce a record (status PENDING_REVIEW). The operator is never blocked,and nothing is fabricated.
Evidence records. Every decision ships with a structured JSON record(schema v1.1.0) including a SHA-256 content hash for integrityverification of the record as produced.
Human override with full audit trail. Original decision, new decision,operator, reason and timestamp are preserved — overrides are data.
Org tenancy isolation. Two demo orgs; every query is org-scoped andverified by adversarial tests (cross-org record/image access → 404).

Quickstart
git clone https://github.com/zainbuilds-dev/cube-01-receiving-manager.gitcd cube-01-receiving-managerpython -m venv venvvenv\Scripts\python.exe -m pip install -r backend\requirements.txt# .env in project root:# GEMINI_API_KEY=<free key from aistudio.google.com/apikey># GEMINI_MODEL=gemini-flash-latest# GEMINI_FALLBACK_MODELS=gemini-3.1-flash-lite# ORG_ALPHA_TOKEN=alpha-demo-token# ORG_BRAVO_TOKEN=bravo-demo-tokenvenv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --port 8000# new terminal:cd frontend && npm install && npm run dev   # http://localhost:5173
Example workflow
Open the UI (Alpha org) → New Receiving Record
Enter the PO (unit_id, SKU, spec colour/variant/components, cartons, qty)
Upload receiving photos → Run Receiving Inspection
Result screen: decision banner → receiving summary → expected-vs-observed →
per-check cards with photo evidence, model version, latency, UNCERTAIN reasons
Review queue for UNCERTAIN/pending records; override with reason (audited)
Export the evidence record JSON
API: GET /docs (FastAPI) after starting the server. All endpoints require
Authorization: Bearer <org-token>.

Documentation
ARCHITECTURE.md — components, data flow, decision policy, security
EVALUATION.md — what was measured, what was not, failure modes
Limitations (honest)
No blind held-out evaluation on 50 unseen units was completed within the
build window; see EVALUATION.md for what was measured.
Single VLM provider (Google Gemini free tier); quality varies by model and load.
Evidence-record hash verifies integrity of the record as produced — it is not
a tamper-evident, immutable or anchored ledger.
Demo-grade static org tokens; no operator authentication (documented).
Barcode/QR tier is an optional dependency (pyzbar); it degrades gracefully
when unavailable and the SKU check falls back to label text.
MVP path is single-SKU records (data model supports multiple line items).
Deployment: runs locally (4 commands); no cloud deployment was completed.
Known issues
Free-tier Gemini occasionally returns 503 under load → the fallback model
chain retries alternates; total failure fails open to PENDING_REVIEW.
A QR/barcode that matches the PO overrides contradictory label text
(documented Tier-1-vs-Tier-2 conflict behavior; see ARCHITECTURE.md).
