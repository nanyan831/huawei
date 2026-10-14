from __future__ import annotations

import hashlib
import json
import re
import shutil
import zipfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLEANED_DIR = ROOT / "data" / "cleaned" / "nankai_history_public_2026-10-09"
OUTPUT_DIR = ROOT / "data" / "knowledge_bases" / "测试样例"
ARCHIVE_PATH = ROOT.parent / "测试样例_知识库导入包_2026-10-12.zip"

KNOWLEDGE_SOURCE = CLEANED_DIR / "knowledge_base.cleaned.md"
SOURCES_SOURCE = CLEANED_DIR / "sources.cleaned.md"

SECTION_FILES = {
    "0": "00_使用说明与证据规则.md",
    "1": "01_发展沿革与关键年份.md",
    "2": "02_重要人物.md",
    "3": "03_重大事件与办学成果.md",
    "4": "04_校训校歌与公能文化.md",
    "5": "05_校址建筑与纪念设施.md",
    "6": "06_校史展馆藏照片与文献.md",
    "7": "07_官方网上展板索引.md",
    "9": "08_易混淆信息与回答边界.md",
}

NOTICE = """> **知识库状态：测试样例**
>
> 本文档仅用于 NK HistoryGuide 联调与检索测试，不是南开大学校史馆最终审定稿，不得作为正式展签、出版物或对外发布材料。回答时必须保留原文中的“待核”“未公开”“仅能确认”等限制语；项目生成编号不得表述为馆藏号。
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^## (\d+)\. .+$", text))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        section_id = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[section_id] = text[match.start():end].strip()
    return sections


def write_markdown(path: Path, title: str, body: str) -> None:
    path.write_text(f"# {title}\n\n{NOTICE}\n{body.strip()}\n", encoding="utf-8")


def build() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True)

    cleaned_text = KNOWLEDGE_SOURCE.read_text(encoding="utf-8")
    sections = split_sections(cleaned_text)
    missing = set(SECTION_FILES) - set(sections)
    if missing:
        raise RuntimeError(f"Missing cleaned sections: {sorted(missing)}")

    documents: list[dict[str, object]] = []
    for section_id, filename in SECTION_FILES.items():
        section = sections[section_id]
        heading = section.splitlines()[0].removeprefix("## ")
        output_path = OUTPUT_DIR / filename
        write_markdown(output_path, f"测试样例｜{heading}", section)
        documents.append(
            {
                "filename": filename,
                "section": section_id,
                "sha256": sha256(output_path),
                "upload_recommended": True,
            }
        )

    complete_filename = "测试样例_完整知识库.md"
    complete_path = OUTPUT_DIR / complete_filename
    cleaned_body = re.sub(r"\A# .+?\n\n", "", cleaned_text, count=1, flags=re.S)
    write_markdown(complete_path, "测试样例｜南开大学校史知识库", cleaned_body)
    documents.append(
        {
            "filename": complete_filename,
            "section": "complete",
            "sha256": sha256(complete_path),
            "upload_recommended": False,
            "note": "单文件导入备用；已导入分主题文档时不要重复导入。",
        }
    )

    sources_filename = "99_来源索引.md"
    sources_path = OUTPUT_DIR / sources_filename
    sources_text = SOURCES_SOURCE.read_text(encoding="utf-8")
    sources_body = re.sub(r"\A# .+?\n\n", "", sources_text, count=1, flags=re.S)
    write_markdown(sources_path, "测试样例｜公开来源索引", sources_body)
    documents.append(
        {
            "filename": sources_filename,
            "section": "sources",
            "sha256": sha256(sources_path),
            "upload_recommended": True,
        }
    )

    readme = OUTPUT_DIR / "导入说明.md"
    readme.write_text(
        """# 测试样例知识库导入说明

## 知识库名称

`测试样例`

## 建议导入文件

导入 `00_` 至 `08_` 的九份主题文档，以及 `99_来源索引.md`。

不要同时导入 `测试样例_完整知识库.md`，否则会造成内容重复。完整稿仅用于平台不支持多文件时的备用导入。

## 使用边界

- 仅供 NK HistoryGuide 联调和检索测试，不得对外发布。
- 资料来自公开来源核验稿，不等同于校史馆正式知识库。
- 带“待核”“未公开”“仅能确认”等限制的内容必须原样保留。
- 项目生成编号不是馆藏号，不得用于展签或资产登记。
- 本包不包含参观路线建议、馆方待补资料、书目审阅稿及未经审核的展品候选表。
""",
        encoding="utf-8",
    )

    manifest = {
        "knowledge_base_name": "测试样例",
        "purpose": "NK HistoryGuide 联调与检索测试",
        "status": "test_only",
        "official_museum_dataset": False,
        "publish_allowed": False,
        "source_cutoff_date": "2026-10-09",
        "package_date": date.today().isoformat(),
        "source_sha256": sha256(KNOWLEDGE_SOURCE),
        "recommended_import_mode": "topic_documents_plus_source_index",
        "excluded_content": [
            "route_suggestions.review_only.md",
            "pending_museum_materials.md",
            "bibliography.review_only.md",
            "exhibit_candidates.cleaned.json",
            "exhibit_candidates.review.csv",
            "knowledge_chunks.cleaned.jsonl",
        ],
        "documents": documents,
    }
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()
    with zipfile.ZipFile(ARCHIVE_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUTPUT_DIR.iterdir()):
            archive.write(path, arcname=f"测试样例/{path.name}")

    print(f"Knowledge base: {OUTPUT_DIR}")
    print(f"Archive: {ARCHIVE_PATH}")
    print(f"Files: {len(list(OUTPUT_DIR.iterdir()))}")


if __name__ == "__main__":
    build()
