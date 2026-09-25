import json
import uuid
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .checks import CHECKS
from .config import CFG
from .decision.engine import decide, load_policy
from .evidence import build_evidence_record
from .extraction.gemini import GeminiProvider
from .extraction.service import PROMPT_VERSION, ExtractionService
from .models import POCreate, CheckContext, utcnow
from .storage import store_image

app = FastAPI(title="Receiving Manager", version=CFG.agent_version)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])
db.init_db()

@app.get("/health")
def health():
    return {"status": "ok", "agent": "receiving-manager", "model": CFG.gemini_model}

@app.post("/api/records")
def create_record(po: POCreate):
    if len(po.line_items) != 1:
        raise HTTPException(400, "MVP supports exactly 1 line item (data model supports more)")
    rid = "rcv_" + uuid.uuid4().hex[:12]
    db.run("INSERT INTO records(id, po_json, status, created_at) VALUES(?,?,?,?)",
           (rid, po.model_dump_json(), "CREATED", utcnow()))
    return {"record_id": rid, "status": "CREATED"}

@app.post("/api/records/{rid}/images")
def upload_images(rid: str, files: list[UploadFile] = File(...)):
    _get_record(rid)
    existing = db.run("SELECT COUNT(*) FROM record_images WHERE record_id=?",
                      (rid,), fetch=True)[0][0]
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
        db.run("INSERT OR IGNORE INTO images(sha256, ext, size, created_at) VALUES(?,?,?,?)",
               (sha, ext, size, utcnow()))
        idx = existing + i
        db.run("INSERT INTO record_images(record_id, sha256, idx, filename) VALUES(?,?,?,?)",
               (rid, sha, idx, f.filename))
        out.append({"image_id": f"img_{idx+1}", "sha256": sha, "filename": f.filename})
    return {"uploaded": out}

@app.get("/api/records")
def list_records():
    rows = db.run("SELECT id, status, decision, created_at FROM records "
                  "ORDER BY created_at DESC", fetch=True)
    return [{"record_id": r[0], "status": r[1], "decision": r[2], "created_at": r[3]}
            for r in rows]

@app.get("/api/records/{rid}")
def get_record(rid: str):
    row = _get_record(rid)
    if row[4]:
        return json.loads(row[4])
    imgs = db.run("SELECT idx, sha256, filename FROM record_images "
                  "WHERE record_id=? ORDER BY idx", (rid,), fetch=True)
    return {"record_id": rid, "status": row[2], "po": json.loads(row[1]),
            "images": [{"image_id": f"img_{r[0]+1}", "sha256": r[1], "filename": r[2]}
                       for r in imgs]}

@app.get("/api/records/{rid}/export")
def export_record(rid: str):
    row = _get_record(rid)
    if not row[4]:
        raise HTTPException(400, "Record not inspected yet")
    return json.loads(row[4])

@app.post("/api/records/{rid}/inspect")
def inspect(rid: str):
    row = _get_record(rid)
    po = POCreate.model_validate_json(row[1])
    imgs = db.run("SELECT idx, sha256, filename FROM record_images "
                  "WHERE record_id=? ORDER BY idx", (rid,), fetch=True)
    if not imgs:
        raise HTTPException(400, "No images uploaded for this record")

    svc = ExtractionService(GeminiProvider())

    def do(im):
        idx, sha, _ = im
        ext = db.run("SELECT ext FROM images WHERE sha256=?", (sha,), fetch=True)[0][0]
        raw = (CFG.image_dir / f"{sha}.{ext}").read_bytes()
        return svc.observe(sha, f"img_{idx+1}", raw)

    image_entries, observations = [], []
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {im[0]: ex.submit(do, im) for im in imgs}
        for im in imgs:
            idx, sha, fname = im
            entry = {"image_id": f"img_{idx+1}", "sha256": sha, "filename": fname}
            try:
                prov, model_id = futs[idx].result()
                observations.append(prov)
            except Exception as e:
                entry["extraction_error"] = f"{type(e).__name__}: {str(e)[:160]}"
            image_entries.append(entry)

    if not observations:
        raise HTTPException(502, "Extraction failed for all images (rate limit or API error); retry shortly")

    model_version = f"gemini:{model_id}|prompt:{PROMPT_VERSION}"
    ctx = CheckContext(po=po.line_items[0], observations=observations,
                       model_version=model_version)
    results = [fn(ctx) for fn in CHECKS.values()]
    outcome = decide(results, load_policy())
    rec = build_evidence_record(rid, po, image_entries, results, outcome)
    db.run("UPDATE records SET status=?, decision=?, evidence_json=? WHERE id=?",
           ("INSPECTED", outcome["decision"], json.dumps(rec), rid))
    return rec

def _get_record(rid: str):
    rows = db.run("SELECT id, po_json, status, decision, evidence_json, created_at "
                  "FROM records WHERE id=?", (rid,), fetch=True)
    if not rows:
        raise HTTPException(404, "Record not found")
    return rows[0]