import pytest
from app.decision.engine import PolicyError, decide, load_policy
from app.models import CheckResult

def cr(key, verdict):
    return CheckResult(check_key=key, verdict=verdict, confidence=0.8,
                       detail="d", model_version="m")

POLICY = load_policy()
KEYS = ["sku_identity", "colour", "variant", "quantity", "carton_count",
        "carton_damage", "unit_damage", "units_per_carton", "missing_components"]

def test_any_fail_wins():
    out = decide([cr(k, "FAIL" if k == "quantity" else "PASS") for k in KEYS], POLICY)
    assert out["decision"] == "FAIL" and out["disposition"] == "EXCEPTION"

def test_uncertain_when_no_fail():
    out = decide([cr(k, "UNCERTAIN" if k == "quantity" else "PASS") for k in KEYS], POLICY)
    assert out["decision"] == "UNCERTAIN" and out["disposition"] == "HOLD_FOR_REVIEW"

def test_pass_when_all_pass():
    out = decide([cr(k, "PASS") for k in KEYS], POLICY)
    assert out["decision"] == "PASS" and out["disposition"] == "ACCEPT"

def test_not_applicable_excluded():
    verdicts = {"colour": "NOT_APPLICABLE", "variant": "NOT_APPLICABLE",
                "missing_components": "NOT_APPLICABLE"}
    out = decide([cr(k, verdicts.get(k, "PASS")) for k in KEYS], POLICY)
    assert out["decision"] == "PASS"

def test_advisory_fail_does_not_block():
    # other_quality is advisory: FAIL there with everything else PASS -> still PASS
    out = decide([cr(k, "PASS") for k in KEYS] + [cr("other_quality", "FAIL")], POLICY)
    assert out["decision"] == "PASS"

def test_missing_critical_check_raises():
    with pytest.raises(PolicyError):
        decide([cr("sku_identity", "PASS")], POLICY)