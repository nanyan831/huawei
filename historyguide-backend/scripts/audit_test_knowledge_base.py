from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


DEFAULT_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge_bases"
    / "测试样例"
    / "manifest.json"
)


def audit(manifest_path: Path, uploaded_names: list[str] | None = None) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    documents = manifest["documents"]
    expected = {item["filename"] for item in documents if item["upload_recommended"]}
    known = {item["filename"] for item in documents}
    issues: list[str] = []

    if len(known) != len(documents):
        issues.append("manifest has duplicate filenames")
    for item in documents:
        path = manifest_path.parent / item["filename"]
        if not path.is_file():
            issues.append(f"missing local file: {item['filename']}")
            continue
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual_hash != item["sha256"]:
            issues.append(f"local hash mismatch: {item['filename']}")

    observed = None
    if uploaded_names is not None:
        names = [name.strip() for name in uploaded_names if name.strip()]
        observed = len(names)
        if len(names) != len(set(names)):
            issues.append("uploaded list has duplicate filenames")
        for name in sorted(set(names) - expected):
            kind = "not recommended" if name in known else "unknown"
            issues.append(f"uploaded {kind} file: {name}")
        for name in sorted(expected - set(names)):
            issues.append(f"recommended file absent from uploaded list: {name}")

    return {
        "local_package_valid": not any(
            issue.startswith(("manifest", "missing local", "local hash")) for issue in issues
        ),
        "recommended_file_count": len(expected),
        "observed_uploaded_count": observed,
        "platform_verified": uploaded_names is not None and not issues,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit test KB files without changing Coze")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--uploaded-list",
        type=Path,
        help="UTF-8 text file with one actual Coze document filename per line",
    )
    args = parser.parse_args()
    uploaded = (
        args.uploaded_list.read_text(encoding="utf-8").splitlines()
        if args.uploaded_list is not None
        else None
    )
    result = audit(args.manifest, uploaded)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result["issues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
