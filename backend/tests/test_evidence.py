from app.evidence import build_evidence_record
from app.models import POLineItem, POCreate, CheckResult

def po():
    return POCreate(unit_id="UNIT-1", po_number="PO-1", po_line=1, supplier="S",
                    operator_id="op_x",
                    line_items=[POLineItem(sku="SKU-1", qty_ordered=24,
                                           spec_colour="Blue", spec_variant="750ml")])

def chk(detail="d"):
    return CheckResult(check_key="quantity", verdict="FAIL", confidence=0.9,
                       detail=detail, model_version="m", summary_value="22")

OUT = {"decision": "FAIL", "decided_by": "x", "decided_at": "t", "policy_version": "1.1.0"}
SUM = {"identity_match": "yes", "carton_damage": "none", "unit_damage": "none",
       "cartons_received": "2", "units_per_carton_counted": "uncertain",
       "qty_received": "22", "quality_flags": []}

def rec(**kw):
    base = dict(record_id="RCV-0001", org="org_demo_alpha", po=po(), images=[],
                checks=[chk()], outcome=OUT, summary=SUM,
                captured_at="2026-01-01T00:00:00Z")
    base.update(kw)
    return build_evidence_record(**base)

def test_hash_stable_for_same_content():
    assert rec()["content_hash"] == rec()["content_hash"]

def test_hash_changes_with_content():
    assert rec(checks=[chk("d1")])["content_hash"] != rec(checks=[chk("d2")])["content_hash"]

def test_required_fields_present():
    r = rec()
    for f in ["record_id", "schema_version", "organization_id", "agent", "subject",
              "unit_id" if False else "captured_at", "images", "checks",
              "receiving_summary", "outcome", "inspection_status", "overrides",
              "status", "content_hash"]:
        assert f in r
    assert r["subject"]["unit_id"] == "UNIT-1"