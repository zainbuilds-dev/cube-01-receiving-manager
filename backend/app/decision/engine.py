import json
from pathlib import Path

from ..models import CheckResult, utcnow

class PolicyError(Exception):
    pass

POLICY_PATH = Path(__file__).parent / "policy.json"

def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))

def decide(results: list, policy: dict) -> dict:
    """Pure function: checks + policy -> outcome. No AI anywhere in here."""
    verdicts = {r.check_key: r.verdict for r in results}
    critical = policy["critical_checks"]
    missing = [k for k in critical if k not in verdicts]
    if missing:
        raise PolicyError(f"Missing results for critical checks: {missing}")

    base = {
        "decided_by": f"decision-engine/policy-{policy['policy_version']}",
        "decided_at": utcnow(),
        "policy_version": policy["policy_version"],
    }
    fails = [k for k in critical if verdicts[k] == "FAIL"]
    if fails:
        return {**base, "decision": "FAIL", "disposition": "EXCEPTION",
                "reason": f"Critical checks failed: {', '.join(fails)}"}
    unsure = [k for k in critical if verdicts[k] == "UNCERTAIN"]
    if unsure:
        return {**base, "decision": "UNCERTAIN", "disposition": "HOLD_FOR_REVIEW",
                "reason": f"Critical checks unresolved: {', '.join(unsure)}"}
    return {**base, "decision": "PASS", "disposition": "ACCEPT",
            "reason": "All critical checks passed"}