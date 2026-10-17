# Windows 本机续做与验证记录（2026-10-14）

本记录对应 `D:\华为杯\huawei` 的本轮完善，区分实际本机验证与仓库已有的服务器历史记录。它不是部署或馆方事实验收记录。发布结论为 **NO-GO**。

## 版本和环境

- 远端：`https://github.com/nanyan831/huawei.git`；主线程已核对克隆 HEAD 与当时远端 `main` 均为 `d2be561b5f90cdd2839434746a2f7fbfb5dc1bbc`。
- 本轮修改在共享工作区中完成；克隆 SHA 不包含新增馆员工作台，不能用它证明本轮代码已提交或推送。最终交接须另核对 `git status`、最新 HEAD 和远端 SHA。
- 平台：Windows / PowerShell；后端虚拟环境 `.venv` 为 Python 3.12.13。
- 依赖准备曾遇到 UV 解压失败与官方 PyPI 超时，随后使用清华 PyPI 镜像安装成功。实际安装包含 FastAPI 0.143.0、SQLAlchemy 2.1.4、Pydantic 2.14.1、pytest 8.4.2。
- 主线程实测 `pip check` 通过，`alembic heads` 为 `0005_history_review_runs`。这是版本/依赖一致性检查，未迁移生产库。
- 本机 Docker CLI 可用，但 Docker daemon 未启动；本轮 Docker 镜像构建、镜像摘要和容器内回归均未验证。`staging_validation_2026-10-14.md` 描述的是旧服务器隔离容器，不能迁移为本机成功记录。

## 项目阅读与本轮范围

交接入口为 `HANDOFF_PROMPT.md` 和 `PROJECT_ROADMAP.md`。项目主体是 FastAPI 后端，提供展品、访客状态/访问事件、推荐/路线、Handoff、确定性 Review、两类快照 run、来源/展品审批与审计。数据库迁移为 `0001` 至 `0005`；配套脚本覆盖导入/导出、隔离恢复及迁移预演、只读 staging/运行配置检查、脱敏轨迹和馆方评分的格式门禁。

资料包、测试知识库和 `evals/curator_cases.json` 是候选材料或评测模板；本轮未取得馆方签字原文或真实评分。当前 Coze 工作流、线上运行版本和部署密钥没有在本机重新核实，历史盘点只作定位线索。

四路分工为主线程整合与环境/依赖、后端接口与测试、前端页面与浏览器、文档与交接记录。为避免共享目录互相覆盖，代理按文件范围修改并由主线程统一回归。

本轮新增可独立完成的馆员入口 `/operator`：来源与展品 JSON 预览/导入、详情核对、来源批准/撤销、展品关联和批准/撤销、审计展示。页面公开壳不含资料；证据 API 使用独立操作员密钥，批量预览不写入，批量导入和单条治理操作均在审计失败时回滚，服务端请求体上限为 8 MiB。流程见 `operator_workspace.md` 和 `evidence_intake.md`。

## 回归与排错证据

| 检查 | 已确认事实 | 本轮结论 |
| --- | --- | --- |
| 首轮 Python 全量回归 | 241 项中 3 项失败；全局数据库 URL 设置为 `:memory:`，与持久化检查及跨线程连接不兼容 | 首轮失败，保留记录；不能提前报全量通过 |
| 后端修复后回归 | 主线程以 `.venv\\Scripts\\python.exe -m pytest -o addopts= -q` 重跑，`263 passed, 1 warning`，退出码 0；警告为 Starlette/httpx 测试客户端弃用提示 | Python 全量回归通过；弃用警告不影响退出码 |
| 首轮浏览器回归 | 9 项业务检查完成，测试数据库清理发生 `EBUSY`，进程退出码 1 | 首轮整体失败；业务成功不等于完整运行成功 |
| 浏览器修复后回归 | 主线程以 `npm.cmd --prefix tests/browser test` 重跑，13/13 checks passed，退出码 0，`pageErrors=[]`；覆盖 320px/390px 无横向溢出、异步竞态、401、登出和随机数据库清理 | 浏览器回归通过；结果 JSON 位于忽略的 `.local/browser-artifacts/` |
| 依赖锁 | 运行锁 24 项、开发锁 33 项；独立 Windows Python 3.12.13 环境以 `uv pip install --require-hashes --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.lock` 安装 32 个适用包、退出码 0 | 该平台锁安装通过；上游独立核验和容器构建未完成，维护见 `dependency_locking.md` |
| Alembic head | 主线程运行 `alembic heads` 得到 `0005_history_review_runs` | head 定位通过；不是生产迁移证据 |
| 本机 Docker | CLI 存在，daemon 未启动 | 未构建验证 |

主线程还以 `node --check app/static/operator/app.js` 验证前端语法（退出码 0），以 `git diff --check` 验证补丁空白（退出码 0），并确认锁文件未包含本机路径、私密索引或临时密钥字符串。`pip check` 通过；`alembic heads` 为 `0005_history_review_runs`。本地启动脚本仍只监听回环地址并使用独立 `.local/workspace.db`。

浏览器工程样例均为非历史资料。结果 JSON 和截图位于忽略的 `.local/browser-artifacts/`，不可作为馆方批准或历史事实评分。首轮失败记录保留；本节新增结果是最终主线程命令的退出码证据，不等同部署或馆方验收。

## 尚未通过的交付门禁

