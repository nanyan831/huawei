# NK HistoryGuide 研判 Agent 上下文记录

用途：持续记录 NK-GeniOS 可信讲解研判层的创建、配置与验证状态。每次继续前先阅读本文件；每完成一个 step，立即追加结果、验证证据和下一步。

## 固定边界

- 主讲解 Agent 负责理解用户问题、调用 HistoryGuide handoff、检索知识库并生成回答草稿。
- 当前保持 NK-GeniOS 单 Agent 模式，研判能力由公网后端的确定性工具提供，不另建第二个对话 Agent。
- 研判工具负责检查来源安全、路线一致性、展品 ID、开发 fixture 数据和回答可发布性。
- 研判工具不自行创造历史事实，不替代知识库，不绕过后端 source-safety。
- 稳定流程应为串行：主讲解生成草稿 -> 调用研判工具 -> pass/revise/block -> 最终回答。
- `ready_for_generation=false`、`grounding_sources_complete=false`、`missing_exhibit_ids` 非空或 `unsourced_exhibit_ids` 非空时必须阻止无依据讲解。
- 当前服务器中的 `fixture-exhibit-001/002` 是非历史事实开发数据，不可用于真实校史讲解。
- 未经用户明确确认，不发布主 Agent、研判 Agent 或相关工作流。

## 目标输出协议

```json
{
  "decision": "pass | revise | block",
  "issues": [],
  "safe_answer": "审核通过或安全降级后的回答"
}
```

## Step 1：建立独立上下文记录

日期：2026-10-07

状态：已完成

结果：

- 已创建本文件，作为研判 Agent 专用的持续上下文记录。
- 已确定双 Agent 采用串行审核，而不是两个平级 Agent 自由对话。
- 已确认 NK-GeniOS 登录页可由内置浏览器访问。
- 当前主讲解 Agent 的 Flat Handoff 工具自然语言联调已通过。

下一步：

- 已被 Step 2 的架构决定替代：不创建第二个对话 Agent，改为单 Agent 调用后端研判工具。

## Step 2：实现后端确定性研判 API

日期：2026-10-09

状态：已完成

架构决定：

- NK-GeniOS 继续使用单 Agent 模式。
- 新增公网后端工具 `POST /api/genios/review`，作为独立研判层。
- 研判过程不调用大模型，只复用 handoff、preflight、source-safety 和 route plan 做确定性检查。
- 工具输入输出采用平台友好的扁平字段，避免嵌套对象导致 NK-GeniOS 插件解析失败。

实现结果：

- 新增 `GeniosReviewRequest` 和 `GeniosReviewResponse`。
- 输入字段包括 `session_id`、`draft_answer`、逗号分隔的 `cited_exhibit_ids`、推荐数量和路线数量。
- 输出字段包括 `decision`、`issues`、`safe_answer`、来源安全、路线顺序、展品 ID、来源引用和 fixture 检查结果。
- 判定优先级为 `block > revise > pass`。
- `ready_for_generation=false`、来源不完整、缺失/无来源展品或开发 fixture 数据会返回 `block`。
- 展品 ID 不合法、引用为空或路线顺序错误会返回 `revise`。
- 所有检查通过时返回 `pass`，并原样返回去除首尾空白后的草稿。
- capability 清单已加入 `/api/genios/review`。

验证证据：

- `python -m compileall -q app`：通过。
- `pytest tests/test_genios_context.py tests/test_openapi_contract.py`：`22 passed`。
- 已覆盖 pass、路线顺序 revise、fixture block 和缺失 session 404。

下一步：

- 为研判接口生成独立的最小 OpenAPI 导入文件。
- 增加 OpenAPI 契约测试，再运行完整测试集。

## Step 3：生成研判工具 OpenAPI 契约

日期：2026-10-09

状态：已完成

实现结果：

- 新增公开契约地址 `/openapi-genios-review.json`。
- 新增 NK-GeniOS 本地上传文件 `historyguide-backend/coze_genios_review_openapi_plugin_auth.json`。
- 契约只暴露 `POST /api/genios/review` 一个工具。
- 认证沿用插件级 `X-HistoryGuide-Api-Key`。
- 请求体和响应体均避免数组/嵌套响应字段；`issues`、`checked_exhibit_ids` 使用字符串。
- `/openapi-genios-review.json` 已加入公开路径白名单，读取契约本身不需要 API Key。

验证证据：

- OpenAPI 上传文件通过 `python -m json.tool` 校验。
- `python -m compileall -q app`：通过。
- 完整 `pytest`：`166 passed`，仅有 2 条第三方库弃用警告。

下一步：

- 制作服务器增量部署包并更新公网后端。
- 公网验证健康检查、OpenAPI 契约、401 鉴权和带 Key 的研判调用。
- 验证完成后，才在 NK-GeniOS 创建并 Debug 新工具；未经用户确认不发布 Agent。

## Step 4：部署并验证公网研判 API

日期：2026-10-09

状态：已完成

部署结果：

- 已生成增量包 `historyguide-review-update.zip`，仅包含 5 个后端代码文件，不包含数据库、环境变量或密钥。
- 已通过免密 SSH 上传并部署到 `/opt/nk-historyguide`。
- 部署前备份：`/opt/nk-historyguide/backups/review-update-20261009-145132.tar.gz`。
- `nk-historyguide.service` 已重启并保持 `active`。
- 重启后 nginx 曾在 uvicorn 启动窗口内短暂返回 502；约 2 秒后本机及公网健康检查均恢复 200，无需回滚。
- 发现运行环境中的 API Key 与 `.historyguide_api_key` 不一致；已将 `historyguide.env` 同步为现有插件使用的 Key，并重启验证。未输出密钥值。

公网验证证据：

- `GET https://historyguide.catlifepet.top/health`：200。
- `GET https://historyguide.catlifepet.top/openapi-genios-review.json`：可读，operationId 为 `review_genios_answer`。
- 无 Key 调用 `POST /api/genios/review`：401。
- 带现有插件 Key 调用：200。
- `demo-session-001` 研判结果：`decision=block`、`fixture_data_detected=true`、展品 ID 和来源检查通过，阻断原因是开发 fixture 数据不可用于真实校史讲解。

安全提醒：

- 当前 Key 曾在对话中暴露，只用于继续联调；正式发布前必须轮换，并同步更新所有插件鉴权。

下一步：

- 在 NK-GeniOS 新建研判插件并导入 `coze_genios_review_openapi_plugin_auth.json`。
- 配置插件级 Header Key，完成 Debug。
- 将通过 Debug 的研判工具加入当前单 Agent，并更新提示词为 handoff -> 草稿 -> review -> 最终输出的串行流程。
- 不发布 Agent，除非用户明确确认。

## Step 5：NK-GeniOS 页面接入尝试

日期：2026-10-09

状态：待继续

门禁：必须先在 NK-GeniOS 工具详情页看到 `Debug 通过`，才能进入 Agent 挂载和提示词修改；后端验证通过不能替代平台 Debug 通过。

当前进展：

- 内置浏览器能够枚举到已登录的 NK-GeniOS Agent 编辑页。
- 浏览器控制接口在绑定现有标签页以及创建同站点控制标签页时连续超时并自动重置。
- 2026-10-09 再次枚举到已登录编辑页，但读取该标签页仍超时；因此本步仍按未验证处理。
- 未盲点页面，未创建重复插件，未上传文件，未修改 Agent，未发布任何内容。

继续位置：

- 上传文件：`historyguide-backend/coze_genios_review_openapi_plugin_auth.json`。
- 插件名称建议：`NK HistoryGuide Answer Review`。
- 插件级 API Key Header：`X-HistoryGuide-Api-Key`，使用服务器 `/opt/nk-historyguide/.historyguide_api_key` 当前值；不要在聊天中再次粘贴。
- Debug 参数：`session_id=demo-session-001`、`draft_answer=先参观展品二。`、`cited_exhibit_ids=fixture-exhibit-002`、`recommendation_limit=3`、`route_max_items=5`。
- 预期 Debug 成功且业务结果为 `decision=block`、`fixture_data_detected=true`。这是正确结果，表示研判层拦截了开发 fixture。

## Step 6：测试知识库接入与问答边界验证

日期：2026-10-13

状态：知识库联调通过；研判插件接入仍待验证

验证证据（用户提供的平台截图与运行记录）：

