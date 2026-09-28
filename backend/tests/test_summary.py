from app.models import CheckResult, POLineItem
from app.summary import build_receiving_summary

def cr(key, verdict, sv=None):
    return CheckResult(check_key=key, verdict=verdict, confidence=0.8, detail="d",
                       model_version="m", summary_value=sv)

def po():
    return POLineItem(sku="S", qty_ordered=24, spec_colour="black", spec_variant="750ml")

def all_pass():
    return [cr("sku_identity", "PASS"), cr("colour", "PASS"), cr("variant", "PASS"),
            cr("quantity", "PASS", "24"), cr("carton_count", "PASS", "2"),
            cr("carton_damage", "PASS", "none"), cr("unit_damage", "PASS", "none"),
            cr("units_per_carton", "PASS", "12"), cr("missing_components", "PASS"),
            cr("other_quality", "PASS", "none")]

def swap(checks, key, verdict, sv=None):
    return [c if c.check_key != key else cr(key, verdict, sv) for c in checks]

def test_identity_yes_when_all_pass():
    s = build_receiving_summary(all_pass(), po())
    assert s["identity_match"] == "yes" and s["quality_flags"] == []
    assert s["qty_received"] == "24" and s["units_per_carton_counted"] == "12"

def test_identity_no_and_flag_on_colour_fail():
    s = build_receiving_summary(swap(all_pass(), "colour", "FAIL"), po())
    assert s["identity_match"] == "no" and s["quality_flags"] == ["wrong_colour"]

def test_identity_uncertain():
    s = build_receiving_summary(swap(all_pass(), "sku_identity", "UNCERTAIN"), po())
    assert s["identity_match"] == "uncertain"

def test_both_variant_flags():
    checks = swap(all_pass(), "colour", "FAIL")
    checks = swap(checks, "variant", "FAIL")
    assert build_receiving_summary(checks, po())["quality_flags"] == \
        ["wrong_colour", "wrong_variant"]

def test_damage_summary_value():
    s = build_receiving_summary(swap(all_pass(), "carton_damage", "FAIL", "crushing"), po())
    assert s["carton_damage"] == "crushing"

def test_derived_qty_formula():
    # quantity uncertain, but cartons x units_per_carton known -> derived qty_received
    checks = swap(all_pass(), "quantity", "UNCERTAIN", "uncertain")
    s = build_receiving_summary(checks, po())
    assert s["qty_received"] == "24"
    assert s["qty_received_source"] == "derived (cartons x units_per_carton)"

def test_qty_stays_uncertain_without_factors():
    checks = swap(all_pass(), "quantity", "UNCERTAIN", "uncertain")
    checks = swap(checks, "carton_count", "UNCERTAIN", "uncertain")
    s = build_receiving_summary(checks, po())
    assert s["qty_received"] == "uncertain"

def test_missing_components_flag():
    s = build_receiving_summary(swap(all_pass(), "missing_components", "FAIL"), po())
    assert "missing_components" in s["quality_flags"]

def test_obvious_defect_flag():
    s = build_receiving_summary(swap(all_pass(), "other_quality", "FAIL"), po())
    assert "obvious_defect" in s["quality_flags"]