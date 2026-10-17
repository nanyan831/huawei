# NK HistoryGuide 收尾路线（2026-10-14）

## 结论

当前是「Coze 单个讲解 Agent + FastAPI 确定性审核服务」，不是已经上线的双 LLM Agent。后端的展品/路线和一般校史 run 均已有 prepare -> review -> finalize 本地接口，但新接口尚未接入 Coze；线上仍是旧版服务，旧库没有 Alembic 版本记录。隔离 staging 的 221 项测试及旧库只读副本迁移预演通过，业务数据门禁仍失败：没有馆方审定的 S01/S02 和真实展品。详细实测见 `historyguide-backend/docs/staging_validation_2026-10-14.md`。

2026-10-14 换电脑续做：Windows 本地仓库位于 `D:\华为杯\huawei`，克隆基线与当时远端 `main` 均为 `d2be561b5f90cdd2839434746a2f7fbfb5dc1bbc`。本轮补齐同源馆员工作台 `/operator`、来源/展品只读预览、原子批量导入及审批/撤销流程；代码仍需以本轮最终回归记录核验，不能据此认定已推送、已部署或馆方已验收。新电脑的测试、依赖和构建限制见 `historyguide-backend/docs/local_validation_2026-10-14.md`，旧服务器 staging 记录保持为历史证据。

推荐架构：访客输入 -> 意图/会话状态 -> 已审定来源检索 -> 讲解 Agent 草稿 -> 引用和快照的确定性门禁 -> 按句事实支持度研判（可由独立模型辅助，但必须可审计）-> finalize 唯一对外出口 -> 反馈和追踪。馆员的来源审批、展品绑定、版本撤销是独立后台流程，不交给访客 Agent 自主操作。纯校史问题不要伪造展品 ID；路线问题必须绑定真实会话与展品。

双 Agent 是待评测的选项，不是上线前提。先让单 Agent + 强制审核链路形成可靠基线；只有在馆方标注集上，独立研判 Agent 明显减少无依据回答、且延迟/成本可接受时，才将它加入生产路径。独立模型的「通过」仍不能代替来源原文、确定性校验或馆方批准。

## 论文到工程决策

