from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{2,3})\s+(.+?)\s*$")
TABLE_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|)+$")
SOURCE_ID_RE = re.compile(r"\bS\d{2}\b", re.IGNORECASE)
INTERNAL_ID_RE = re.compile(r"\b(?:B|H|C|T|F)\d{2}\b|\bZ(?:19|25)-\d{2}\b", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
BARE_URL_RE = re.compile(r"https?://[^\s)>]+")
ANCHOR_RE = re.compile(r"<a\s+id=[\"'][^\"']+[\"']\s*></a>", re.IGNORECASE)
CITATION_LINK_RE = re.compile(r"\[([^\]]*S\d{2}[^\]]*)\]\(#s\d{2}\)", re.IGNORECASE)
PENDING_TERMS = (
    "待核",
    "尚缺",
    "未取得",
    "未公开",
    "未展示",
    "不能据",
    "不确认",
    "不等于",
    "不意味着",
    "不应",
    "不宜",
    "仅作",
    "需查看原件",
)


@dataclass
class MarkdownTable:
    h2: str
    h3: str
    headers: list[str]
    rows: list[list[str]]
    start_line: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a sourced Nankai history Markdown collection into reviewable knowledge assets."
    )
    parser.add_argument("input", type=Path, help="Source Markdown file; it is never modified.")
    parser.add_argument("output_dir", type=Path, help="Directory for cleaned artifacts.")
    parser.add_argument("--cleaned-date", default="2026-10-12")
    return parser.parse_args()


def normalize_lines(text: str) -> list[str]:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized: list[str] = []
    blank_count = 0
    for line in lines:
        if line:
            blank_count = 0
            normalized.append(line)
            continue
        blank_count += 1
        if blank_count <= 2:
            normalized.append("")
    while normalized and not normalized[-1]:
        normalized.pop()
    return normalized


def parse_tables(lines: list[str]) -> list[MarkdownTable]:
    tables: list[MarkdownTable] = []
    h2 = ""
    h3 = ""
    index = 0
    while index < len(lines):
        heading_match = HEADING_RE.match(lines[index])
        if heading_match:
            if len(heading_match.group(1)) == 2:
                h2 = heading_match.group(2)
                h3 = ""
            else:
                h3 = heading_match.group(2)

        if (
            lines[index].startswith("|")
            and index + 1 < len(lines)
            and TABLE_SEPARATOR_RE.match(lines[index + 1])
        ):
            headers = split_table_row(lines[index])
            rows: list[list[str]] = []
            row_index = index + 2
            while row_index < len(lines) and lines[row_index].startswith("|"):
                row = split_table_row(lines[row_index])
                if len(row) < len(headers):
                    row.extend([""] * (len(headers) - len(row)))
                rows.append(row[: len(headers)])
                row_index += 1
            tables.append(
                MarkdownTable(
                    h2=h2,
                    h3=h3,
                    headers=headers,
                    rows=rows,
                    start_line=index + 1,
                )
            )
            index = row_index
            continue
        index += 1
    return tables


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def h2_number(title: str) -> str:
    match = re.match(r"^(\d+)\.", title)
    return match.group(1) if match else ""


def h3_number(title: str) -> str:
    match = re.match(r"^(\d+\.\d+)", title)
    return match.group(1) if match else ""


def split_h2_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    preamble: list[str] = []
    sections: dict[str, list[str]] = {}
    current = ""
    for line in lines:
        match = re.match(r"^##\s+(.+)$", line)
        if match:
            current = h2_number(match.group(1))
            sections[current] = [line]
        elif current:
            sections[current].append(line)
        else:
            preamble.append(line)
    return preamble, sections


def split_h3_section(section_lines: list[str], wanted: set[str]) -> list[str]:
    prefix: list[str] = []
    selected: list[str] = []
    current = ""
    seen_h3 = False
    for line in section_lines:
        match = re.match(r"^###\s+(.+)$", line)
        if match:
            seen_h3 = True
            current = h3_number(match.group(1))
        if not seen_h3:
            prefix.append(line)
        elif current in wanted:
            selected.append(line)
    return prefix + selected