- 平台中的“测试知识库”显示 11 份文档；本次导入的 10 份 Markdown 均显示“解析成功”且已启用。用户确认没有旧资料引入，但第 11 份文档的具体内容未在截图中核实。
- 命中测试“南开大学何时建立”返回 3 个分段，来源为 `01_发展沿革与关键年份.md`。
- Agent 回答正确区分 1919 年创办、9 月 25 日开学典礼、10 月 17 日校庆日和 11 月 22 日成立纪念大会，并给出 `[S01][S02][S31，第89条]`。用户提供的运行记录提到检索上下文 `context3`，可确认本次回答使用了知识库内容。
- 边界测试询问张伯苓手札原件的馆藏编号与所在展柜号；Agent 明确回答当前资料不足、无法确认，未编造编号或位置。

限制与下一步：

- 当前知识库为测试资料，不是校史馆审定稿；不得据此正式发布历史讲解服务。
- 研判插件在 NK-GeniOS 的创建、Debug 与 Agent 挂载状态仍无验证证据。按 Step 5 门禁，先验证研判工具 Debug 通过，再修改 Agent 串行流程。
- 正式发布前轮换曾在对话中暴露的 API Key，并同步更新插件鉴权。

## Step 7：NK-GeniOS 研判工具 Debug 验证

日期：2026-10-14

状态：已完成；Agent 挂载与串行调用仍待验证

平台验证证据（用户提供的 Debug Request/Response）：

- 已创建 `NK HistoryGuide Answer Review` 插件并导入 `review_genios_answer` 工具。
- 首次 Debug 返回 401，提示缺少有效的 HistoryGuide API Key；用户更新插件 Header 后再次 Debug 通过。
- 请求：`session_id=demo-session-001`、`draft_answer=先参观展品二。`、`cited_exhibit_ids=fixture-exhibit-002`、`recommendation_limit=3`、`route_max_items=5`。
- 响应：`decision=block`、`fixture_data_detected=true`、`ready_for_generation=true`、`grounding_sources_complete=true`、`route_order_valid=true`、`exhibit_ids_valid=true`、`source_references_valid=true`。
- `issues` 明确指出开发 fixture 数据不可用于真实讲解；`safe_answer` 为拒绝提供不可靠讲解的安全降级文本。平台调试成功且业务阻断符合预期。

下一步：

- 在当前单 Agent 的插件列表中挂载研判工具，但先不发布。
- 更新并验证串行流程：获取 handoff、结合知识库生成草稿、调用研判工具、按 `pass/revise/block` 决定最终回答。不得把 Debug 通过等同于 Agent 自动调用成功。
- 发布前仍须轮换已暴露的 API Key，并同步更新所有相关插件。

## Step 8：研判工具挂载到讲解 Agent

日期：2026-10-14

状态：用户报告已挂载；Agent 实际调用尚未验证

进展与约束：

- NK-GeniOS 平台要求先发布插件，才能将工具添加到 Agent。用户已按平台流程完成研判工具添加；这不等同于发布讲解 Agent。
- 后端 `review_genios_answer` 要求至少一个 `cited_exhibit_ids`，且 ID 必须来自 handoff 中的 grounding 展品。纯知识库史实问答没有展品 ID 时，不应强行调用该工具；需继续按知识库证据规则回答。
- Review 是确定性结构检查（来源完整性、展品 ID、路线顺序、fixture），不验证复杂历史叙述的语义真伪；历史事实仍须以知识库证据为准。
- 对涉及具体展品或路线的草稿，必须在最终回答前调用 Review；`block` 时使用 `safe_answer` 降级，不得展示未核验草稿；`revise` 时根据 `issues` 修订并重试，不能把修订请求当作通过。

下一步：

- 核对 Agent 当前提示词中的 HistoryGuide 工具调用规则，再加入最小范围的 Review 调用与结果处理规则。
- 在 Agent 预览中分别测试纯史实问答（不强制 Review）和带展品 ID 的参观推荐（必须调用 Review，开发 fixture 应被阻断）。
- 继续保持讲解 Agent 未发布，并在正式发布前轮换已暴露的 Key。

## Step 9：单 Agent 端到端阻断路径联调

日期：2026-10-14

状态：阻断路径已完成；通过与修订路径仍待验证

用户确认的联调结果：

- 之前 Agent 预览中 Handoff 曾返回 401；随后用户报告已完成工具调用检查，确认本轮 Handoff 调用成功，Review 返回预期的 `decision=block` 与 `fixture_data_detected=true`。本记录依据用户确认，未保存含密钥的调用截图。
- Agent 最终回答正确给出南开大学 1919 年创办、9 月 25 日开学典礼、10 月 17 日校庆日以及 `[S01][S02][S31，第89条]` 来源。
- 对展品与参观顺序，Agent 给出“当前参观上下文或资料来源未通过安全检查，暂时无法提供可靠建议”，未泄露开发 fixture 展品或路线。

尚未完成：

- 未验证非 fixture、经审定展品上的 `pass` 分支，也未验证路线顺序错误触发的 `revise` 分支。
- 测试知识库尚非校史馆审定稿；不能以此作为真实馆内展品讲解发布依据。
- 已暴露的 API Key 尚待轮换并同步更新 Handoff、Review 两个插件；讲解 Agent 保持未发布。

下一步：先取得至少一条有来源、经馆方核验且具稳定展品 ID 的真实展品数据，再建立对应访客会话，测试 `pass` 和 `revise`。在此之前不要将 fixture 测试结果误当成正式讲解可发布的证明。

## Step 10：Agent 架构调研与本地审核闭环

日期：2026-10-14

状态：本地后端实现并通过测试；线上平台未接线、未部署

- 调研 ReAct、Magentic-One、AFlow、Tau-bench、AgentDojo、ALCE 后，确定当前项目继续采用单讲解 Agent 加确定性后端研判。此研判层不是第二个 LLM Agent，不能声称已做语义事实核验。
- 新增证据源、展品关联与人工审批记录；未审批、撤销、变更或 fixture 数据在 Review 阶段阻断。新增数据库迁移 `0003_evidence_governance`。
- 新增 15 分钟时限的审核 run：prepare 保存参观及证据快照、review 记录草稿哈希与结论、finalize 只返回相同草稿或安全阻断文本。参观状态或证据变更、过期、重放均拒绝。新增迁移 `0004_review_runs`。
- 增加审核流程与迁移测试，并将临时密钥文件列入 `.gitignore`。架构和上线门禁详见 `historyguide-backend/docs/agent_architecture_2026.md`。
- 本地测试通过不等于 Coze 必经审核：既有插件仍是旧接口；只有平台最终输出经工作流或网关强制走 finalize，才构成实际强制门禁。馆方审定证据、语义级引用核验、完整评测、密钥轮换与服务器部署仍未完成。
- 新增操作员审核统计接口 `GET /api/evidence/review-run-stats`，只汇总状态、结论和超时数，不返回草稿。全量本地测试为 179 passed，迁移预演和只读 staging 校验测试通过。此为本地验证结果，不代表线上部署完成。

## Step 11：证据摘录绑定与离线流程验收

日期：2026-10-14

状态：本地实现并测试；线上 Coze 与服务器仍未接入

- 修复证据正文被改而存储哈希未变时审批仍有效的问题；审核时重算正文哈希，发现不一致即阻断。
- 新 run 的 prepare 返回已审批来源的 ID、标题、URI、哈希和最多 8,000 字符摘录；review 要求每个引用展品提供已关联来源的原文摘录。空白、伪造和未关联来源会要求修订。此为引用存在性与来源绑定检查，不是历史语义真伪判断。
- finalize 改为审核草稿的原文哈希精确匹配；审计日志只记展品/来源 ID 与摘录哈希，不存草稿或摘录正文。
- 新增 `GET /openapi-genios-runs.json` 的三工具插件契约，未导入 Coze；旧插件保持不变。
- 新增 `scripts/evaluate_agent_traces.py`，对脱敏轨迹检查 prepare、review、finalize、最终输出的顺序及一致性。它只能验证轨迹结构，不能代替真实平台日志或馆方事实评测。
- 仍需馆方审定资料、Coze 强制出口接线、真实运行轨迹、密钥轮换及 staging 部署验收。详细操作边界见 `historyguide-backend/docs/agent_architecture_2026.md`。
- 新增 `historyguide-backend/docs/coze_agent_run_workflow.md`，提供 staging 插件接线、Agent 调用规则与验收题单。文档不是平台变更记录，不能以此认定 Coze 已接入新接口。

