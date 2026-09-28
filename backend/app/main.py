import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import db
from .auth import require_org
from .checks import CHECKS
from .config import CFG
from .decision.engine import decide, load_policy
from .evidence import build_evidence_record
from .extraction.gemini import GeminiProvider
from .extraction.service import PROMPT_VERSION, ExtractionService
from .models import POCreate, CheckContext, CheckResult, OverrideRequest, utcnow
from .storage import store_image
from .summary import build_receiving_summary

app = FastAPI(title="Receiving Manager", version=CFG.agent_version)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
db.init_db()

SHA_RE = re.compile(r"^[0-9a-f]{64}$")
MEDIA = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp"}

@app.get("/health")
def health():
    return {"status": "ok", "agent": "receiving-manager", "model": CFG.gemini_model,
            "version": CFG.agent_version}

@app.post("/api/records")
def create_record(po: POCreate, org: str = Depends(require_org)):
    if len(po.line_items) != 1:
        raise HTTPException(400, "MVP supports exactly 1 line item (data model supports more)")
    rid = db.next_record_id(org)
    db.run("INSERT INTO records(org_id, id, unit_id, po_json, status, created_at) "
           "VALUES(?,?,?,?,?,?)",
           (org, rid, po.unit_id, po.model_dump_json(), "CREATED", utcnow()))
    return {"record_id": rid, "unit_id": po.unit_id, "org_id": org, "status": "CREATED"}

@app.post("/api/records/{rid}/images")
def upload_images(rid: str, files: list[UploadFile] = File(...),
                  org: str = Depends(require_org)):
    _get_record(org, rid)
    existing = db.run("SELECT COUNT(*) FROM record_images WHERE org_id=? AND record_id=?",
                      (org, rid), fetch=True)[0][0]
    if existing + len(files) > CFG.max_images_per_record:
        raise HTTPException(400, f"Max {CFG.max_images_per_record} images per record")
    out = []
    for i, f in enumerate(files):
        raw = f.file.read()
        if len(raw) > CFG.max_image_bytes:
            raise HTTPException(400, f"{f.filename} exceeds size limit")
        try:
            sha, ext, size = store_image(raw)
        except ValueError as e:
            raise HTTPException(400, f"{f.filename}: {e}")
        db.run("INSERT OR IGNORE INTO images(org_id, sha256, ext, size, created_at) "
               "VALUES(?,?,?,?,?)", (org, sha, ext, size, utcnow()))
        idx = existing + i
        db.run("INSERT INTO record_images(org_id, record_id, sha256, idx, filename) "
               "VALUES(?,?,?,?,?)", (org, rid, sha, idx, f.filename))
        out.append({"image_id": f"img_{idx+1}", "sha256": sha, "filename": f.filename})
    return {"uploaded": out}

@app.get("/api/records")
def list_records(org: str = Depends(require_org)):
    rows = db.run("SELECT id, unit_id, status, decision, created_at FROM records "
                  "WHERE org_id=? ORDER BY created_at DESC", (org,), fetch=True)
    return [{"record_id": r[0], "unit_id": r[1], "status": r[2], "decision": r[3],
             "created_at": r[4]} for r in rows]

@app.get("/api/records/{rid}")
def get_record(rid: str, org: str = Depends(require_org)):
    row = _get_record(org, rid)
    if row[4]:
        return json.loads(row[4])
    imgs = db.run("SELECT idx, sha256, filename FROM record_images "
                  "WHERE org_id=? AND record_id=? ORDER BY idx", (org, rid), fetch=True)
    return {"record_id": rid, "status": row[2], "po": json.loads(row[1]),
            "images": [{"image_id": f"img_{r[0]+1}", "sha256": r[1], "filename": r[2]}
                       for r in imgs]}

@app.get("/api/records/{rid}/export")
def export_record(rid: str, org: str = Depends(require_org)):
    row = _get_record(org, rid)
    if not row[4]:
        raise HTTPException(400, "Record not inspected yet")
    return json.loads(row[4])

