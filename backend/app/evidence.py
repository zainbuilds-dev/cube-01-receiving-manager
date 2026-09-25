import hashlib
import json
from typing import Optional

from .config import CFG
from .models import POCreate, CheckResult, utcnow

def build_evidence_record(record_id: str, po: POCreate, images: list,
                          checks: list, outcome: dict,
                          captured_at: Optional[str] = None) -> dict:
    rec = {
        "record_id": record_id,
        "schema_version": CFG.schema_version,
        "organization_id": CFG.org_id,
        "client_id": CFG.client_id,
        "agent": {"name": "receiving-manager", "version": CFG.agent_version},
        "subject": {
            "po_number": po.po_number,
            "supplier": po.supplier,
            "line_items": [li.model_dump() for li in po.line_items],
        },
        "captured_at": captured_at or utcnow(),
        "operator_label": None,
        "images": images,
        "checks": [c.model_dump() for c in checks],
        "outcome": outcome,
        "overrides": [],
        "status": "ACTIVE",
    }
    rec["content_hash"] = hashlib.sha256(
        json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return rec