import hashlib
import json
from typing import List, Optional

from .config import CFG
from .models import POCreate, CheckResult, utcnow

def build_evidence_record(record_id: str, org: str, po: POCreate, images: list,
                          checks: List[CheckResult], outcome: dict, summary: dict,
                          captured_at: Optional[str] = None,
                          inspection_status: str = "INSPECTED") -> dict:
    rec = {
        "record_id": record_id,
        "schema_version": CFG.schema_version,
        "organization_id": org,
        "client_id": "client_demo",
        "agent": {"name": "receiving-manager", "version": CFG.agent_version},
        "subject": {
            "unit_id": po.unit_id,
            "po_number": po.po_number,
            "po_line": po.po_line,
            "supplier": po.supplier,
            "operator_id": po.operator_id,
            "line_items": [li.model_dump() for li in po.line_items],
        },
        "captured_at": captured_at or utcnow(),
        "operator_label": None,
        "images": images,
        "checks": [c.model_dump() for c in checks],
        "receiving_summary": summary,
        "outcome": outcome,
        "inspection_status": inspection_status,
        "overrides": [],
        "status": "ACTIVE",
    }
    rec["content_hash"] = hashlib.sha256(
        json.dumps(rec, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return rec