| 一手研究 | 与本项目有关的证据 | 工程取舍 |
| --- | --- | --- |
| [ReAct, ICLR 2023](https://arxiv.org/abs/2210.03629) | 推理与工具调用交替能处理交互任务 | 允许 Agent 调用检索/后端，但限制工具权限和步数；不把自由工具循环当安全边界 |
| [Single-agent or Multi-agent Systems?, 2025](https://arxiv.org/abs/2505.18286) | 单/多 Agent 收益取决于任务和成本，论文提出混合级联 | 先做单 Agent 基线；仅对高风险或不确定回答调用第二研判模型，并与基线实测比较 |
| [Self-RAG, ICLR 2024](https://research.ibm.com/publications/self-rag-learning-to-retrieve-generate-and-critique-through-self-reflection) 与 [CRAG, 2024](https://arxiv.org/abs/2401.15884) | 检索质量和生成自检会影响事实性 | 为检索增加来源质量/缺失判断；对馆史仅回退到馆方批准来源，不自动信任公网检索 |
| [Reliability-Aware RAG, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1738/) 与 [Generate but Verify, IJCNLP-AACL 2025](https://aclanthology.org/2025.ijcnlp-long.56/) | 多来源可信度及答案对证据的忠实度需要单独评估 | 每个事实句绑定可查看的来源摘录和版本；冲突/证据不足时拒答或送馆员复核 |
| [AgentDojo, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/97091a5177d8dc64b1da8bf3e1f6fb54-Paper-Datasets_and_Benchmarks_Track.pdf) | 工具与外部内容可成为提示注入入口 | 检索文档当数据；限制 Agent 工具、权限、出站内容，并做注入回归测试 |
| [ReliabilityBench, 2026](https://arxiv.org/abs/2601.06112) 与 [Agent Evaluation Survey, 2025](https://arxiv.org/abs/2507.21504) | 单次通过率不覆盖重复运行、等义改写或工具故障 | 用真实 Coze 轨迹重复运行，分别统计事实支持、引用、拒答、路线、故障降级、成本和延迟 |

以上是论文启发的设计推断，不表示论文验证了本项目或当前代码已具备对应能力。

## 必须完成的顺序与验收

### 0. 版本与密钥边界

- 将源码、测试、上下文记录推至 GitHub；数据库、密钥、部署压缩包和本机虚拟环境不得入库。新电脑克隆后可独立运行测试。
- 锁定部署依赖和镜像来源，记录构建摘要。已暴露的线上业务 Key 在可回滚窗口内轮换，配置独立操作员 Key；不要把值写入仓库、Prompt 或聊天。
- 证据：远端 `main` 指向本地 HEAD、干净工作区、可复现构建、配置检查与密钥轮换验收记录。

### 1. 馆方资料与馆员入口

- 馆方逐条审定原始出处、摘录、日期、版本、授权与稳定来源 ID；Coze 知识库 ID 和后端 ID 建立一一映射。正式展品须有稳定 exhibit_id、可核对来源和馆方批准记录；fixture 永不升为正式数据。
- 完成工作人员导入/预览/批准/撤销页面，复用现有 operator API，新增必要的鉴权、上传校验与审批审计；导入失败整批回滚。
- 证据：馆员签字的来源清单、映射表、真实展品导入/撤销回归测试和 staging 数据门禁通过。当前这项未完成。

本地工程进度：工作人员页面已实现并复用 operator API，支持普通表单上传单件展品、可选原子关联已有来源，也支持 JSON 文件/粘贴、预览确认、来源正文查看、展品绑定、批准/撤销及审计查看；细节见 `historyguide-backend/docs/operator_workspace.md`。单件上传的展品、来源链接和审计记录同事务提交，来源不存在或审计失败时不留下半条记录。导入固定为待审批状态，预览不写库；服务端鉴权与 8 MiB 请求体限制不能替代馆方核实原文。阶段 1 仍缺真实资料、签字清单、Coze ID 映射、目标环境数据门禁及馆员试用签收。

### 2. 可证明的答案出口

- 在 staging 部署与当前 Alembic head `0008_claim_support_reviews` 一致的后端。Coze 导入单次放行工具；严格模式关闭旧的 `/api/genios/runs` 和 `/api/genios/history-runs` 多步 HTTP 路径。
- Coze 工作流或应用网关必须只显示 finalize 返回的 `answer`，不能由提示词自行决定是否跳过 review。超时、401、409、工具不可用、撤销来源和过期快照均不得输出未审核草稿。
- 本地新增 `/api/genios/answers/history` 与 `/api/genios/answers/exhibit` 单次放行工具（OpenAPI: `/openapi-genios-answers.json`），服务端串行 prepare/review/finalize 并只返回放行答案或安全阻断。它尚未部署或导入 Coze，也不能强制平台一定调用；访客最终展示通道仍须工作流/可信网关锁定。
- 在 review 与馆员评测之间补按句 claim -> source quote 的语义支持检查；该检查需要原文可追溯、能拒绝「引用存在但不支持结论」，不得把当前 `semantic_verified=false` 当通过。
- 本地已加入来源版本绑定的人工 claim-to-quote 审核草稿/批准/撤销记录。staging/production 配置校验要求 `HISTORYGUIDE_CLAIM_SUPPORT_REQUIRED=true`，单次放行接口在严格模式逐条校验当前审批，缺审或撤销返回 409；`claim_support_reviewed=true` 仅表示有对应人工审批记录，`semantic_verified` 仍为 false。操作见 `historyguide-backend/docs/claim_support_review.md`。真实馆员身份认证、原始出处核实、跨句语义能力和并发撤销原子性尚未验收。
- 馆员工作台现有“声明审核”页可创建候选、并列阅读来源全文/摘录/声明、明确确认、批准或撤销；本地隔离浏览器流程已验证。它尚未连接真实馆方账号体系或 staging 数据，也不意味着候选由馆方实际审定。
- 严格放行现将来源和审核行的 `FOR UPDATE` 锁保持到 finalize 审计/答案提交，审计记录所用审核 ID。2026-10-18 已在服务器的一次性 PostgreSQL 16 容器上完成真实双连接验证：放行事务持锁期间撤销被阻塞，提交后撤销对新事务可见，唯一探针记录已清理；完整脱敏记录见 `historyguide-backend/docs/staging_validation_2026-10-18.md`。该容器没有公网端口且测试后已删除；这证明当前代码的并发锁路径，不代表生产数据库迁移或 Coze 接线完成。
- 发现旧 `/api/genios/review` 可把结构检查通过的草稿放进 `safe_answer`；严格模式现返回 409，旧多步路由也不可用。结构化 Handoff 仍可供上下文检索，但它不授权最终展示；Coze 工作流/可信展示网关必须单独强制只采用一次放行工具的 `answer`。staging 接线文档已改为这一路径，真实 Coze 绕过测试尚未完成。
- 本地一般校史 review 已先收紧为逐字摘录：`claim_text` 必须位于已批准的 `evidence_quote`，草稿不得夹带额外句子；这是防止明显的无依据改写，不是跨句语义蕴含、来源真伪或馆方事实审核。新插件参数尚未在 Coze 更新，正式语义门禁仍未完成。
- 本地新增受业务密钥保护的 `/api/genios/sources/search` 与 `/openapi-genios-sources.json`，只按短关键词检索后端已审批、非 fixture、哈希和审核记录完整的来源摘录；未命中返回空列表。它是有边界的字面检索，不能代替 Coze ID 映射、馆方原始资料核验或语义检索，尚未在 staging/Coze 部署。
- 本地展品/路线 run review 也已要求逐字 `claim_text`，多展品答案只能使用后端可核对的展品名与引用顺序；当前已导入的 Coze 插件仍不含这个新字段。自由改写、跨来源归纳及真正语义蕴含继续保持未验收，不得声称已解决。
- 证据：Coze 配置截图/导出、脱敏端到端轨迹、强制出口绕过测试及来源冲突/缺失用例。仅本地接口绿灯不算完成。

### 3. 对照评测，而非先堆 Agent

- 扩充 `historyguide-backend/evals/curator_cases.json` 为馆方标注集，至少覆盖创办日期混淆、展品真实来源、未知馆藏号、反向路线、来源撤销、提示注入、工具失败和多轮状态变化。
- 单 Agent 基线与「独立研判 Agent」候选在同一模型预算、同一资料、同一测试集上比较。每类关键用例多次运行并做等义改写及故障注入；馆员审核事实与引文，工程端记录 pass/revise/block、延迟和成本。
- 上线阈值由馆方与项目负责人在测试前签署；建议高风险用例零未拦截错误、所有正式事实句均有可核对来源，并报告重复运行方差。小样本零错误不等于生产零风险。
- 证据：真实、脱敏的轨迹和馆员评分，不接受示例 JSON 或自动脚本自评作为事实正确性的证明。

本地已补配对评测脚本 `scripts/compare_agent_modes.py` 和每题两种问法，按三次重复要求单/双 Agent 在同一模型、语料版本、后端版本和输出预算下成对记录。它只核对标签覆盖并报告错误次数、延迟与 token，不会代替真实 Coze 轨迹、馆员评分或事先签署的上线阈值；操作说明见 `historyguide-backend/docs/paired_agent_evaluation.md`。

### 4. 生产运行与体验

- 先留可恢复备份并演练回滚；仅在隔离副本和 staging 验证后迁移线上旧库。正式部署需要 Python >=3.11、迁移模式、独立密钥、最小网络暴露、HTTPS、监控告警、日志脱敏、限流与故障降级。数据库方案按并发/备份要求选型，若转 PostgreSQL，必须先做数据迁移与恢复验收。
- Web/H5 覆盖访客会话、进度、讲解、路线和来源查看；馆员入口与访客入口分权。Coze 插件授权、调用链和前端展示在真实环境逐项验收。
- 访客浏览器不得持有共享业务或操作员密钥；需由服务端网关持钥并校验访客会话归属、限流和唯一 `finalize` 答案出口。旧 Web/H5 文档的直连示例仅可用隔离测试密钥在 staging 验证，不能作为生产方案。
- 本地已加入默认关闭的访客令牌网关：可信服务以业务 Key 对已有会话签发短期令牌，访客凭令牌访问自己的状态、已审批路线/展品和后端审核答案。令牌摘要现持久化，可由可信服务按会话或访客自身撤销；仍没有自助会话注册、Coze 模型适配器、代理层限流或生产部署证据；签发令牌不得交给模型或放进公开二维码，详见 `historyguide-backend/docs/visitor_gateway.md`。
- 证据：`docs/production_readiness_decision_checklist.md` 与 `docs/staging_validation_record.md` 的真实记录、备份恢复演练、访问控制测试、馆方试运行签收。

本地已补 `scripts/smoke_isolated_runtime.py`：临时迁移库、随机测试密钥和仅回环地址的真实 Uvicorn HTTP 冒烟检查，包括访客授权与撤销。2026-10-18 又在服务器构建了当前锁定镜像，并保留一个 `network=none`、无公开端口的隔离 SQLite staging；健康、就绪、管理员入口、工具 OpenAPI、单展品上传和 PostgreSQL 并发探针均通过。它仍不可被 Coze 或访客访问，也不是生产部署；公开 staging、备份恢复和真实平台接线仍待完成。

## 何时算项目可以收尾

不是“服务器一直运行”就完成。只有代码已推送、馆方来源已审、强制审核出口已接线、真实双路径问答与路线通过重复评测、密钥已轮换、备份回滚已演练、馆员导入入口可用、试运行签收和运维责任人明确，才可宣布交付。此后是常规运营、来源更新和监控，不是无限期开发。

当前最近的安全行动：确认 GitHub 可达并核验远端提交；随后取得馆方审批资料和 Coze 可操作权限。在此之前不要发布新的 Coze Agent 或修改线上数据库。

## 本轮四路协同与接续顺序

用户要求四路协同，本轮采用主线程加三名代理共享同一工作目录，按文件范围分工：主线程负责版本盘点、独立环境、依赖锁、README 和集成验证；后端代理负责接口、鉴权、事务及测试隔离；前端代理负责馆员页面、浏览器流程和启动脚本；文档代理负责路线、交接、操作说明及验证记录。共享目录中的修改不会自动形成 Git 提交，最终由主线程统一核对。

下一步按阶段证据推进：先完成并保存本机回归与锁定依赖的核验，再在具备 Docker daemon 的环境构建新镜像并记录摘要；取得馆方审批资料后，在独立 staging 导入/审批并建立 Coze 来源映射；获得 Coze 可编辑登录态后完成强制 finalize 接线、语义支持检查和重复评测。正式轮换、备份恢复、迁移及发布按既定安全边界执行，仍须相应真实环境证据和必要的人为授权。尚无这些输入时继续完成可独立验证的工程工作，发布结论保持 **NO-GO**。