@app.post("/api/records/{rid}/inspect")
def inspect(rid: str, org: str = Depends(require_org)):
    row = _get_record(org, rid)
    po = POCreate.model_validate_json(row[1])
    imgs = db.run("SELECT idx, sha256, filename FROM record_images "
                  "WHERE org_id=? AND record_id=? ORDER BY idx", (org, rid), fetch=True)
    if not imgs:
        raise HTTPException(400, "No images uploaded for this record")

    svc = ExtractionService(GeminiProvider())

    def do(im):
        idx, sha, _ = im
        ext = db.run("SELECT ext FROM images WHERE org_id=? AND sha256=?",
                     (org, sha), fetch=True)[0][0]
        raw = (CFG.image_dir / f"{sha}.{ext}").read_bytes()
        return svc.observe(sha, f"img_{idx+1}", raw)

    image_entries, observations = [], []
    model_id = "unknown"
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {im[0]: ex.submit(do, im) for im in imgs}
        for im in imgs:
            idx, sha, fname = im
            entry = {"image_id": f"img_{idx+1}", "sha256": sha, "filename": fname}
            try:
                prov, mid = futs[idx].result()
                observations.append(prov)
                if (prov.quality or {}).get("verdict") != "REJECTED":
                    model_id = mid
            except Exception as e:
                entry["extraction_error"] = f"{type(e).__name__}: {str(e)[:160]}"
            image_entries.append(entry)

    for e in image_entries:
        prov = next((p for p in observations if p.image_id == e["image_id"]), None)
        if prov is not None and prov.quality:
            e["quality"] = prov.quality

    usable = [p for p in observations if (p.quality or {}).get("verdict") != "REJECTED"]

    if usable:
        model_version = f"gemini:{model_id}|prompt:{PROMPT_VERSION}"
        ctx = CheckContext(po=po.line_items[0], observations=usable,
                           model_version=model_version)
        results = [fn(ctx) for fn in CHECKS.values()]
        status = "INSPECTED"
    elif observations:
        qreasons = "; ".join(sorted({r for p in observations
                                     for r in (p.quality or {}).get("reasons", [])}))
        model_version = f"quality-gate|prompt:{PROMPT_VERSION}"
        results = [
            CheckResult(check_key=key, verdict="UNCERTAIN", confidence=0.0,
                        detail=(f"All {len(observations)} photograph(s) were rejected by "
                                f"the image-quality gate ({qreasons}). The capture is "
                                "retained; nothing could be reliably verified "
                                "automatically. Human review required."),
                        evidence=[], model_version=model_version, latency_ms=0,
                        uncertainty_reason="LOW_IMAGE_QUALITY", summary_value="uncertain")
            for key in CHECKS
        ]
        status = "PENDING_REVIEW"
    else:
        model_version = f"extraction-failed|prompt:{PROMPT_VERSION}"
        results = [
            CheckResult(check_key=key, verdict="UNCERTAIN", confidence=0.0,
                        detail=("Vision extraction failed for every image (API error or "
                                "rate limit). The capture is retained; nothing could be "
                                "verified automatically. Human review required."),
                        evidence=[], model_version=model_version, latency_ms=0,
                        uncertainty_reason="EXTRACTION_FAILED", summary_value="uncertain")
            for key in CHECKS
        ]
        status = "PENDING_REVIEW"

    outcome = decide(results, load_policy())
    summary = build_receiving_summary(results, po.line_items[0])
    rec = build_evidence_record(rid, org, po, image_entries, results, outcome,
                                summary, inspection_status=status)
    db.run("UPDATE records SET status=?, decision=?, evidence_json=? WHERE org_id=? AND id=?",
           (status, outcome["decision"], json.dumps(rec), org, rid))
    return rec

@app.post("/api/records/{rid}/override")
def override_record(rid: str, req: OverrideRequest, org: str = Depends(require_org)):
    """Human override with full audit trail: the machine decision is preserved
    inside the override entry — overrides are data, never discarded."""
    row = _get_record(org, rid)
    if not row[4]:
        raise HTTPException(400, "Record not inspected yet — nothing to override")
    if not req.override_by.strip() or not req.override_reason.strip():
        raise HTTPException(400, "override_by and override_reason are required")
    rec = json.loads(row[4])
    original_decision = rec["outcome"]["decision"]
    if original_decision == req.new_decision:
        raise HTTPException(400, f"New decision equals current decision ({original_decision})")

    entry = {
        "override_by": req.override_by.strip(),
        "override_reason": req.override_reason.strip(),
        "original_decision": original_decision,
        "new_decision": req.new_decision,
        "timestamp": utcnow(),
    }
    rec["overrides"].append(entry)
    rec["outcome"] = {
        **rec["outcome"],
        "decision": req.new_decision,
        "disposition": {"PASS": "ACCEPT", "FAIL": "EXCEPTION",
                        "UNCERTAIN": "HOLD_FOR_REVIEW"}[req.new_decision],
        "decided_by": f"human-override/{req.override_by.strip()}",
        "decided_at": entry["timestamp"],
        "reason": f"Human override: {req.override_reason.strip()}",
    }
    rec["status"] = "OVERRIDDEN"
    rec["content_hash"] = hashlib.sha256(
        json.dumps({k: v for k, v in rec.items() if k != "content_hash"},
                   sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    db.run("UPDATE records SET status=?, decision=?, evidence_json=? "
           "WHERE org_id=? AND id=?",
           ("OVERRIDDEN", req.new_decision, json.dumps(rec), org, rid))
    return rec

@app.get("/api/images/{sha}")
def get_image(sha: str, org: str = Depends(require_org)):
    if not SHA_RE.match(sha):
        raise HTTPException(400, "invalid hash")
    row = db.run("SELECT ext FROM images WHERE org_id=? AND sha256=?", (org, sha),
                 fetch=True)
    if not row:
        raise HTTPException(404, "image not found")
    ext = row[0][0]
    path = CFG.image_dir / f"{sha}.{ext}"
    if not path.exists():
        raise HTTPException(404, "image file missing")
    return FileResponse(path, media_type=MEDIA[ext])

def _get_record(org: str, rid: str):
    rows = db.run("SELECT id, po_json, status, decision, evidence_json, created_at "
                  "FROM records WHERE org_id=? AND id=?", (org, rid), fetch=True)
    if not rows:
        raise HTTPException(404, "Record not found")
    return rows[0]