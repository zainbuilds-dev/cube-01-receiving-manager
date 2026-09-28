import io

from PIL import Image

from app.quality import classify
from app.checks import quantity
from app.models import (CheckContext, ImageObservation, ObsProvenance, POLineItem)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
ALPHA = {"Authorization": "Bearer alpha-demo-token"}
PO = {"unit_id": "UNIT-Q1", "po_number": "PO-Q1", "po_line": 1,
      "line_items": [{"sku": "SKU-Q1", "qty_ordered": 10}]}

# ---- classify (pure, deterministic) ----
def test_classify_acceptable():
    assert classify(400.0, 128.0, 800) == ("ACCEPTABLE", [])

def test_classify_degraded_blur():
    v, r = classify(100.0, 128.0, 800)
    assert v == "DEGRADED" and "blurry" in r

def test_classify_rejected_severe_blur():
    v, r = classify(20.0, 128.0, 800)
    assert v == "REJECTED" and "severely_blurry" in r

def test_classify_rejected_dark():
    v, r = classify(400.0, 20.0, 800)
    assert v == "REJECTED" and "extremely_dark" in r

def test_classify_degraded_dark():
    v, r = classify(400.0, 40.0, 800)
    assert v == "DEGRADED" and "too_dark" in r

def test_classify_resolution():
    assert classify(400.0, 128.0, 150)[0] == "REJECTED"
    v, r = classify(400.0, 128.0, 350)
    assert v == "DEGRADED" and "low_resolution" in r

# ---- quantity conflicts across reliable counts ----
def obs(**kw):
    base = dict(visible_sku_text=None, visible_product_text=None, printed_quantity=None,
                visible_unit_count=None, count_confidence=None, full_contents_visible=False,
                cartons_visible=1, dominant_product_color=None, color_reliability="good",
                label_colour_text=None, label_variant_text=None, visible_components=None,
                contents_open_for_inspection=False, damages=[], quality_issues=[], notes=None)
    base.update(kw)
    return ImageObservation(**base)

def ctx(obs_list):
    po = POLineItem(sku="SKU-Q1", qty_ordered=24)
    provs = [ObsProvenance(image_id=f"img_{i+1}", sha256=f"sha{i}", observation=o)
             for i, o in enumerate(obs_list)]
    return CheckContext(po=po, observations=provs, model_version="t")

def test_qty_conflicting_reliable_counts():
    r = quantity.run(ctx([obs(visible_unit_count=24, count_confidence=0.9,
                              full_contents_visible=True),
                          obs(visible_unit_count=22, count_confidence=0.85,
                              full_contents_visible=True)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

def test_qty_agreeing_reliable_counts_pass():
    r = quantity.run(ctx([obs(visible_unit_count=24, count_confidence=0.9,
                              full_contents_visible=True),
                          obs(visible_unit_count=24, count_confidence=0.85,
                              full_contents_visible=True)]))
    assert r.verdict == "PASS" and r.summary_value == "24"

# ---- all photos rejected -> PENDING_REVIEW (offline: no VLM call happens) ----
def test_all_photos_rejected_goes_pending_review():
    buf = io.BytesIO()
    Image.new("RGB", (120, 120), (128, 128, 128)).save(buf, "PNG")
    r = client.post("/api/records", json=PO, headers=ALPHA)
    rid = r.json()["record_id"]
    up = client.post(f"/api/records/{rid}/images",
                     files={"files": ("tiny.png", buf.getvalue(), "image/png")},
                     headers=ALPHA)
    assert up.status_code == 200
    ins = client.post(f"/api/records/{rid}/inspect", headers=ALPHA)
    assert ins.status_code == 200
    body = ins.json()
    assert body["inspection_status"] == "PENDING_REVIEW"
    assert body["outcome"]["decision"] == "UNCERTAIN"
    assert body["outcome"]["disposition"] == "HOLD_FOR_REVIEW"
    assert all(c["uncertainty_reason"] == "LOW_IMAGE_QUALITY" for c in body["checks"])
    assert body["images"][0]["quality"]["verdict"] == "REJECTED"