## Step 12：业务 Key 轮换准备

日期：2026-10-14

状态：本地支持与测试完成；线上旧 Key 未轮换

- 增加临时 `HISTORYGUIDE_API_KEY_NEXT` 配置，短时间内可接受旧、新两个业务 Key，以便逐个迁移 Coze 插件；最终撤销旧 Key 后只保留新 Key。
- 鉴权比较改用常数时间函数；安全状态仅报告是否处于轮换窗口，不返回任何密钥值。运行配置校验拒绝相同的新旧 Key 或复用操作员 Key。
- 本地测试覆盖双 Key 接受和切换后旧 Key 返回 401。操作步骤与服务端版本差异提示见 `historyguide-backend/docs/business_key_rotation.md`。
- 尚未访问服务器或 Coze 插件密钥配置，因此不能声称已完成真实轮换。原先对话中暴露的 Key 在现网是否仍有效，必须以实际服务器鉴权验证为准。

## Step 13：Handoff 提前阻断未审批展品

日期：2026-10-14

状态：本地实现并通过测试；线上旧插件仍未切换

- 修复旧 Handoff 仅凭非空来源字符串可能给出 `ready_for_generation=true` 的问题。现在 grounding 展品缺少当前馆方审批时，结构化与扁平 Handoff 均返回 `ready_for_generation=false`，`blocking_check_names` 含 `museum_approval`。
- 新增结构完整但未审批展品的专门回归测试；本地全量测试为 192 项通过。旧线上截图的 fixture 状态与本地新版本不可直接比较。
- 只读检查显示 Codex 内置浏览器仍在南开统一身份认证页，无法核实当前 Coze 插件/工作流配置。已请求用户自行登录；未输入或获取账号密码。
- 纯校史问答没有展品 ID，仍缺独立的审定来源审核路径与强制最终出口；不能伪造展品 ID 来走展品 run。馆方审定材料、真实平台轨迹、密钥轮换、服务器迁移和上线验收均未完成。

## Step 14：纯校史问答的独立来源引用流程

日期：2026-10-14

状态：本地实现并测试；审定来源、平台接线与实际事实评测待完成

- 新增 `history_review_runs` 表及迁移 `0005_history_review_runs`。纯校史问题不再需要虚构访客或展品 ID；prepare 绑定问题哈希与已审批来源 ID，review 核对原文摘录及正文 `[来源ID]`，finalize 仅放行同一草稿。
- 撤销、篡改、缺失、fixture 来源及过期 run 会拒绝处理。审核日志不保存问题、草稿或摘录正文。
- 响应显式包含 `semantic_verified=false`，强调这是引用结构检查，不是语义事实证明。尚无馆方审定来源内容映射到后端，Coze 的测试知识库不能直接当作批准来源。
- 新增独立 `/openapi-genios-history-runs.json` 插件契约；Coze 尚未导入。全量本地测试为 198 项通过，包括迁移预演。
- 原 Step 13 所述“纯校史问答缺独立路径”在**本地代码层面**已缓解，但强制平台出口、馆方审定来源和历史事实评测仍未完成。

## Step 15：馆方标注评测门禁模板

日期：2026-10-14

状态：本地模板与评分脚本完成；真实 Coze 轨迹和馆方评分尚无

- 增加 `historyguide-backend/evals/curator_cases.json`，列出创办日期与来源、未知馆藏号拒答、fixture 阻断、真实展品通过、反向路线修订、来源撤销、检索提示注入与工具故障 8 类上线必测场景。
- 增加 `scripts/score_curator_evaluation.py`：逐案例要求评审人、脱敏轨迹索引及相关评分均明确为 true；缺任何案例或任一必需评分均失败。脚本不验证评审人身份或证据真实性。
- 该模板**没有**实际馆方评分，不能作为项目已通过事实评测的证据。需等审定来源、Coze 工作流接线和真实轨迹后再执行。

## Step 16：两类审核运行量统一观测

日期：2026-10-14

状态：本地实现并测试；线上未部署

- 操作员接口 `GET /api/evidence/review-run-stats` 现分别汇总展品/路线 run 与纯校史 run 的总量、准备、已审、完成、超时、通过和退回数。响应仍不包含问题、草稿或摘录正文。
- 本地测试覆盖纯校史完成后的统计值，以及既有展品 run 统计接口权限与隐私边界。
- 真实监控看板、告警阈值与 Coze 日志关联仍需在 staging 上验证；本地计数不代表线上运行量。
- 本轮全量本地测试 201 项通过；独立迁移预演实际执行到 `0005_history_review_runs`，确认 10 张表并删除临时数据库，未修改配置中的应用数据库。

## Step 17：审核与放行状态的竞争保护

日期：2026-10-14

状态：本地实现并通过测试；线上未部署

- 展品/路线 run 与纯校史 run 的 review、finalize 均改为带状态条件的数据库更新。已放行 run 不会被迟到的 review 写回重新打开；finalize 只允许一次 `reviewed -> finalized` 状态转换。更新失败时回滚并要求重新准备 run。
- 增加两类 run 的陈旧会话回归用例，覆盖重复放行和迟到审核；本地全量测试 205 项通过。
- 该保护只涉及本地数据库 run 状态，不提供 Coze 消息发送的跨系统原子性，也不证明历史陈述语义正确。馆方审定来源、真实平台轨迹、强制出口、密钥轮换、staging/线上验收仍待完成。

## Step 18：密钥文件配置兼容

日期：2026-10-14

状态：本地实现并通过测试；未读取或改动服务器真实密钥

- `Settings.from_env()` 支持 `HISTORYGUIDE_API_KEY_FILE`、`HISTORYGUIDE_API_KEY_NEXT_FILE` 和 `HISTORYGUIDE_OPERATOR_API_KEY_FILE`，与直接环境变量二选一。要求绝对路径、单行非空 UTF-8 内容，缺失、不可读、超大或多行时启动失败。
- 更新 README 与轮换手册，避免把服务器截图中的 `_FILE` 配置误当成本地版本已支持或已部署的证明。真实运行版本、secret 来源、权限和旧 Key 撤销仍须在 staging/服务器核验。
- 增加配置异常用例；本地全量测试通过（207 项，第三方依赖有 2 条弃用警告）。没有在此轮读取或输出已暴露的旧密钥值。

## Step 19：馆方证据草稿批量导入与核对

日期：2026-10-14

状态：本地 API 和定向测试通过；网页界面、Coze 同步与真实馆方审批未完成

- 清洗包清单标记 `staff_review_required`、`direct_database_import_allowed=false`；`sources.cleaned.json` 只有来源元数据，没有可作为已审批原文的正文。因此没有把 75 条来源或 266 条知识片段自动导入、批准。
- 新增操作员专用 `POST /api/evidence/sources/batch`：每批最多 20 条，重复 ID 整批拒绝，落库状态固定为 `draft`；`GET /api/evidence/sources` 提供分页/状态筛选但不返回正文，`GET /api/evidence/sources/{source_id}` 返回详情供人工核对。
- 定向测试验证鉴权、批量原子性、草稿不能进入校史回答，以及详情可供审核。流程和示例见 `historyguide-backend/docs/evidence_intake.md`。
- 本轮全量本地测试 210 项通过；操作员接口仍由 `/api/evidence` 前缀统一保护。
- 仍需馆方提供并核准原始摘录、建立 Coze 引用 ID 与后端 ID 的映射；当前并无工作人员网页导入界面或线上部署。

## Step 20：指定知识库引用 ID 的只读发布门禁

日期：2026-10-14

状态：本地脚本与定向测试通过；尚无真实 Coze 轨迹或 staging 数据库验收

- `scripts/validate_staging_database.py` 新增可重复的 `--require-source-id` 参数。逐 ID 只读查询 `evidence_sources`，核验存在、`approved`、非 fixture、复核记录、来源元数据及正文 SHA-256 一致性；报告不打印正文。
- 测试覆盖已审批通过、草稿/缺失拒绝、正文篡改拒绝、重复和不安全 ID 参数拒绝。
- 使用方式已加入 `historyguide-backend/docs/evidence_intake.md`。它不验证 Coze 实际检索片段与后端资料一致，更不能代替馆方语义事实审查。
- 本轮全量本地测试 212 项通过。对工作区 `historyguide.db` 的只读试跑以退出码 1 失败：S01/S02 均不存在，`alembic_version` 表缺失。该库不是已验收 staging；未对其执行迁移、导入或清理。

