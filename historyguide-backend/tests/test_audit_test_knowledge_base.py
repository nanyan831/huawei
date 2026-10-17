from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_test_knowledge_base.py"
SPEC = importlib.util.spec_from_file_location("audit_test_knowledge_base", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_local_package_integrity() -> None:
    result = module.audit(module.DEFAULT_MANIFEST)
    assert result["local_package_valid"] is True
    assert result["recommended_file_count"] == 10
    assert result["platform_verified"] is False
    assert result["issues"] == []


def test_uploaded_list_detects_backup_duplicate() -> None:
    documents = json.loads(module.DEFAULT_MANIFEST.read_text(encoding="utf-8"))["documents"]
    names = [item["filename"] for item in documents]
    result = module.audit(module.DEFAULT_MANIFEST, names)
    assert result["observed_uploaded_count"] == 11
    assert result["platform_verified"] is False
    assert "uploaded not recommended file: 测试样例_完整知识库.md" in result["issues"]


def test_uploaded_list_matches_recommended_documents() -> None:
    documents = json.loads(module.DEFAULT_MANIFEST.read_text(encoding="utf-8"))["documents"]
    names = [item["filename"] for item in documents if item["upload_recommended"]]
    result = module.audit(module.DEFAULT_MANIFEST, names)
    assert result["platform_verified"] is True
    assert result["issues"] == []
