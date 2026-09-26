from app.models import CheckResult
from app.summary import build_receiving_summary
from app.models import POLineItem

def cr(key, verdict, sv=None):
    return CheckResult(check_key=key, verdict=verdict, confidence=0.8, detail="d",
                       model_version="m", summary_value=sv)

def po():
    return POLineItem(sku="S", qty_ordered=24, spec_colour="black", spec_variant="750ml")

ALL_PASS = [cr("sku_identity", "PASS"), cr("colour", "PASS"), cr("variant", "PASS"),
            cr("quantity", "PASS", "24"), cr("carton_count", "PASS", "2"),
            cr("carton_damage", "PASS", "none"), cr("unit_damage", "PASS", "none")]

def test_identity_yes_when_all_pass():
    s = build_receiving_summary(ALL_PASS, po())
    assert s["identity_match"] == "yes" and s["quality_flags"] == []
    assert s["qty_received"] == "24" and s["carton_damage"] == "none"

def test_identity_no_and_flag_on_colour_fail():
    checks = [c if c.check_key != "colour" else cr("colour", "FAIL") for c in ALL_PASS]
    s = build_receiving_summary(checks, po())
    assert s["identity_match"] == "no" and s["quality_flags"] == ["wrong_colour"]

def test_identity_uncertain():
    checks = [c if c.check_key != "sku_identity" else cr("sku_identity", "UNCERTAIN")
              for c in ALL_PASS]
    assert build_receiving_summary(checks, po())["identity_match"] == "uncertain"

def test_both_variant_flags():
    checks = [c if c.check_key != "colour" else cr("colour", "FAIL") for c in ALL_PASS]
    checks = [c if c.check_key != "variant" else cr("variant", "FAIL") for c in checks]
    assert build_receiving_summary(checks, po())["quality_flags"] == \
        ["wrong_colour", "wrong_variant"]

def test_damage_summary_value():
    checks = [c if c.check_key != "carton_damage"
              else cr("carton_damage", "FAIL", "crushing") for c in ALL_PASS]
    assert build_receiving_summary(checks, po())["carton_damage"] == "crushing"