## Step 21：无 Alembic 记录旧库的副本接管预演

日期：2026-10-14

状态：本地预演通过；服务器数据库未检查、未修改

- 新增 `scripts/rehearse_legacy_adoption.py`。对指定 SQLite 文件只读备份，在临时副本上比对每个 Alembic 修订的结构签名，检查完整性、识别唯一匹配版本，然后只对副本执行 stamp/upgrade；升级后核对旧表逐行摘要及最终结构。
- 工作区 `historyguide.db` 的副本匹配 `0005_history_review_runs`，预演保留 9 张原表、42 行数据。原库没有 `alembic_version`，脚本没有对原库 stamp 或迁移；它仍不能作为 staging 或馆方数据验收证据。
- 测试覆盖 HEAD 等价旧库、较早版本升级、结构漂移拒绝、外键损坏拒绝和源文件字节不变。迁移边界见 `historyguide-backend/docs/database_migrations.md`。
- 现网库版本及 schema 未核实；上线前仍需识别真实数据库、可恢复备份、staging 副本预演与人工 cutover。没有自动处理现网。
- 本轮全量本地测试 216 项通过；仅有两条第三方测试客户端弃用警告。

## Step 22：共享环境启动拒绝隐式建表

日期：2026-10-14

状态：本地实现与定向测试通过；现网启动参数未改变

- 新增 `HISTORYGUIDE_SCHEMA_MODE`。本地演示默认 `auto_create`；设置 `migrated` 后，服务启动只读核验 `alembic_version` 当前 head 与 SQLAlchemy 模型结构差异，不执行 `create_all`。无版本表或结构漂移会拒绝启动。
- staging/production 的运行配置校验要求 `migrated`；`/api/system/database` 在该模式下报告 `alembic_migrated_verified`。测试覆盖正确迁移库、无版本旧库、缺表漂移和本地兼容模式。
- 文档已说明切换次序；没有在真实服务器设置该参数，也没有对其数据库做 stamp/upgrade。现网数据库仍需备份与 staging 验收。
- 本轮全量本地测试 221 项通过；两条弃用警告来自第三方测试客户端。

## Step 23：现网只读盘点与版本差异

日期：2026-10-14

状态：只读核实；现网未部署、未备份、未迁移、未重启

- 已通过已知主机校验的免密 SSH 确认 `nk-historyguide.service` 为 active，运行目录 `/opt/nk-historyguide`，现用虚拟环境 Python 3.10.12；当前本地代码要求 Python >=3.11，服务器 PATH 未发现 3.11/3.12。
- 公网系统接口仍报告 SQLite + `create_all`。准确定位数据库为 `/opt/nk-historyguide/historyguide.db`；只读检查显示四张早期业务表、无 `alembic_version`，结构与 `0002_audit_logs` 阶段相符但尚不能视作正式迁移版本。
- 现网数据计数：2 条展品均为 `fixture-exhibit-*`，1 条访客状态、0 条访问事件、2 条审计日志；外键检查无违规。环境文件仅发现业务 Key、数据库 URL、日志格式三个变量名，未发现独立操作员 Key；没有查看变量值或资料正文。
- 独立观测报告见 `historyguide-backend/docs/live_inventory_2026-10-14.md`。下一阶段需在隔离 staging 使用真实服务器库的一致副本预演、准备 Python >=3.11 环境与可恢复备份，再考虑部署；当前不能将本地功能或测试绿灯等同现网就绪。

## Step 24：隔离容器 staging 与现网旧库只读接管预演

日期：2026-10-14

状态：技术兼容性验证通过；资料、平台接线及生产发布门禁仍未通过

- 修正 Docker 镜像构建，使其携带 `alembic.ini` 和 `migrations`；在现有服务器上构建 Python 3.12.15 隔离镜像。使用镜像及软件包镜像源，尚未独立核实上游供应链，也未锁定依赖版本。
- 新建与现网分离的空 SQLite staging 库，执行 `alembic upgrade head` 至 `0005_history_review_runs`；`--network none`、无公开端口的容器以 `migrated` 模式启动，`/health`、`/ready`、数据库状态及新工具 OpenAPI 均为 HTTP 200。
- 本地和镜像实际依赖环境均为 221 项测试通过。最初容器测试因只读挂载的默认数据库路径及漏传 README 失败，修正测试环境后全量通过；不能把前两次环境错误当成代码缺陷或掩盖记录。
- 为隔离容器单独生成业务/操作员测试密钥，以只读文件挂载。运行配置校验 0 fail、1 个 CORS 未配置 warning；业务接口无 Key 401、有测试 Key 200，操作员接口无 Key 401、有独立测试 Key 200。没有读取或输出线上旧密钥值。
- 对真实线上 `historyguide.db` 只读挂载运行接管预演：唯一匹配 `0002_audit_logs`，临时副本升级到 `0005_history_review_runs`，原 4 表 5 行摘要不变。**未**对现网库 stamp、迁移、备份留档或切换服务；线上 `nk-historyguide.service` 仍 active。
- 新空 staging 的数据门禁按预期失败：没有展品，也没有已审定的 S01/S02 来源。Coze 尚未接入新工具，馆方评测、强制审核出口、线上密钥轮换及可恢复备份仍待完成。详见 `historyguide-backend/docs/staging_validation_2026-10-14.md`，当前发布结论为 NO-GO。

## Step 25：GitHub 首次推送与论文驱动接管计划

日期：2026-10-14

状态：源码已推至 GitHub；项目发布门禁仍为 NO-GO

- 在项目根目录初始化 Git `main`，远端指向同一仓库的 `https://github.com/nanyan831/huawei.git`（用户给的 SSH 地址因本机 22/443 连接失败而改用 HTTPS）。已完成 Git Credential Manager 设备授权并推送；`git ls-remote` 核对远端 `main` 与本地提交 `ea9df131d9ec5a002bad325ad0d57d6220b4d139` 一致。本条日志新增后应再核对一次最新 SHA。
- 根目录 `.gitignore` 与后端忽略规则排除了虚拟环境、SQLite 数据库、临时 Key、部署压缩包、Git bundle 和本地 DOCX；提交内容做过常见令牌/私钥格式扫描。未读取或提交旧线上业务密钥值。
- 新增 `PROJECT_ROADMAP.md`：基于 ReAct、单/多 Agent 对照、Self-RAG/CRAG、RAG 事实忠实度、AgentDojo 与可靠性评测论文，列出馆方来源、强制审核出口、语义核验、真实评测、部署和馆员入口的完成门禁。结论是先建立单 Agent + 确定性门禁基线，不把第二个 LLM Agent 视为天然更安全。
- 新增 `HANDOFF_PROMPT.md` 供另一台电脑克隆接管，含独立环境测试、状态审计、保密边界及离线 bundle 路径。`historyguide-20261014.bundle` 已按 `main` 单分支重建并通过 `git bundle verify`；它是本机备用文件，不在 GitHub 仓库中。
- 本轮后端 221 项本地测试通过。GitHub 上云不代表 Coze 新工作流、馆方资料或生产部署完成；下一步仍是取得审定来源、Coze 可操作权限与正式发布授权后逐门禁验收。

## Step 26：Windows 克隆接管与四路协同盘点

日期：2026-10-14

状态：克隆与项目阅读已完成；本轮修改仍在本地，发布门禁维持 NO-GO

- 按用户要求从 `https://github.com/nanyan831/huawei.git` 接管到 `D:\华为杯\huawei`。主线程核对克隆 HEAD 与当时远端 `main` 均为 `d2be561b5f90cdd2839434746a2f7fbfb5dc1bbc`；这与 Step 25 首次推送的历史 SHA 不同，不能把旧 SHA 当最新状态。
- 阅读实际文件 `HANDOFF_PROMPT.md`、路线、架构、历史 staging/现网盘点、上下文最近步骤及后端入口。项目仍为单讲解 Agent + 确定性后端审核，不存在本轮已验证的第二个 LLM Agent。
- 按用户要求四路协同：主线程负责环境/依赖和整合，后端代理负责接口及测试，前端代理负责馆员页面/浏览器/启动脚本，文档代理负责路线、交接和实测记录。所有人共享工作目录，按文件边界修改，整合时由主线程核对。
- 本机 `.venv` 为 Python 3.12.13；UV 解压与官方 pip 下载曾失败，清华镜像安装成功。主线程实测 `pip check` 通过、Alembic head 为 `0005_history_review_runs`。镜像安装不是上游供应链独立验证。
- 本机有 Docker CLI 但 daemon 未启动，未完成本轮镜像构建。Steps 23–24 的服务器/container 证据为历史记录，本轮没有再次访问生产库、检查 Coze 登录态或执行轮换/上线。
- 本阶段证据汇总见 `historyguide-backend/docs/local_validation_2026-10-14.md`；本轮 HEAD/远端一致性、最终回归、真实资料、平台接线、备份恢复及发布验收仍未完成。

