from app.evidence import build_evidence_record
from app.models import POLineItem, POCreate, CheckResult

def po():
    return POCreate(po_number="PO-1", supplier="S",
                    line_items=[POLineItem(sku="SKU-1", expected_qty=24, variant="Blue")])

def chk(detail="d"):
    return CheckResult(check_key="quantity", verdict="FAIL", confidence=0.9,
                       detail=detail, model_version="m")

OUT = {"decision": "FAIL", "decided_by": "x", "decided_at": "t", "policy_version": "1.0.0"}

def test_hash_stable_for_same_content():
    a = build_evidence_record("rcv_1", po(), [], [chk()], OUT, captured_at="2026-01-01T00:00:00Z")
    b = build_evidence_record("rcv_1", po(), [], [chk()], OUT, captured_at="2026-01-01T00:00:00Z")
    assert a["content_hash"] == b["content_hash"]

def test_hash_changes_with_content():
    a = build_evidence_record("rcv_1", po(), [], [chk("d1")], OUT, captured_at="2026-01-01T00:00:00Z")
    b = build_evidence_record("rcv_1", po(), [], [chk("d2")], OUT, captured_at="2026-01-01T00:00:00Z")
    assert a["content_hash"] != b["content_hash"]

def test_required_fields_present():
    r = build_evidence_record("rcv_1", po(), [], [chk()], OUT)
    for f in ["record_id", "schema_version", "organization_id", "client_id", "agent",
              "subject", "captured_at", "images", "checks", "outcome", "overrides",
              "status", "content_hash"]:
        assert f in r