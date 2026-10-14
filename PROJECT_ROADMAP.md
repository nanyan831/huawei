# NK HistoryGuide 收尾路线（2026-10-14）

## 结论

当前是「Coze 单个讲解 Agent + FastAPI 确定性审核服务」，不是已经上线的双 LLM Agent。后端的展品/路线和一般校史 run 均已有 prepare -> review -> finalize 本地接口，但新接口尚未接入 Coze；线上仍是旧版服务，旧库没有 Alembic 版本记录。隔离 staging 的 221 项测试及旧库只读副本迁移预演通过，业务数据门禁仍失败：没有馆方审定的 S01/S02 和真实展品。详细实测见 `historyguide-backend/docs/staging_validation_2026-10-14.md`。

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

### 2. 可证明的答案出口

- 在 staging 部署与 `0005` 一致的后端。Coze 导入两个新 run 插件；展品/路线用 `/api/genios/runs`，一般校史用 `/api/genios/history-runs`。
- Coze 工作流或应用网关必须只显示 finalize 返回的 `answer`，不能由提示词自行决定是否跳过 review。超时、401、409、工具不可用、撤销来源和过期快照均不得输出未审核草稿。
- 在 review 与馆员评测之间补按句 claim -> source quote 的语义支持检查；该检查需要原文可追溯、能拒绝「引用存在但不支持结论」，不得把当前 `semantic_verified=false` 当通过。
- 证据：Coze 配置截图/导出、脱敏端到端轨迹、强制出口绕过测试及来源冲突/缺失用例。仅本地接口绿灯不算完成。

### 3. 对照评测，而非先堆 Agent

- 扩充 `historyguide-backend/evals/curator_cases.json` 为馆方标注集，至少覆盖创办日期混淆、展品真实来源、未知馆藏号、反向路线、来源撤销、提示注入、工具失败和多轮状态变化。
- 单 Agent 基线与「独立研判 Agent」候选在同一模型预算、同一资料、同一测试集上比较。每类关键用例多次运行并做等义改写及故障注入；馆员审核事实与引文，工程端记录 pass/revise/block、延迟和成本。
- 上线阈值由馆方与项目负责人在测试前签署；建议高风险用例零未拦截错误、所有正式事实句均有可核对来源，并报告重复运行方差。小样本零错误不等于生产零风险。
- 证据：真实、脱敏的轨迹和馆员评分，不接受示例 JSON 或自动脚本自评作为事实正确性的证明。

### 4. 生产运行与体验

- 先留可恢复备份并演练回滚；仅在隔离副本和 staging 验证后迁移线上旧库。正式部署需要 Python >=3.11、迁移模式、独立密钥、最小网络暴露、HTTPS、监控告警、日志脱敏、限流与故障降级。数据库方案按并发/备份要求选型，若转 PostgreSQL，必须先做数据迁移与恢复验收。
- Web/H5 覆盖访客会话、进度、讲解、路线和来源查看；馆员入口与访客入口分权。Coze 插件授权、调用链和前端展示在真实环境逐项验收。
- 证据：`docs/production_readiness_decision_checklist.md` 与 `docs/staging_validation_record.md` 的真实记录、备份恢复演练、访问控制测试、馆方试运行签收。

## 何时算项目可以收尾

不是“服务器一直运行”就完成。只有代码已推送、馆方来源已审、强制审核出口已接线、真实双路径问答与路线通过重复评测、密钥已轮换、备份回滚已演练、馆员导入入口可用、试运行签收和运维责任人明确，才可宣布交付。此后是常规运营、来源更新和监控，不是无限期开发。

当前最近的安全行动：确认 GitHub 可达并核验远端提交；随后取得馆方审批资料和 Coze 可操作权限。在此之前不要发布新的 Coze Agent 或修改线上数据库。