## Step 27：本地馆员工作台与批量治理完善

日期：2026-10-14

状态：本地功能已实现；整合回归进行中，尚未部署或取得馆员签收

- 新增同源中文 `/operator` 页面，复用操作员证据和审计接口；支持来源与展品 JSON 文件/粘贴、只读预览、确认导入、详情核对、来源批准/撤销、展品来源关联/批准/撤销及审计查看。
- 来源和展品每批最多 20 条，额外伪造审批字段和空白内容被拒绝；预览不写库、不占用 ID，提交重查冲突。导入数据与审计同事务，冲突或审计插入失败整批回滚；CLI 展品导入复用事务逻辑。
- 证据 API 使用独立操作员密钥，错误/缺失密钥失败关闭；页面壳和明确静态资源公开但无资料或密钥。服务端在 JSON 解析前限制 8 MiB 请求体，含无 Content-Length 流式请求。
- 本地启动脚本监听回环地址，隐藏输入新操作员 Key，使用独立 `.local/workspace.db`；已有库须满足迁移门禁。页面不持久化 Key、原文以文本呈现、原始出处仅 HTTP/HTTPS 可点击。操作员姓名是审计字段，不能当身份认证或馆方签字。
- 首轮 Python 回归 241 项中 3 项失败，原因为将全局数据库配置设为 `:memory:` 与持久化检查、跨线程连接不兼容；首轮浏览器 9 项业务检查完成，但 Windows 清理测试库发生 `EBUSY`，整体退出码 1。随后脱敏 `browser-check.json` 记录 13 项浏览器业务/安全/竞态检查、`pageErrors=[]`，包含 320px 无横向溢出；仍须以主线程最终命令退出码和启动脚本证据整合为准，不能抹去首轮失败。
- 操作流程见 `historyguide-backend/docs/operator_workspace.md` 与 `historyguide-backend/docs/evidence_intake.md`，最终结果应续写本机验证记录。未导入清洗候选为批准来源，也未把 fixture 或 `semantic_verified=false` 当事实通过。
- 尚未完成：本轮整合最终回归、依赖锁和镜像构建证据；馆方审定原文/真实展品/Coze ID 映射、馆员签收、真实强制 finalize 轨迹和语义支持评测、生产轮换/备份/恢复/发布仍需独立验收。

## Step 28：四路协同收尾与本机最终回归

日期：2026-10-14

状态：本地工程回归完成；发布门禁仍为 NO-GO

- 主线程完成四路协同整合：后端代理复核操作员密钥与业务密钥隔离、多应用实例鉴权隔离、批量来源/展品及审计事务回滚、单条来源/展品治理操作的审计异常回滚、审核人长度校验；前端代理复核馆员工作台浏览器竞态、401/登出清理、320px/390px 响应式布局；文档工作由主线程合并到本记录和本机验证记录。
- `.venv\\Scripts\\python.exe -m pytest -o addopts= -q` 退出码 0，`263 passed, 1 warning`。警告为第三方 Starlette/httpx 测试客户端弃用提示。`npm.cmd --prefix tests/browser test` 退出码 0，13/13 检查通过，`pageErrors=[]`；`node --check app/static/operator/app.js` 与 `git diff --check` 均退出码 0。
- 依赖开发锁在 Windows Python 3.12.13 独立环境以 `uv pip install --require-hashes` 安装通过，`pip check` 通过；Alembic head 为 `0005_history_review_runs`。本机 Docker daemon 未启动，因此没有新增镜像构建、摘要、容器回归或生产迁移证据。
- 本轮未读取、输出或提交旧业务密钥；未把 fixture、清洗候选资料或测试知识库当作馆方批准资料。新增工作台只提供本地待审批流程，审核人字段不构成身份认证。
- 仍缺馆方签字来源与真实展品 ID、Coze 可编辑登录态和新插件真实轨迹、按句语义支持验收、线上密钥轮换、生产备份/恢复/回滚/迁移、馆员试用签收及发布授权。上述门禁未满足前，不得把本地绿灯宣布为上线或馆方验收。

## Step 29：云端同步后本机验证与访客密钥边界

日期：2026-10-16

状态：远端代码已同步，本机工程回归通过；Docker 与访客网关仍未完成，发布门禁保持 NO-GO

- 当前工作区从 GitHub 快进到 `7d98e51`，更新后 `main` 与 `origin/main` 一致。Windows 浏览器使用本机代理 `127.0.0.1:7892`，Git 直连 GitHub 被重置；仅对本次 fetch 临时指定代理，没有把代理写入仓库配置。
- 当前电脑 Python 3.12.14 虚拟环境全量 `pytest` 为 `263 passed, 2 warnings`，警告均为第三方弃用提示。`npm ci` 成功，馆员工作台浏览器回归 `13/13` 通过，覆盖权限、导入/审批/撤销、移动布局和异步竞态；使用的是隔离随机测试库与临时测试密钥。
- 本机找不到 `docker` 命令，本轮未构建镜像、未记录镜像摘要，也未执行容器回归。先前服务器隔离镜像的成功记录不能替代当前提交的构建证据。
- 复核开发文档发现旧 Web/H5 和运维说明曾要求访客浏览器直接携带共享业务 Key，且把 Handoff 预检当成可直接展示生成答案的门禁。已修正文档：正式访客端须经持钥的服务端网关并校验会话归属与限流；展品/路线和纯校史分别走 review-run，并只展示 `finalize.answer`。这些是待实现/待接线的要求，不表示网关或 Coze 强制出口已上线。
- 继续推进的硬阻塞仍是馆方审定来源与真实展品、Coze 引用 ID 映射、逐句事实支持评测、真实平台轨迹、密钥轮换、备份恢复和馆员签收。不要把清洗候选或 fixture 当作正式资料。
## Step 30 (2026-10-17): General-history literal-claim gate

- Current worktree remains based on `7d98e51`, with prior documentation changes uncommitted. No production service or Coze configuration was changed in this step.
- General-history review now requires each `HistoryCitation` to supply `claim_text` exactly contained in its approved `evidence_quote`; the answer may contain only the ordered claim texts and their source markers. This rejects a 1920 claim paired with a 1919 source and uncited extra prose. The custom Coze OpenAPI schema and staging instructions were updated; the Coze plugin itself must be re-imported only after staging deployment and authorization.
- Focused history/OpenAPI tests passed locally (15 tests); full Python regression passed locally (264 tests, 2 third-party warnings). Literal matching is intentionally restrictive and does not verify historical truth or semantic entailment; `semantic_verified` remains false. Exhibition/route review still has its own structural checks. Continue with real curator sources, trusted final-answer workflow/gateway, real Coze traces, and production gates. Release stays NO-GO.

## Step 31 (2026-10-17): Server-side single-call answer release

- Added protected `/api/genios/answers/history` and `/api/genios/answers/exhibit` endpoints plus `/openapi-genios-answers.json`. One backend request now internally prepares a snapshot, reviews the supplied draft/citations, and finalizes only an allowed answer. History revise and exhibit revise return 409 without echoing the draft; exhibit block returns the safe block answer. These tools are not a public visitor gateway and do not enforce Coze's final display channel.
- Focused history, exhibit, OpenAPI and security checks passed locally (46 tests), including missing-key 401 and revoked-source block. Full local Python regression: 269 passed, 2 third-party warnings; staff-browser checks: 13/13 passed; `git diff --check` passed. No deployment, Coze import, curator content approval, key rotation, or real platform trace occurred. Next: Coze enforced output path, exhibit claim support, approved data, and production gates. Status remains NO-GO.

## Step 32 (2026-10-17): Exhibit literal-claim and route-order gate

