"""
Display labels and triage priority for decoded messages, driven by shared/codes.json.

Priority is a single integer, higher = more urgent, so the dashboard can sort on
one column. Bands keep medical-urgency flags above every resource request and
resource requests above check-ins (SRS 3.4); within a band, severity/urgency
orders items.
"""

import json
from pathlib import Path

BAND = {"MEDICAL_URGENT": 300, "RESOURCE_REQUEST": 200, "CHECKIN": 100, "ACK": 0}

# field name -> codes.json table used to label it
FIELD_TABLES = {
    ("CHECKIN", "status"): "checkin_status",
    ("RESOURCE_REQUEST", "resource_type"): "resource_type",
    ("RESOURCE_REQUEST", "urgency"): "urgency",
    ("MEDICAL_URGENT", "severity"): "severity",
    ("MEDICAL_URGENT", "condition_code"): "condition_code",
    ("ACK", "status"): "ack_status",
}


class Codes:
    def __init__(self, path: Path):
        self.tables = json.loads(Path(path).read_text(encoding="utf-8"))

    def label(self, table: str, code) -> str:
        entry = self.tables.get(table, {}).get(str(code))
        if entry is None:
            return f"Unknown ({code})"
        return entry["label"] if isinstance(entry, dict) else entry

    def type_key(self, msg_type: int) -> str:
        entry = self.tables["msg_type"].get(str(int(msg_type)))
        return entry["key"] if entry else f"TYPE_{int(msg_type)}"

    def labels_for(self, type_key: str, fields: dict) -> dict:
        return {
            name: self.label(table, fields[name])
            for (tkey, name), table in FIELD_TABLES.items()
            if tkey == type_key and name in fields
        }

    def priority(self, type_key: str, fields: dict) -> int:
        band = BAND.get(type_key, 0)
        if type_key == "MEDICAL_URGENT":
            return band + 10 * int(fields.get("severity", 0))
        if type_key == "RESOURCE_REQUEST":
            return band + 10 * int(fields.get("urgency", 0))
        if type_key == "CHECKIN":
            # A "not safe" check-in outranks a plain "safe" one.
            return band + 10 * int(fields.get("status", 0))
        return band

    def summary(self, type_key: str, fields: dict) -> str:
        labels = self.labels_for(type_key, fields)
        if type_key == "CHECKIN":
            n = fields.get("group_size", 1)
            return f"{labels.get('status', 'Check-in')} - group of {n}"
        if type_key == "RESOURCE_REQUEST":
            return f"{labels.get('resource_type', 'Resource')} x{fields.get('quantity', '?')} ({labels.get('urgency', '?')} urgency)"
        if type_key == "MEDICAL_URGENT":
            return f"{labels.get('severity', '?')}: {labels.get('condition_code', '?')}"
        if type_key == "ACK":
            return f"Ack for seq {fields.get('orig_seq')}: {labels.get('status', '?')}"
        return type_key
