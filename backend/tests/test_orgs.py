from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
ALPHA = {"Authorization": "Bearer alpha-demo-token"}
BRAVO = {"Authorization": "Bearer bravo-demo-token"}
# valid PNG magic bytes (storage validates magic, not extensions)
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-body-for-tests"

PO = {
    "unit_id": "UNIT-T1", "po_number": "PO-T1", "po_line": 1, "supplier": "S",
    "operator_id": "op_test",
    "line_items": [{"sku": "SKU-T1", "qty_ordered": 10, "spec_colour": "blue",
                    "spec_variant": "bath", "cartons_ordered": 1,
                    "units_per_carton_ordered": 10}],
}

def test_no_token_is_401():
    r = client.get("/api/records")
    assert r.status_code == 401

def test_second_org_sees_zero_rows():
    r = client.post("/api/records", json=PO, headers=ALPHA)
    assert r.status_code == 200
    rid = r.json()["record_id"]
    r = client.get("/api/records", headers=BRAVO)
    assert r.status_code == 200
    assert rid not in [x["record_id"] for x in r.json()]
    assert r.json() == []   # bravo has no records at all

def test_second_org_cannot_get_other_org_record():
    r = client.post("/api/records", json=PO, headers=ALPHA)
    rid = r.json()["record_id"]
    assert client.get(f"/api/records/{rid}", headers=BRAVO).status_code == 404

def test_second_org_cannot_fetch_other_org_image():
    r = client.post("/api/records", json=PO, headers=ALPHA)
    rid = r.json()["record_id"]
    up = client.post(f"/api/records/{rid}/images",
                     files={"files": ("a.png", PNG_BYTES, "image/png")}, headers=ALPHA)
    assert up.status_code == 200
    sha = up.json()["uploaded"][0]["sha256"]
    assert client.get(f"/api/images/{sha}", headers=ALPHA).status_code == 200
    assert client.get(f"/api/images/{sha}", headers=BRAVO).status_code == 404