- New exhibit/route run citations now require `claim_text` verbatim in an approved source quote. Review rejects any draft text beyond the ordered quoted claims and source markers. For multiple cited exhibits, only a deterministic route prefix built from approved exhibit names and cited order is permitted; the existing route-plan order check still applies.
- Focused exhibit/OpenAPI tests passed locally (23 tests), including invented claim, uncited extra prose, required-field contract and reversed two-exhibit route. Full Python regression: 271 passed, 2 third-party warnings; staff browser: 13/13; `git diff --check`: passed. Old Handoff and `/api/genios/review` remain legacy structural preflight; do not use them as final release. New Coze plugin definitions must be re-imported only after a matching staging deployment. No production or Coze changes were made; status remains NO-GO.

## Step 33 (2026-10-17): Default-off visitor token gateway

- Added opt-in `/api/visitor` routes with a server-only signing key distinct from the business/operator keys. A trusted business-key caller grants a short-lived token for an existing session; the browser uses only that bearer token. Token routes bind state, approved exhibit reads, approved route, visit events and one-call reviewed-answer release to the token's session. No self-service public session creation or database migration was added.
- Local isolated tests cover closed-by-default behavior, missing/reused key rejection, token tampering/expiry, session binding, key separation, approved-only data, rejected extra answer text, blocked draft context, and release after approving all candidate exhibits. Runtime config validation reports missing or reused gateway keys and warns about trusted issuer/HTTPS/proxy rate limits.
- `docs/visitor_gateway.md` records provisioning and remaining risks. This is not a Coze model adapter and does not make the Coze UI's final output mandatory. No public deployment, token delivery, rate-limit proof, museum content approval or key rotation was performed. Status remains NO-GO.
- Full local Python regression: 277 passed, 2 third-party warnings. Staff-browser checks: 13/13. `git diff --check`: passed. The configuration and security-status contracts were updated; no Alembic migration was required because tokens are stateless and short-lived.

## Step 34 (2026-10-17): Single-call release trace gate

- The offline trace checker now accepts the recommended `/api/genios/answers/history` and `/api/genios/answers/exhibit` single-call flow. It requires one successful `answer_tool` event followed by exactly one user-visible `final_answer` identical to the tool's released answer. Planned 4xx/5xx tests can instead set `expected_status_code` and pass only with a matching failed tool event and no visible answer. Other tool endpoints, mixed legacy/new flows, extra answers, and model-modified text fail. The older prepare/review/finalize format remains supported.
- Added focused counterexamples for a 401 tool response followed by an answer, unreviewed extra answer, non-release endpoint, mixed flow, changed visible text, and a failed tool releasing text. Local Python regression: 281 passed, 2 third-party warnings; focused evaluator tests: 9 passed. The checker only validates supplied trace structure and equality; it cannot authenticate a Coze export or prove factual support. Real redacted platform traces and curator labels remain missing, so release status stays NO-GO.

## Step 35 (2026-10-17): Paired single/review-Agent evaluation harness

- Added `scripts/compare_agent_modes.py` and two prompt variants for each of the eight curator cases. The protocol requires three repetitions of every case/variant in both single-Agent and review-Agent modes (96 labeled traces total). The checker rejects missing or duplicate runs, reused trace references, unscored checks, and differences in model, approved corpus revision, backend revision or output budget. It reports failed runs, median latency and token totals per mode without declaring either mode superior.
- Added `docs/paired_agent_evaluation.md` and focused tests; full local Python regression: 288 passed, 2 third-party warnings. The current browser inventory contains no open Coze tab, so no platform edits or real traces were collected. Curator-approved data, signed acceptance thresholds and the second Agent implementation remain pending; the comparison harness is not evidence of production readiness. Status remains NO-GO.

## Step 36 (2026-10-17): Read-only Coze configuration audit

- The user confirmed Coze editing access but no curator-approved source list or real exhibit IDs. Opened the actual NK-GeniOS Agent editor in the in-app browser and read its current configuration without changing it. It is still in single-Agent mode, with only `NK HistoryGuide Flat Handoff` and `NK HistoryGuide Answer Review` attached. The prompt allows general-history answers from the test knowledge base without a required reviewed-answer release call; the visible test knowledge base has 11 files.
- This is direct UI evidence that the new `/api/genios/answers/*` one-call plugin and mandatory final-output workflow have not been connected. No publication, plugin edit, key entry, or staging deployment was performed. Do not re-import a schema that the running server does not yet implement. The Coze tab was retained for later integration. Release status remains NO-GO.

## Step 37 (2026-10-17): Reproducible CI gate prepared

- Added `.github/workflows/ci.yml` with read-only repository permissions and SHA-pinned official checkout/setup actions. On a hosted Ubuntu runner it installs the hash-locked development dependencies, runs the Python suite and isolated operator browser checks, builds the locked Docker image, and probes `/ready` inside the container without publishing a host port or using deployment secrets.
- Official GitHub action releases and tag SHAs were checked before writing the workflow. Local YAML parsing passed; local Python regression remains 288 passed, 2 third-party warnings. This machine has no Docker CLI, and the uncommitted workflow has not run on GitHub, so image build and CI status remain unverified. It does not deploy to staging or production. Release remains NO-GO.

## Step 38 (2026-10-17): Persisted visitor-token revocation and staging access check

- The user reported an independent staging environment, but did not know its connection details. Repository records identify a past network-isolated Docker staging container on the existing server; that historical container had no published port and was not Coze-accessible. The local SSH aliases resolve to private network addresses; a read-only `kunpeng_server` connection attempt timed out during banner exchange. No staging identity or reachable deployment endpoint was verified. No server file, database, Coze configuration, or production process was changed.
- Added Alembic `0006_visitor_access_grants` and a database table containing only SHA-256 token digests, session IDs, expiry and revocation state. Issuance commits the grant before returning the raw token; visitor access now requires both a valid signature and an active recorded grant. A trusted business-key caller can revoke all grants for one session via `/api/visitor/grants/revoke`; a visitor can revoke its own bearer token via `/api/visitor/revoke`. The gateway remains off by default.
- Tests cover signed but unregistered tokens, key separation, session scoping, self-revocation, trusted per-session revocation, and revocation visibility in a fresh database Session. Full local Python regression: 288 passed, 2 third-party warnings. Isolated Alembic migration rehearsal reached `0006_visitor_access_grants` with 11 tables; `git diff --check` passed. These tests do not prove production/staging operation or a cross-host deployment.
- Current code and docs expect migration head `0006`; prior `0005` staging and live-database rehearsal records remain historical evidence only. A new reachable staging target, fresh non-production keys, backup/restore rehearsal, Coze tool import and actual trace tests remain pending. No commit or push was made per the user's instruction. Release remains NO-GO.

## Step 39 (2026-10-17): Migrated loopback runtime smoke

- Added `scripts/smoke_isolated_runtime.py` and a pytest integration test. The script filters inherited `HISTORYGUIDE_` settings, creates a fresh temporary SQLite database, upgrades it to the current Alembic head, starts real Uvicorn only on `127.0.0.1` with random test keys, then checks readiness, the new answer-tool OpenAPI, missing-key 401, visitor session creation, token grant, bearer access, trusted revocation and post-revocation 401. It terminates the child process and removes the temporary database; no production endpoint or configured database is contacted.
- First Windows run completed the HTTP checks but failed temporary-file cleanup because SQLite was briefly locked after process exit. Added bounded cleanup retry with a resolved-path check constrained to the generated temp directory; both the standalone script and its pytest case then passed. This is runtime integration evidence, not Docker, remote staging, Coze integration, museum-data or production evidence. No commit/push or live configuration change occurred; release remains NO-GO.
- Final local verification for this step: full Python suite 289 passed with two third-party deprecation warnings; operator browser suite 13/13 passed; `git diff --check` passed. Two temporary directories from the initial cleanup failure may remain under the OS temp directory; a manual cleanup attempt was blocked by command policy and was not bypassed. The corrected script removed its own subsequent temp databases successfully.

## Step 40 (2026-10-17): Transactional visitor-grant audit

- Grant issuance, trusted per-session revocation, and visitor self-revocation now add audit events in the same database transaction as the credential state change. No raw bearer token or key is logged; issuance records only the expiry, and trusted revocation records the affected count. Audit write failures roll back issuance or revocation so access control and the log do not disagree.
- Focused gateway tests cover expected audit actions and forced audit-write failure for all three credential operations. Approved-source retrieval was inspected: the existing general-history prepare route already returns approved source excerpts for known stable source IDs, while the separate `/api/evidence` source-detail endpoints remain operator-only. Automatic Coze citation-ID mapping and real museum-approved source data remain absent; no duplicate retrieval endpoint was introduced. No server/Coze changes or commit/push occurred, release remains NO-GO.
- Final local verification: full Python suite 290 passed with two third-party deprecation warnings; isolated migrated Uvicorn smoke passed and removed its temporary database; `git diff --check` passed. These checks are local only.

