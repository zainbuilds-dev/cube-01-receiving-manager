import pytest
from app.decision.engine import PolicyError, decide, load_policy
from app.models import CheckResult

def cr(key, verdict):
    return CheckResult(check_key=key, verdict=verdict, confidence=0.8,
                       detail="d", model_version="m")

POLICY = load_policy()
KEYS = ["sku_identity", "colour", "variant", "quantity",
        "carton_count", "carton_damage", "unit_damage"]

def test_any_fail_wins():
    out = decide([cr("sku_identity", "PASS"), cr("colour", "PASS"), cr("variant", "PASS"),
                  cr("quantity", "FAIL"), cr("carton_count", "PASS"),
                  cr("carton_damage", "PASS"), cr("unit_damage", "PASS")], POLICY)
    assert out["decision"] == "FAIL" and out["disposition"] == "EXCEPTION"

def test_uncertain_when_no_fail():
    out = decide([cr("sku_identity", "PASS"), cr("colour", "PASS"), cr("variant", "PASS"),
                  cr("quantity", "UNCERTAIN"), cr("carton_count", "PASS"),
                  cr("carton_damage", "PASS"), cr("unit_damage", "PASS")], POLICY)
    assert out["decision"] == "UNCERTAIN" and out["disposition"] == "HOLD_FOR_REVIEW"

def test_pass_when_all_pass():
    out = decide([cr(k, "PASS") for k in KEYS], POLICY)
    assert out["decision"] == "PASS" and out["disposition"] == "ACCEPT"

def test_not_applicable_excluded():
    out = decide([cr("sku_identity", "PASS"), cr("colour", "NOT_APPLICABLE"),
                  cr("variant", "NOT_APPLICABLE"), cr("quantity", "PASS"),
                  cr("carton_count", "PASS"), cr("carton_damage", "PASS"),
                  cr("unit_damage", "PASS")], POLICY)
    assert out["decision"] == "PASS"

def test_missing_critical_check_raises():
    with pytest.raises(PolicyError):
        decide([cr("sku_identity", "PASS")], POLICY)