def clean_markdown_citations(text: str) -> str:
    text = ANCHOR_RE.sub("", text)
    return CITATION_LINK_RE.sub(lambda match: f"[{match.group(1)}]", text)


def plain_text(value: str) -> str:
    value = ANCHOR_RE.sub("", value)
    value = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), value)
    value = CITATION_LINK_RE.sub(lambda match: match.group(1), value)
    value = value.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", value).strip(" ;；")


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def extract_source_ids(text: str) -> list[str]:
    return unique([match.upper() for match in SOURCE_ID_RE.findall(text)])


def extract_internal_ids(text: str) -> list[str]:
    return unique([match.upper() for match in INTERNAL_ID_RE.findall(text)])


def extract_urls(text: str) -> list[str]:
    markdown_urls = [match.group(2) for match in MARKDOWN_LINK_RE.finditer(text)]
    bare_urls = BARE_URL_RE.findall(text)
    return unique(markdown_urls + bare_urls)


def parse_source_index(tables: list[MarkdownTable]) -> list[dict[str, object]]:
    source_table = next(table for table in tables if h2_number(table.h2) == "12")
    sources: list[dict[str, object]] = []
    for row in source_table.rows:
        source_ids = extract_source_ids(row[0])
        if not source_ids:
            continue
        title_matches = list(MARKDOWN_LINK_RE.finditer(row[1]))
        title = plain_text(row[1])
        url = title_matches[0].group(2) if title_matches else ""
        if title_matches:
            title = plain_text(title_matches[0].group(1))
        sources.append(
            {
                "source_id": source_ids[0],
                "title": title,
                "url": url,
                "publisher": plain_text(row[2]),
                "published_or_version_date": plain_text(row[3]),
                "priority": plain_text(row[4]),
                "accessed_date": "2026-10-09",
            }
        )
    return sources


CANDIDATE_TABLES = {
    "5.2": "building_or_memorial",
    "6.2": "exhibition_category",
    "6.3": "archive_item",
    "6.4": "exhibition_item",
    "6.5": "image_or_document",
    "7.1": "online_panel_2025",
    "7.2": "online_panel_2019",
}


def find_cell(headers: list[str], row: list[str], terms: tuple[str, ...]) -> str:
    for header, cell in zip(headers, row):
        if any(term in header for term in terms):
            return plain_text(cell)
    return ""


def parse_candidates(tables: list[MarkdownTable]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for table in tables:
        section = h3_number(table.h3)
        record_type = CANDIDATE_TABLES.get(section)
        if record_type is None:
            continue
        for row in table.rows:
            candidate_ids = extract_internal_ids(row[0])
            if not candidate_ids:
                continue
            candidate_id = candidate_ids[0]
            row_text = " ".join(row)
            source_ids = extract_source_ids(row_text)
            internal_references = [
                value for value in extract_internal_ids(row_text) if value != candidate_id
            ]
            source_columns = {
                index
                for index, header in enumerate(table.headers)
                if "来源" in header or "出处" in header
            }
            description_parts = []
            for index, (header, cell) in enumerate(zip(table.headers, row)):
                if index in {0, 1} or index in source_columns or not plain_text(cell):
                    continue
                description_parts.append(f"{plain_text(header)}：{plain_text(cell)}")
            pending = [term for term in PENDING_TERMS if term in row_text]
            blockers = [
                "Confirm current display status, official collection/exhibit number, and venue location.",
                "Assign importance from 1 to 5 after curator review.",
                "Confirm text and image reuse permissions before visitor-facing publication.",
            ]
            if pending:
                blockers.append("Resolve the pending or limiting statements preserved from the source row.")
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "proposed_backend_id": "nk-" + candidate_id.lower(),
                    "record_type": record_type,
                    "title": plain_text(row[1]),
                    "period": find_cell(table.headers, row, ("时期", "年代", "时间", "背景")),
                    "people_or_themes": find_cell(table.headers, row, ("人物", "主题")),
                    "verified_description": "；".join(description_parts),
                    "source_ids": source_ids,
                    "source_urls": extract_urls(row_text),
                    "internal_references": internal_references,
                    "evidence_status": (
                        "public_source_verified_with_limitations" if pending else "public_source_verified"
                    ),
                    "pending_markers": pending,
                    "import_ready": False,
                    "blocking_reasons": blockers,
                    "original_section": f"{table.h2} / {table.h3}",
                    "original_line": table.start_line,
                }
            )
    return candidates


