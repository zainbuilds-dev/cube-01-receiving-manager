# Cube Buildathon · 01 · Receiving Manager

**Commerce Context stream · Round 2 · Individual Build**

> Five agents, one unit, one record that follows it.
> A physical product arrives, gets prepped, gets shipped, comes back. At every step a person makes a fast judgment that nobody records. **You build the agent that makes one of those judgments, and leaves proof.**

**New here? Read these first:**

1. [`GITHUB-GUIDE.md`](GITHUB-GUIDE.md) explains how to fork the repository, set it up, build and push your work.
2. [`RULES.md`](RULES.md) covers the repository and engineering rules.

---

## This implementation

This fork contains an MVP for recording a supplier delivery against one purchase-order line. It accepts receiving images, extracts image observations, runs ten checks, applies a deterministic decision policy, and stores an evidence record that can be reviewed or overridden by an operator.

The implementation is not production-ready and has not been accuracy-evaluated. See [`ARCHITECTURE.md`](ARCHITECTURE.md) for system details and [`EVALUATION.md`](EVALUATION.md) for the evaluation status and required methodology.

### Local setup

Prerequisites: Python 3.11 or newer, Node.js supported by Vite 8, and a Gemini API key for image inspection.

From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix frontend install
Copy-Item .env.example .env
```

Set `GEMINI_API_KEY` in `.env`. The default model is configured in `backend/app/config.py`; optionally set `GEMINI_MODEL` and `GEMINI_FALLBACK_MODELS` there as environment values. Do not commit `.env` or credentials.

Start both the API and frontend from the `frontend` directory:

```powershell
Set-Location frontend
npm run dev
```

The dev command starts the API on port 8000 if it is not already healthy, then starts Vite and prints its URL (normally `http://localhost:5173`). The frontend proxies `/api` and `/health` to the API. Stop the command with Ctrl+C; it stops only the API process it started. Image inspection requires a valid Gemini key; intake and record review can be exercised without claiming model accuracy.

Run checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
npm --prefix frontend run build
```

### Render deployment

The root `render.yaml` Blueprint deploys the API and built frontend together as one free Docker web service: https://receiving-manager-fullstack.onrender.com. `GEMINI_API_KEY` is currently unset in Render; add it in the service environment to enable image inspection. The free service uses ephemeral storage, so records and uploaded images can be lost when the service restarts or redeploys. The included organization tokens are demo credentials, not production authentication.

### Scope and limitations

- The API currently supports exactly one purchase-order line per record.
- The database is local SQLite and tenant access is enforced by application-level organization filters, not database row-level security.
- Usable photos for one receiving record are sent in one indexed Gemini batch; each deterministic check is then evaluated from those observations.
- Organization tokens are static demo credentials and are not production authentication.
- Image-quality thresholds are provisional heuristics and need validation on real receiving photos.
- Missing API credentials or model failures preserve the capture and return `PENDING_REVIEW`/`UNCERTAIN`; image inspection itself requires a valid Gemini key.
- This fork currently has no held-out labeled image set or measured per-check performance; unit tests are not accuracy results.
- The public demo is https://receiving-manager-fullstack.onrender.com; no demo-video URL is provided.
- The mandatory LinkedIn post and its URL have not been provided; publish the post, tag CodeQuesters and Sydon.AI, then include its URL in the official form.

These limitations mean the current implementation does not yet satisfy all engineering and submission requirements in [`RULES.md`](RULES.md) and the participant handbook.

### Final submission items

- GitHub fork: this repository.
- README and architecture: [`README.md`](README.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md).
- Evaluation report: [`EVALUATION.md`](EVALUATION.md), currently without measured results.
- Demo video: not yet recorded or linked.
- Deployment URL: https://receiving-manager-fullstack.onrender.com.
- LinkedIn post URL: mandatory, but not available in this repository; include it in the official form after publishing and tagging CodeQuesters and Sydon.AI.
- Final submission: complete the official form before its deadline; this repository folder is not the submission form.

---

## Your problem statement: Receiving Manager

|                              |                                                                                     |
| ---------------------------- | ----------------------------------------------------------------------------------- |
| **Position in the chain**    | Step 1 of 5. Supplier delivery.                                                     |
| **Customer**                 | Seller or 3PL taking supplier delivery                                              |
| **What gets recorded**       | Condition on arrival                                                                |
| **Who consumes your output** | Prep Manager (next in the chain) and Recovery Manager (supplier and inbound claims) |

A pallet arrives from a manufacturer, often overseas. Someone opens the cartons and decides whether what arrived is what was ordered: right SKU, right count, undamaged, to the quality agreed. Today this is a spot check at best. Shortages and defects surface weeks later when units fail in prep or come back as returns, by which point the supplier conversation is unwinnable because nothing was recorded on arrival.

**What the agent returns, from photographs at the point of receipt:**

* Identity of the goods against the purchase order line
* Quantity received against quantity ordered, including carton count and units per carton
* Damage visible on cartons and units: crushing, water, tears
* Quality flags against the agreed spec: wrong colour, wrong variant, missing components, obvious defects

> This is where supplier disputes originate, and the only point at which a claim against the supplier is still possible. Every downstream problem in this chain is cheaper if it was caught here.

### The chain you are part of

```text
 Supplier delivery      Inbound to Amazon     Outbound to buyer     Customer return        Money back
 ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
 │ 01 Receiving │ ───▶ │ 02 Prep      │ ───▶ │ 03 Pack      │ ───▶ │ 04 Returns   │      │ 05 Recovery  │
 │ condition on │      │ compliance   │      │ contents at  │      │ condition &  │      │ reads all    │
 │ arrival      │      │ proof        │      │ seal         │      │ disposition  │      │ four → claim │
 └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────┬───────┘      └──────▲───────┘
        └─────────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘
