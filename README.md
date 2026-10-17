# NK HistoryGuide 南开校史智能讲解与安全研判系统

NK HistoryGuide 是面向南开大学校史馆场景的可审计智能讲解原型。项目把大模型生成与
确定性后端门禁分开：讲解 Agent 负责理解问题和组织草稿，FastAPI 后端负责会话状态、
展品路线、来源治理、逐条声明审核、答案放行和审计记录。

## 已实现能力

- 校史问答和展品讲解的单次安全放行接口；证据不足时返回明确阻断结果。
- 展品推荐、参观顺序、剩余时间和会话状态的结构化 Handoff。
- 来源、展品、来源关联及 claim-to-quote 审核的创建、批准、撤销和审计。
- 工作人员页面 `/operator`：上传单件展品、批量导入、预览、关联来源和审核。
- 可撤销的短期访客令牌网关，默认关闭，不向浏览器暴露共享业务密钥。
- Alembic 迁移、SQLite 本地运行和 PostgreSQL 并发放行锁验证。
- Coze/NK-GeniOS OpenAPI 文档、接线说明、评测脚本和运维清单。

## 架构

```text
访客 / Coze Agent
        |
        v
受限工具调用与会话状态
        |
        v
已审批来源检索 -> Agent 草稿 -> 引用/快照/声明审核门禁
                                      |
                          +-----------+-----------+
                          |                       |
                       放行答案                安全阻断
                          |
                          v
                    审计记录与撤销

工作人员 -> /operator -> 来源/展品/声明审核 -> 同一数据库治理链路
```

独立“研判 Agent”是可对照评测的增强方案，不替代确定性门禁和馆员审核。项目先保留可复现
的单 Agent 基线，再通过同一测试集比较双 Agent 是否真正降低错误。

## 快速运行

要求 Python 3.11 及以上。进入 `historyguide-backend` 后执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
$env:HISTORYGUIDE_DATABASE_URL = "sqlite:///./historyguide.db"
$env:HISTORYGUIDE_SCHEMA_MODE = "migrated"
$env:HISTORYGUIDE_API_KEY = "replace-with-a-local-test-key"
$env:HISTORYGUIDE_OPERATOR_API_KEY = "replace-with-a-different-local-test-key"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开 `http://127.0.0.1:8000/operator` 可试用工作人员入口。密钥只用于本地测试，不要写入
仓库、Prompt、浏览器代码或提交材料。

## 验证

```powershell
cd historyguide-backend
.\.venv\Scripts\python.exe -m pytest -o addopts= -q
cd tests\browser
npm test
```

2026-10-18 的提交前验证结果为 Python `322 passed`、工作人员浏览器流程 `15/15`。
当前镜像还在服务器隔离环境完成了：

- SQLite 与 PostgreSQL 从空库迁移到 `0008_claim_support_reviews`；
- staging 配置检查 0 失败、0 警告；
- PostgreSQL 双连接并发撤销/放行锁验证；
- 管理员创建来源、上传单件展品、保持草稿和原子关联来源的黑盒验证。

脱敏记录见
[服务器隔离验证](historyguide-backend/docs/staging_validation_2026-10-18.md)。

## 资料与演示边界

仓库中的 fixture、测试知识库和示例展品仅用于工程验证，不代表馆方正式馆藏记录。正式
对外讲解仍需馆方审定来源、真实展品 ID、工作人员签收、Coze 最新放行工具接线以及备份
恢复演练。当前公开域名仍运行旧版兼容服务；本仓库最新版已通过隔离服务器验证，但尚未
替换线上服务。该边界不会影响代码和原型提交，但不能据此宣称已经生产上线。

## 主要文档

- [后端与接口说明](historyguide-backend/README.md)
- [项目收尾路线](PROJECT_ROADMAP.md)
- [Coze 接线流程](historyguide-backend/docs/coze_agent_run_workflow.md)
- [工作人员入口](historyguide-backend/docs/operator_workspace.md)
- [Agent 架构调研](historyguide-backend/docs/agent_architecture_2026.md)
- [双 Agent 对照评测](historyguide-backend/docs/paired_agent_evaluation.md)
- [换机接管 Prompt](HANDOFF_PROMPT.md)

## 目录

```text
historyguide-backend/   FastAPI 服务、数据库迁移、工作人员前端、测试与文档
.github/workflows/      自动回归与镜像构建检查
PROJECT_ROADMAP.md      完成条件、证据和剩余上线门禁
HANDOFF_PROMPT.md       在另一台电脑继续项目的接管说明
```