def resolve_candidate_sources(candidates: list[dict[str, object]]) -> None:
    source_map = {candidate["candidate_id"]: candidate["source_ids"] for candidate in candidates}
    for candidate in candidates:
        source_ids = list(candidate["source_ids"])
        for internal_id in candidate["internal_references"]:
            source_ids.extend(source_map.get(internal_id, []))
        candidate["source_ids"] = unique(source_ids)


def parse_knowledge_chunks(
    tables: list[MarkdownTable],
    candidate_source_map: dict[str, list[str]],
) -> list[dict[str, object]]:
    chunks: list[dict[str, object]] = []
    allowed_h2 = {"1", "2", "3", "4", "5", "6", "7", "9"}
    table_counter = 0
    for table in tables:
        if h2_number(table.h2) not in allowed_h2 or h3_number(table.h3) == "7.3":
            continue
        table_counter += 1
        for row_number, row in enumerate(table.rows, start=1):
            row_text = " ".join(row)
            source_ids = extract_source_ids(row_text)
            internal_ids = extract_internal_ids(row_text)
            for internal_id in internal_ids:
                source_ids.extend(candidate_source_map.get(internal_id, []))
            source_ids = unique(source_ids)
            candidate_ids = extract_internal_ids(row[0])
            base_id = candidate_ids[0].lower() if candidate_ids else f"t{table_counter:02d}-r{row_number:03d}"
            content_parts = [
                f"{plain_text(header)}：{plain_text(cell)}"
                for header, cell in zip(table.headers, row)
                if plain_text(cell)
            ]
            pending = [term for term in PENDING_TERMS if term in row_text]
            chunks.append(
                {
                    "chunk_id": f"nk-history-{base_id}",
                    "section": table.h2,
                    "subsection": table.h3,
                    "title": plain_text(row[1] if candidate_ids and len(row) > 1 else row[0]),
                    "content": "；".join(content_parts),
                    "source_ids": source_ids,
                    "source_urls": extract_urls(row_text),
                    "internal_references": internal_ids,
                    "evidence_status": (
                        "needs_source_review"
                        if not source_ids and not extract_urls(row_text)
                        else "public_source_verified_with_limitations"
                        if pending
                        else "public_source_verified"
                    ),
                    "eligible_for_rag": bool(source_ids or extract_urls(row_text)),
                    "pending_markers": pending,
                }
            )
    return chunks


def section_text(section_lines: list[str]) -> str:
    return clean_markdown_citations("\n".join(section_lines)).strip()


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_review_csv(path: Path, candidates: list[dict[str, object]]) -> None:
    fieldnames = [
        "candidate_id",
        "proposed_backend_id",
        "record_type",
        "title",
        "period",
        "people_or_themes",
        "verified_description",
        "source_ids",
        "evidence_status",
        "pending_markers",
        "official_collection_id",
        "current_location",
        "importance_1_to_5",
        "rights_status",
        "reviewer",
        "review_decision",
        "review_notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(
                {
                    "candidate_id": candidate["candidate_id"],
                    "proposed_backend_id": candidate["proposed_backend_id"],
                    "record_type": candidate["record_type"],
                    "title": candidate["title"],
                    "period": candidate["period"],
                    "people_or_themes": candidate["people_or_themes"],
                    "verified_description": candidate["verified_description"],
                    "source_ids": "；".join(candidate["source_ids"]),
                    "evidence_status": candidate["evidence_status"],
                    "pending_markers": "；".join(candidate["pending_markers"]),
                    "official_collection_id": "",
                    "current_location": "",
                    "importance_1_to_5": "",
                    "rights_status": "",
                    "reviewer": "",
                    "review_decision": "",
                    "review_notes": "",
                }
            )