```

The first four are the same machine: a camera, a model, and a decision bound to a record. What changes is the ruleset, the buyer and the moment. The fifth has no camera. It turns the other four's records into a claim.

Your output has to be usable by another pod. That's deliberate, and it's scored.

---

## Reference and evaluation data

The original track repository's synthetic sample CSV is not included in this fork. It is not an evaluation set, and no labeled receiving-image fixtures are currently checked in. Do not infer real marketplace requirements or model performance from synthetic examples. See [`EVALUATION.md`](EVALUATION.md) for the missing evaluation work.

---

## How this works

You have a defined problem statement, supporting domain information and an engineering repository to build from. Understand the customer and operational workflow before writing code, then build and measure whether the solution works.

Your goal is to turn the Receiving Manager problem into a working, measurable agent.

### What you're given

* This problem statement
* A domain brief covering the real economics, fee structures and what a working day in a warehouse looks like *(shared by the organisers)*
* The engineering rules in [`RULES.md`](RULES.md)
* Official repository documentation and supporting resources

### What you produce

Build your solution in **your own GitHub fork**.

Your final Round 2 submission should include:

* A working Receiving Manager
* A `README.md` explaining your solution, setup, assumptions and limitations
* An `ARCHITECTURE.md`
* An eval report/results with numbers and named failure modes
* A working demo/video
* A deployment URL, where applicable
* Your mandatory LinkedIn post URL

## Build and submission flow

```text
Understand
    ↓
Build
    ↓
Test
    ↓
Evaluate
    ↓
Document
    ↓
Demo / Deploy
    ↓
Submit
```

Round 2 is an **individual build**.

The official build phase begins on **25 September 2026 at 9:00 AM IST**.

Submissions open from **27 September 2026**.

The final submission deadline is **1 October 2026 at 6:00 PM IST**.

The submission form closes permanently at the deadline. **There is no resubmission.**

All code commits forming your Round 2 submission must be made during the authorised build phase. Do not continue making Round 2 code changes after the build phase ends.

## What we're being straight with you about

* **The core assumption is untested.** Nobody knows yet whether vision models can identify products and grade condition on long-tail catalogues without per-SKU training. Finding out that it doesn't hold, and documenting that clearly, counts as a successful outcome.
* **Nobody has spoken to a customer yet.** If you can get a real prep center or seller on a call, ask them to rank the five problems by urgency. Don't ask whether they'd buy what you're building.
* **The background documents disagree in places.** A contradiction is a finding. Raise it as an Issue labelled `finding`.

---

## Evaluation

Your Round 2 submission is evaluated out of **100 points**:

| Criterion                                    |  Points |
| -------------------------------------------- | ------: |
| Problem Understanding & Solution Relevance   |  **15** |
| Agent Functionality & Decision Quality       |  **25** |
| Evaluation, Accuracy & Uncertainty Handling  |  **25** |
| Evidence, Traceability & Engineering Quality |  **20** |
| UX, Demo & Documentation                     |  **15** |
| **TOTAL**                                    | **100** |

For the vision-based portions of the Receiving Manager, use an appropriate unseen/held-out evaluation set and report your methodology, results, false positives, false negatives, `UNCERTAIN` cases and failure modes.

---

## Evidence and decision traceability

Your Receiving Manager should leave evidence behind for its decisions.

At minimum, the workflow should make it possible to understand:

```text
What was received?
        ↓
What was expected?
        ↓
What checks were performed?
        ↓
What did the agent find?
        ↓
What verdict was produced?
        ↓
Why?
```

Use the official evidence contract provided by the organisers as the baseline for interoperability with the other Managers.

---

## PASS · FAIL · UNCERTAIN

For individual checks:

* **PASS** — the evidence supports the condition.
* **FAIL** — the evidence shows the condition is not met.
* **UNCERTAIN** — the evidence is insufficient for a reliable judgment.

`UNCERTAIN` is not simply a low-confidence PASS.

---

*CUBE Buildathon · Commerce Context*
