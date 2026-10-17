import hashlib
import json


def source_approval_fingerprint(
    source_id: str, title: str, source_uri: str, content_sha256: str
) -> str:
    payload = {
        "id": source_id,
        "title": title,
        "source_uri": source_uri,
        "content_sha256": content_sha256,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