- 无新的馆方批准原文、授权/版本/签字清单、稳定真实 exhibit ID 或 Coze/后端来源映射。
- 无本机已授权 Coze 登录态、双路径新插件接线、强制 finalize 的真实端到端轨迹。
- 无按句 claim 到 source quote 的语义支持验收；`semantic_verified=false` 不能作为事实通过。
- 无同一馆方标注集上的单 Agent / 独立研判 Agent 重复对照和馆方评分。
- 无本轮真实线上 Key 轮换、生产可恢复备份、恢复/回滚演练、生产数据库迁移或发布证据。
- 无馆员试用签收、访客 Web/H5 真实接线验收及运维责任人签收。

本轮本机工程回归与依赖锁证据已收齐；下一步是在 Docker daemon 可用的独立环境构建镜像并记录摘要。资料与 Coze 权限到齐后再按 `PROJECT_ROADMAP.md` 逐阶段收集目标环境证据。当前可试用本地工作人员流程，不能宣布上线或项目验收完成。

## 2026-10-16 另一工作区复验

- 当前工作区 `C:\Users\11329\Desktop\华为杯校史馆` 的 `main` 已快进到 `7d98e51`，与获取后的 `origin/main` 一致。以下结果对应这个提交和随后仅修改文档的工作区，不代表服务器部署。
- `.venv\Scripts\python.exe --version` 为 Python 3.12.14；`.venv\Scripts\python.exe -m pytest -o addopts= -q` 退出码 0，`263 passed, 2 warnings in 6.61s`。警告来自 FastAPI/Starlette 的第三方弃用接口。
- `tests/browser` 下 `npm.cmd ci` 退出码 0，`npm.cmd test` 退出码 0，`13/13` 浏览器检查通过。测试自建回环服务、随机 SQLite 文件和临时测试密钥；未连接生产环境。
- `docker version` 无法执行，因为当前 PowerShell 找不到 `docker` 命令；本轮镜像构建、摘要和容器内回归仍未验证。
- Web/H5、部署和运维文档已澄清：访客浏览器不可持有共享业务/操作员 Key，Handoff 仅作预检，只有 review-run 的 `finalize.answer` 可展示。服务端访客网关和 Coze 强制出口尚未实现或部署，工程与发布结论不变：**NO-GO**。

## 2026-10-17 一般校史逐字主张门禁

- `HistoryCitation` 新增必填 `claim_text`；review 要求它是已审批 `evidence_quote` 的逐字片段，且草稿只由这些片段和对应 `[source_id]` 组成。新增 1920/1919 错配、额外未引用句、缺失字段回归。对应 Coze OpenAPI 契约已更新，本地全量 `pytest -o addopts= -q` 退出码 0：`264 passed, 2 warnings`。
- 这使一般校史输出暂时限制为摘录式回答，不等于语义蕴含、史实真伪或馆方签字验收。当前已导入 Coze 的插件不自动更新；本轮未重新导入、未部署服务器、未接入强制最终出口。仍为 **NO-GO**。

## 2026-10-17 单次审核放行工具

- 新增受业务密钥保护的 `/api/genios/answers/history`、`/api/genios/answers/exhibit` 及双操作 OpenAPI 文档。后端内部串行执行 prepare/review/finalize，仅返回放行答案或安全阻断；revise 返回 409 且不回显草稿。局部回归覆盖通过、拒绝错误年份、拒绝错误展品摘录、撤销来源后阻断、无 Key 为 401、OpenAPI 契约。
- 该工具不是浏览器可直连的无密钥访客网关，不能强迫 Coze 调用，也没有改变现有三步接口。正式上线仍需独立访客身份/会话、限流、服务端持钥、Coze 强制展示路径及真实平台轨迹。当前工作区全量 `pytest -o addopts= -q` 为 `269 passed, 2 warnings`；馆员浏览器测试 `13/13` 通过，`git diff --check` 通过。尚未部署或导入 Coze，仍为 **NO-GO**。

## 2026-10-17 展品逐字主张与路线顺序

- 新 run 的 `EvidenceCitation` 也要求必填 `claim_text`，且必须是获批来源摘录中的逐字片段。草稿仅可由这些片段及 `[source_id]` 组成；引用多个展品时可加由后端展品名和路线顺序校验的固定前缀。错误主张、额外讲解和倒序均触发 `revise`。
- 旧 `/api/genios/review` 与 Handoff 兼容接口仍属结构化预检，不能替代 run/finalize。逐字约束会限制自由讲解；它不是史实语义、上下文充分性或来源可信度验证。当前全量 Python 回归 `271 passed, 2 warnings`，馆员浏览器 `13/13` 通过，`git diff --check` 通过。Coze 插件未更新，线上仍未接线，发布门禁维持 **NO-GO**。

## 2026-10-17 访客令牌网关本机回归

- 默认关闭的 `/api/visitor` 网关在隔离测试库中验证了可信业务 Key 签发、独立 HMAC 签名令牌、会话绑定、过期/篡改拒绝、已审批展品与路线过滤、访客事件、两类审核答案及未审批候选导致的安全阻断。它不创建公开会话，也不调用 Coze 模型。
- 当前工作区全量 `pytest -o addopts= -q` 退出码 0：`277 passed, 2 warnings`。馆员浏览器 `13/13`，`git diff --check` 退出码 0。本机测试不证明 HTTPS、代理限流、令牌交付、线上密钥轮换或平台最终出口。网关未在 staging/production 启用，仍为 **NO-GO**。