## Step 41 (2026-10-17): Backend-approved source discovery and fixture closure

- Added business-key-only `POST /api/genios/sources/search` and `/openapi-genios-sources.json` for bounded literal keyword lookup over approved backend sources. It returns stable source IDs, source URI, content hash and at most five exact excerpts from the first 8,000 characters; empty results remain inconclusive. Query terms and result counts are capped, SQL LIKE wildcards are escaped, and responses are `no-store`. This is not embedding/semantic retrieval and is not yet imported into Coze.
- Closed a fixture-source approval gap: new `fixture-` or `fixture:` evidence cannot be approved; a legacy record incorrectly marked approved cannot back an exhibit or history answer. The source release rule now requires an actual review record, nonblank provenance/body, and content-hash consistency. Exhibit approval and runtime approval checks use these gates. Tests include a fixture linked after an exhibit was approved and an old source marked approved without a reviewer.
- Focused source/history/exhibit/OpenAPI tests passed. The local-only plugin still needs matching staging deployment, Coze authentication/import, real approved corpus and authentic platform traces. No production changes or commit/push; release remains NO-GO.
- Final verification: full Python suite 295 passed with two third-party deprecation warnings; migrated loopback Uvicorn smoke passed, including missing-key 401 and authenticated empty result for the new search route; `git diff --check` passed. The read-only staging validator now rejects fixture URIs and empty bodies just as the runtime gate does. No remote staging or Coze call was performed.

## Step 42 (2026-10-17): Test knowledge-base import audit

- Rechecked the local test-corpus manifest: it contains 11 Markdown documents but marks only 10 for upload. The full single-file knowledge base is a backup that must not coexist with the nine topic documents and source index. Earlier Coze UI showed 11 attached files; that count is a discrepancy, not proof of which file is extra. The current in-app browser has no open Coze tab, so the actual platform filenames were not rechecked and no Coze content was changed.
- Added a read-only audit script that validates local document SHA-256 values and optionally compares an operator-copied list of actual Coze filenames against the recommended set. Without an uploaded list it explicitly reports `platform_verified=false`. Three focused tests pass, including duplicate-backup detection; full local Python regression is 298 passed with two third-party deprecation warnings. Production corpus approval, Coze IDs, source mappings, real trace acceptance, and staging deployment remain missing; release stays NO-GO. No commit or push was made.
- Repeated read-only SSH probes of the two locally configured aliases: `kunpeng_server` timed out during banner exchange and `pa_vm` timed out on port 22. This computer still has no verified reachable independent staging host or HTTPS endpoint. No remote command ran and no secret was read.

## Step 43 (2026-10-17): Reject whitespace-only source claims

- Found a real release-path edge case: both citation schemas accepted eight spaces as `claim_text`; an empty normalized claim is a substring of every evidence quote, so a draft containing only `[source_id]` could satisfy literal-claim equality. Added field validation rejecting whitespace-only `claim_text` and `evidence_quote` in both history and exhibit citations. API tests now cover both history fields and the exhibit claim; an existing exhibit whitespace-quote test now expects input rejection.
- Full local Python regression is 301 passed with two third-party deprecation warnings; `git diff --check` found no whitespace errors (only Windows line-ending notices). This does not establish semantic entailment, Coze mandatory release, remote staging availability or museum-source approval. No deployment, commit or push; production status remains NO-GO.

## Step 44 (2026-10-17): Source-search recall beyond invalid legacy rows

- Inspected approved-source discovery and found a fixed SQL `LIMIT 50` applied before the Python publication gate. Fifty legacy records marked approved but lacking review metadata could hide a valid source ranked next. Replaced that cutoff with streamed, ordered candidate inspection until the caller's 1-5 valid-result limit is filled; close the SQL result when done. Added a regression with 51 invalid higher-ranked matches followed by a valid match.
- Focused search tests pass; full local Python suite is 302 passed with two third-party deprecation warnings, and `git diff --check` found no whitespace errors. The search is still lexical and may scan many invalid rows; measure real-corpus latency and enforce trusted-proxy rate limits before public use. No source was approved, no Coze/staging deployment, commit or push occurred. Release remains NO-GO.

## Step 45 (2026-10-17): Source approval locks metadata and body

- Found that a post-approval title or original-URI edit did not invalidate the source: only the body hash was checked. Added a deterministic approval fingerprint for source ID, title, URI, and content hash, plus Alembic `0007_source_approval_fingerprint`. Both history and exhibit publication gates reject missing or changed fingerprints. Staging's read-only source validator checks the same fingerprint. The operator source read model now exposes it for audit.
- The migration does **not** backfill legacy approved rows; the migration regression proves they remain unavailable until fresh review/reapproval. Tests also cover source title and URI mutation invalidating an approved exhibit and URI mutation blocking history preparation. The first legacy-adoption rehearsal failed because model and migration column order differed; aligned model column order with the SQLite upgrade rather than relaxing schema matching, then the focused rehearsal passed.
- A new Coze editor tab was created but reading its state timed out twice, so no live configuration was inferred or changed. No remote staging or production deployment, curator sign-off, key rotation, commit or push occurred. Release remains NO-GO.
- Final local verification: full Python suite 306 passed with two third-party deprecation warnings; migrated real-Uvicorn loopback smoke passed and removed its temporary database; `git diff --check` found no whitespace errors. These results do not prove remote deployment or actual Coze behavior.

## Step 46 (2026-10-17): Human claim-support decisions gate answer release

- Read-only Coze UI check confirmed the draft remains single-Agent with only legacy Handoff/Answer Review plugins; its prompt still allows test-knowledge-base history answers without the new backend release tool. No Coze edit, publish, or live deployment was made.
- Added Alembic `0008_claim_support_reviews` and operator-only claim candidate/read/approve/revoke endpoints. Approval requires an explicit `support_confirmed=true`; each record binds exact source ID, approved source fingerprint, evidence quote, and claim text. Create/approve/revoke actions have transaction-coupled audit events. A source metadata/body change or revocation invalidates release.
- `HISTORYGUIDE_CLAIM_SUPPORT_REQUIRED=true` is mandatory in staging/production config validation. When enabled, one-call history and exhibit `pass` answers require approved claim support for every citation; responses disclose `claim_support_reviewed`, while `semantic_verified` stays false. Legacy multi-call prepare/review/finalize HTTP routes reject strict-mode requests to avoid a bypass. Blocked exhibit requests retain their safe block response. Local defaults remain false for legacy tests.
- Focused tests cover missing/draft review, explicit approval, revocation, source metadata invalidation, a negation-fragment candidate left unapproved, operator separation, and strict legacy-route rejection. Full Python suite passed with two third-party deprecation warnings; isolated migrated Uvicorn HTTP smoke passed; `git diff --check` passed with only Windows line-ending notices. No commit or push was made.
- This is auditable human review plumbing, not automated entailment or proof of real curator identity. The staff interface does not yet expose this new approval workflow. Real curator-approved data, staging access, Coze mandatory output wiring, concurrency/revocation policy, authenticated reviewer identity, and authentic platform traces remain missing. Release status remains NO-GO.

## Step 47 (2026-10-17): Staff claim-support review workspace

- Added operator-key-protected paginated claim-support listing and a “声明审核” tab to the existing same-origin staff workspace. Staff can submit a draft source-quote/claim pair, inspect the full approved source alongside the quote and claim, explicitly confirm support, approve, and revoke. Current source fingerprint/status is displayed, and the approval button stays disabled on a stale source. The page uses text nodes for untrusted source content and retains the existing in-memory-only key handling and 401 logout behavior.
- Added API list/filter regression and isolated real-browser steps for create/approve/revoke, disabled approval before confirmation, inert untrusted text, desktop/mobile layout, and the previous workflows. Browser suite passed 15/15; desktop/mobile screenshots were inspected with no overflow. No real curator account or materials were used.
- This closes a local operator UI gap but not real identity assurance, source sign-off, staging deployment, Coze mandatory release wiring, semantic model evaluation, or final handover. No commit/push/live edit; release remains NO-GO.

