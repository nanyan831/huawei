# 南开校史资料清洗报告

清洗日期：2026-10-12

## 输入

- 原文件：`南开大学校史与展陈资料汇编_公开来源核验版_2026-10-09(1).md`
- 原文件 SHA-256：`4301fc25f08f898e1924aa0f95f0c20e8397dd38c5d20e76cb24ede63a2df063`
- 原文件保持不变。
- 原文行数：621
- Markdown 表格数：23
- 表格数据行数：391

## 输出统计

- 公开来源记录：75
- 展品／建筑／图版候选：105
- 知识 chunks：266
- 可进入下一轮 RAG 审核的 chunks：266
- 带限制语的 chunks：23
- 仍缺直接来源的 chunks：0
- 缺少来源的候选编号：无
- 未在来源目录定义的来源号：无
- 重复候选编号：无

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
