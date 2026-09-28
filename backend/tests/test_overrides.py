import json

from fastapi.testclient import TestClient

from app import db
from app.main import app

client = TestClient(app)
ALPHA = {"Authorization": "Bearer alpha-demo-token"}
BRAVO = {"Authorization": "Bearer bravo-demo-token"}
PO = {"unit_id": "UNIT-OV1", "po_number": "PO-OV1", "po_line": 1,
      "line_items": [{"sku": "SKU-OV1", "qty_ordered": 10}]}

def _seed_inspected(rid: str):
    """Inject a minimal evidence record directly (offline: no VLM needed)."""
    rec = {
        "record_id": rid, "schema_version": "1.1.0",
        "organization_id": "org_demo_alpha", "client_id": "client_demo",
        "agent": {"name": "receiving-manager", "version": "t"},
        "subject": {"unit_id": "U", "po_number": "P", "po_line": 1, "supplier": None,
                    "operator_id": None, "line_items": []},
        "captured_at": "2026-01-01T00:00:00Z", "operator_label": None,
        "images": [], "checks": [], "receiving_summary": {},
        "outcome": {"decision": "UNCERTAIN", "disposition": "HOLD_FOR_REVIEW",
                    "decided_by": "decision-engine/policy-1.2.0", "decided_at": "t",
                    "policy_version": "1.2.0", "reason": "seeded"},
        "inspection_status": "INSPECTED", "overrides": [], "status": "ACTIVE",
        "content_hash": "seeded",
    }
    db.run("UPDATE records SET status='INSPECTED', decision='UNCERTAIN', "
           "evidence_json=? WHERE org_id=? AND id=?",
           (json.dumps(rec), "org_demo_alpha", rid))

def _make_record():
    r = client.post("/api/records", json=PO, headers=ALPHA)
    rid = r.json()["record_id"]
    _seed_inspected(rid)
    return rid

def test_override_requires_inspection():
    r = client.post("/api/records", json=PO, headers=ALPHA)
    rid = r.json()["record_id"]
    resp = client.post(f"/api/records/{rid}/override", headers=ALPHA,
                       json={"override_by": "op_x", "override_reason": "r",
                             "new_decision": "PASS"})
    assert resp.status_code == 400

def test_override_same_decision_rejected():
    rid = _make_record()
    resp = client.post(f"/api/records/{rid}/override", headers=ALPHA,
                       json={"override_by": "op_x", "override_reason": "r",
                             "new_decision": "UNCERTAIN"})
    assert resp.status_code == 400

def test_override_success_full_audit_trail():
    rid = _make_record()
    resp = client.post(f"/api/records/{rid}/override", headers=ALPHA,
                       json={"override_by": "op_dana",
                             "override_reason": "Manually counted 10 units in person; photo angle hid two.",
                             "new_decision": "PASS"})
    assert resp.status_code == 200
    body = resp.json()
    ov = body["overrides"][0]
    assert ov["original_decision"] == "UNCERTAIN" and ov["new_decision"] == "PASS"
    assert ov["override_by"] == "op_dana" and "Manually counted" in ov["override_reason"]
    assert body["outcome"]["decision"] == "PASS"
    assert body["outcome"]["disposition"] == "ACCEPT"
    assert body["outcome"]["decided_by"] == "human-override/op_dana"
    assert body["status"] == "OVERRIDDEN"
    assert body["content_hash"] != "seeded"

def test_override_cross_org_blocked():
    rid = _make_record()
    resp = client.post(f"/api/records/{rid}/override", headers=BRAVO,
                       json={"override_by": "op_evil", "override_reason": "r",
                             "new_decision": "PASS"})
    assert resp.status_code == 404