## Step 48 (2026-10-17): Bind strict release to approval rows and audit

- Inspected the one-call answer services and found the claim approval check ran just before finalize but did not lock source/approval rows or record which approval IDs were used. Strict release now reads both row types with `FOR UPDATE` in deterministic citation order and holds the transaction through answer finalization. The finalization audit event records only the approval IDs, not source/answer text. Existing local non-strict workflows retain their behavior.
- Focused tests cover PostgreSQL dialect lock SQL, exact audit linkage for history and exhibit passes, and fail-closed repeat calls after approval revocation. A first exhibit test unexpectedly returned HTTP 200 because the session lacked a visit event and was safely blocked; the test now models a valid visit and asserts `decision=pass` as well as HTTP status.
- SQLite ignores row-level `FOR UPDATE`; these tests prove query construction and sequential behavior, not real multi-connection serialization. A genuine PostgreSQL staging race test, verified reviewer identity, curator-approved source/exhibit data, Coze output gate and real traces remain required. No deployment or commit/push; release stays NO-GO.

## Step 49 (2026-10-17): Close legacy draft-review strict-mode bypass

- Audited the remaining answer-like routes. Legacy `POST /api/genios/review` could return a passing `safe_answer` equal to the draft without any claim-support approval. In strict mode it now returns 409 before reading the session or draft. Existing multi-call run routes were already closed in strict mode. Handoff remains structured context and cannot itself enforce the user-visible final answer path.
- Updated the legacy Review OpenAPI description/409 response and rewrote the Coze staging guide around the new one-call history/exhibit release tools, current Alembic head, claim approval, and a mandatory final-output workflow. The guide explicitly prohibits treating test-KB content, old Review `safe_answer`, or a prompt-only instruction as release authorization.
- Focused strict-mode, context, and OpenAPI tests passed; full local Python suite passed with two third-party warnings. No live Coze edit, new staging deployment, real curator approval, or commit/push. Release remains NO-GO.

## Step 50 (2026-10-18): PostgreSQL claim-release concurrency staging probe

- Added `psycopg[binary]` to runtime dependencies and rebuilt both SHA-256 lock files with the repository's Python 3.11 universal-lock procedure. A hash-locked development install completed and `pip check` reported no broken requirements. The local environment also received `uv` only as a development tool; `.venv` remains ignored and no tool binary or credential was added to Git.
- Added `scripts/verify_postgres_claim_release_lock.py`. It refuses non-PostgreSQL targets and refuses all writes unless `--acknowledge-staging-write-test` is provided. Against an isolated migrated PostgreSQL staging database it creates a uniquely named synthetic evidence source and approved claim, runs the actual strict `_require_claim_support` check in one transaction, attempts approval revocation from a second connection, verifies the revocation remains blocked until release commit and is visible to a fresh transaction afterward, then removes its source, review and related audit records by default. Connection URLs and credentials are never printed.
- Hardened abnormal cleanup: even if candidate creation fails after source creation, the source and matching audit records are removed; live probe threads are released and joined before cleanup and engine disposal. Added five local safety/cleanup tests, plus documentation in the README, migration guide, claim-support guide and staging validation record.
- Verification: 15 focused migration/claim/probe tests passed; the full Python suite passed 318 tests with one third-party Starlette deprecation warning; the isolated operator browser suite passed all 15 checks; the migrated real-Uvicorn loopback smoke passed and removed its temporary database; `compileall`, hash-locked install, `pip check`, and `git diff --check` passed (line-ending notices only). The explicit SQLite rejection path was also exercised. One initial browser command used the wrong working-directory-relative package path and did not run tests; rerunning `npm test` from `tests/browser` produced the recorded 15/15 result.
- This machine has no Docker, Podman, `psql`, PostgreSQL server, or known reachable staging database URL, so the genuine two-connection PostgreSQL probe was **not run**. It remains a mandatory staging command, along with real curator-approved data, authenticated curator identity, Coze one-call release wiring, bypass tests, authentic traces, backup/restore rehearsal and deployment evidence. No Coze/server edit, commit or push occurred. Release remains NO-GO.

## Step 51 (2026-10-18): Staff single-exhibit upload form and atomic source links

- Confirmed the staff workspace already supported JSON exhibit batches, but a non-technical administrator still had to author JSON and link sources in a separate action. Added a visible “上传一件展品” form under the exhibit intake mode with stable ID, name, period, importance, description, provenance reference, optional existing source IDs, keywords, people, themes and time range. The form requires explicit confirmation and labels the result as pending review; it never approves or publishes an exhibit.
- Added operator-key-protected `POST /api/evidence/exhibits`. The payload contains one validated exhibit plus up to 20 unique existing source IDs. The exhibit, source links and `exhibit_uploaded` audit event commit in one transaction. A missing source returns 404 without creating the exhibit; duplicate/invalid input is rejected; an audit or integrity failure rolls back both the exhibit and its links. Existing JSON batch import and later manual source linking remain available.
- The browser flow now uploads `browser-exhibit` through the ordinary form, atomically links `browser-S01`, verifies the detail, then performs the existing explicit approval. Desktop and 390 px mobile screenshots were visually inspected: the form remains readable, the table precedes the long form on mobile, and no horizontal overflow or overlap was observed.
- Verification: 39 focused operator API tests passed; full Python regression passed 321 tests with one third-party Starlette deprecation warning; isolated browser regression passed 15/15; migrated real-Uvicorn smoke passed; `git diff --check` passed with line-ending notices only. The first browser run failed only because the test rewrite removed a fixture variable reused by a later race test; restoring that local fixture produced the recorded 15/15 result.
- This is a local staff intake implementation, not a deployed administrator portal. It still requires HTTPS/access restriction, a configured operator credential, real curator identity, museum-approved sources, staging migration/deployment and staff acceptance. Uploaded records do not sync themselves to Coze and cannot enter approved answer release until source and exhibit governance gates pass. No Coze/server edit, commit or push occurred; release remains NO-GO.

## Step 52 (2026-10-18): Isolated server image, PostgreSQL lock and upload validation

- Reached the existing server directly and kept production unchanged. The current workspace archive was extracted under `/opt/nk-historyguide-staging-20261018` and built as `nk-historyguide:staging-20261018`. A new SQLite database migrated through `0008_claim_support_reviews`; the retained staging container runs with `network=none`, no published ports, no restart and no OOM event. Internal `/health`, `/ready`, `/operator`, Answer OpenAPI and Handoff OpenAPI checks all returned HTTP 200.
- Reused only the locally cached PostgreSQL image to create a separate temporary PostgreSQL 16 container on an internal-only Docker network with an in-memory data directory and no host port. The current migrations completed, the staging runtime configuration validator reported 0 failures and 0 warnings, and the genuine two-connection claim-release probe passed: revocation stayed blocked until release commit, a fresh transaction observed it afterward, and all synthetic records were removed.
- Ran a server-side black-box administrator upload against a separate disposable SQLite database. Source creation and single-exhibit upload both returned HTTP 201; the exhibit remained draft, its source link was present and detail retrieval succeeded. The upload container and database were deleted after the check.
- Cleanup verification found the temporary PostgreSQL container, network, upload container and database-URL environment file absent. The production systemd service remained active and its public health endpoint remained healthy. No production file, database, reverse proxy, key or Coze setting was changed. The server still exposes the older public application; the retained new staging has no public endpoint. Full evidence is in `historyguide-backend/docs/staging_validation_2026-10-18.md`. Release remains NO-GO pending public staging/Coze wiring, real museum-approved data, curator identity, backup/restore rehearsal and authentic traces.

## Step 53 (2026-10-18): Submission regression and repository entry point

- Re-ran the complete current workspace before committing: Python regression passed 321 tests with one third-party Starlette deprecation warning; the isolated real-browser operator suite passed all 15 workflows; `compileall`, `pip check`, CI workflow YAML parsing and `git diff --check` passed. The warning is in the installed FastAPI/Starlette test adapter and did not fail application tests.
- Scanned all pending text files for the previously exposed `hg-prod-` key prefix, common GitHub token/private-key signatures and credential-bearing PostgreSQL URLs. No match was found. Ignored local key/database/runtime files remain outside `git status`.
- Added the repository-root `README.md` as the reviewer entry point. It summarizes the implemented architecture, runnable commands, validation evidence, important documents and the distinction between a submit-ready code prototype and an uncompleted production rollout. No claim of production deployment or museum approval was added.
