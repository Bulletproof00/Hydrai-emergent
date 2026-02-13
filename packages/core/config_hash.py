import hashlib
import json


def compute_config_hash(snapshot: dict) -> str:
    clean = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()