def main() -> int:
    args = parse_args()
    source_text = args.input.read_text(encoding="utf-8-sig")
    source_sha256 = hashlib.sha256(args.input.read_bytes()).hexdigest()
    lines = normalize_lines(source_text)
    tables = parse_tables(lines)
    preamble, sections = split_h2_sections(lines)
    sources = parse_source_index(tables)
    candidates = parse_candidates(tables)
    resolve_candidate_sources(candidates)
    candidate_source_map = {
        candidate["candidate_id"]: list(candidate["source_ids"]) for candidate in candidates
    }
    chunks = parse_knowledge_chunks(tables, candidate_source_map)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    knowledge_parts = [
        "# 南开大学校史知识库清洗版",
        "",
        f"清洗日期：{args.cleaned_date}",
        "",
        "用途：供 NK HistoryGuide 知识库审核与后续 RAG 导入。原始措辞和来源号尽量保留。",
        "",
        "> 本文件不是馆方现行展品清册。项目生成编号不能冒充馆藏号；带有待核、尚缺、未公开等限制的内容必须保留限制语。来源详情见 `sources.cleaned.json`。",
        "",
    ]
    for section_number in ("0", "1", "2", "3", "4", "5", "6"):
        knowledge_parts.append(section_text(sections[section_number]))
        knowledge_parts.append("")
    knowledge_parts.append(section_text(split_h3_section(sections["7"], {"7.1", "7.2"})))
    knowledge_parts.append("")
    knowledge_parts.append(section_text(sections["9"]))
    knowledge_parts.append("")
    (output_dir / "knowledge_base.cleaned.md").write_text(
        "\n".join(knowledge_parts).strip() + "\n", encoding="utf-8"
    )

    route_text = "# 参观路线建议（非史实知识库）\n\n" + section_text(sections["8"]) + "\n"
    (output_dir / "route_suggestions.review_only.md").write_text(route_text, encoding="utf-8")

    pending_section = split_h3_section(sections["7"], {"7.3"})
    pending_text = (
        "# 待馆方补齐与继续核验清单\n\n"
        + section_text(pending_section)
        + "\n\n"
        + section_text(sections["11"])
        + "\n"
    )
    (output_dir / "pending_museum_materials.md").write_text(pending_text, encoding="utf-8")

    bibliography_text = "# 正式出版物与书目线索（复核用）\n\n" + section_text(sections["10"]) + "\n"
    (output_dir / "bibliography.review_only.md").write_text(
        bibliography_text, encoding="utf-8"
    )
    source_markdown = "# 公开来源索引\n\n" + section_text(sections["12"]) + "\n"
    (output_dir / "sources.cleaned.md").write_text(source_markdown, encoding="utf-8")

    write_json(output_dir / "sources.cleaned.json", sources)
    write_json(output_dir / "exhibit_candidates.cleaned.json", candidates)
    write_review_csv(output_dir / "exhibit_candidates.review.csv", candidates)
    with (output_dir / "knowledge_chunks.cleaned.jsonl").open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    source_id_set = {source["source_id"] for source in sources}
    candidate_missing_sources = [
        candidate["candidate_id"] for candidate in candidates if not candidate["source_ids"]
    ]
    unknown_source_ids = sorted(
        {
            source_id
            for chunk in chunks
            for source_id in chunk["source_ids"]
            if source_id not in source_id_set
        }
    )
    duplicate_candidate_ids = sorted(
        candidate_id
        for candidate_id, count in Counter(
            candidate["candidate_id"] for candidate in candidates
        ).items()
        if count > 1
    )
    eligible_chunk_count = sum(bool(chunk["eligible_for_rag"]) for chunk in chunks)
    limited_chunk_count = sum(
        chunk["evidence_status"] == "public_source_verified_with_limitations"
        for chunk in chunks
    )
    review_chunk_count = sum(
        chunk["evidence_status"] == "needs_source_review" for chunk in chunks
    )

    report = f"""# 南开校史资料清洗报告

清洗日期：{args.cleaned_date}

## 输入

- 原文件：`{args.input.name}`
- 原文件 SHA-256：`{source_sha256}`
- 原文件保持不变。
- 原文行数：{len(lines)}
- Markdown 表格数：{len(tables)}
- 表格数据行数：{sum(len(table.rows) for table in tables)}

## 输出统计

- 公开来源记录：{len(sources)}
- 展品／建筑／图版候选：{len(candidates)}
- 知识 chunks：{len(chunks)}
- 可进入下一轮 RAG 审核的 chunks：{eligible_chunk_count}
- 带限制语的 chunks：{limited_chunk_count}
- 仍缺直接来源的 chunks：{review_chunk_count}
- 缺少来源的候选编号：{', '.join(candidate_missing_sources) if candidate_missing_sources else '无'}
- 未在来源目录定义的来源号：{', '.join(unknown_source_ids) if unknown_source_ids else '无'}
- 重复候选编号：{', '.join(duplicate_candidate_ids) if duplicate_candidate_ids else '无'}

## 清洗规则

- 不改写原始史实，不补充原文没有的日期、人物关系、展柜位置或馆藏号。
- 知识库正文保留第0—7节中的已核材料和第9节的差异处理规则。
- 第7.3节移入待核清单；第8节路线建议与史实知识分离。
- 第10节书目只作为继续核验入口，不直接作为已读原文。
- 第11节馆方缺口单独保存，不进入面向游客的知识正文。
- 第12节拆成来源索引，知识 chunks 通过 source_ids 与其关联。
- 公开展板顺序编号、图片索引号和项目编号均不得冒充馆藏号。
- 所有候选条目统一为 `import_ready=false`，必须经过馆方或负责人复核后再转为正式 exhibit seed。

## 需要人工处理

- 确认2026年现场仍在展出的展品、展板和具体位置。
- 为正式展品分配稳定 ID、重要度1—5、关键词和主题。
- 获取展签原文、馆藏号、原件／复制件属性、版权和图片使用范围。
- 对 `needs_source_review` 和带限制语的 chunks 逐条复核。
- 正式导入前将通过审核的候选转换为后端 exhibit seed，并执行 dry-run、备份和审核。

## 输出文件

- `knowledge_base.cleaned.md`：知识库审核正文。
- `knowledge_chunks.cleaned.jsonl`：逐条 RAG 候选记录。
- `exhibit_candidates.cleaned.json`：展品及图版候选，默认不可导入。
- `exhibit_candidates.review.csv`：供工作人员填写馆藏号、位置、重要度、版权和审核结论。
- `sources.cleaned.json` / `sources.cleaned.md`：来源索引。
- `route_suggestions.review_only.md`：路线建议，与史实分离。
- `pending_museum_materials.md`：待馆方补齐和待核项目。
- `bibliography.review_only.md`：正式出版物和书目线索。
"""
    (output_dir / "cleaning_report.md").write_text(report, encoding="utf-8")

    manifest = {
        "dataset": "nankai_history_public_sources",
        "source_file": args.input.name,
        "source_sha256": source_sha256,
        "source_cutoff_date": "2026-10-09",
        "cleaned_date": args.cleaned_date,
        "status": "staff_review_required",
        "direct_database_import_allowed": False,
        "counts": {
            "sources": len(sources),
            "candidates": len(candidates),
            "knowledge_chunks": len(chunks),
            "rag_review_candidates": eligible_chunk_count,
        },
        "files": [
            "knowledge_base.cleaned.md",
            "knowledge_chunks.cleaned.jsonl",
            "exhibit_candidates.cleaned.json",
            "exhibit_candidates.review.csv",
            "sources.cleaned.json",
            "sources.cleaned.md",
            "route_suggestions.review_only.md",
            "pending_museum_materials.md",
            "bibliography.review_only.md",
            "cleaning_report.md",
        ],
    }
    write_json(output_dir / "manifest.json", manifest)

    print(json.dumps(manifest["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
