# NK HistoryGuide 开发上下文记录

用途：避免对话上下文过长或压缩后丢失项目状态。每次继续开发前，先阅读本文档，再阅读两份项目定位与路线文档中与当前阶段相关的内容。

## 固定工作规则

1. 每次开始开发前先阅读本文档。
2. 不偏离项目定位：NK HistoryGuide 是面向真实校史馆参观场景的上下文感知 AI 智能讲解与参观 Agent，不是普通校史问答机器人。
3. Codex 负责 FastAPI 后端、数据管理、Visitor State、展品管理、GeniOS 协作接口、测试和文档。
4. Codex 不负责大模型训练、数字人、AR/VR 和无关功能。
5. 每完成一个阶段或重要步骤，都在本文档追加简短结果和下一步期望。

## 已读取的核心文档

- `NK_HistoryGuide与南开校史Agent差异化定位文档 (1).docx`
- `NK_HistoryGuide_Codex开发边界与实施路线.md`
- `NK_HistoryGuide_Codex启动Prompt文档.docx`

## 当前项目状态

日期：2026-09-22

项目根目录：

```text
C:\Users\11329\Desktop\华为杯校史馆
```

已建立后端目录：

```text
C:\Users\11329\Desktop\华为杯校史馆\historyguide-backend
```

当前目录尚未初始化为 Git 仓库。

## 已完成结果

### 阶段 1：后端基础工程

已完成：

- 创建 `historyguide-backend`
- 创建 FastAPI 应用入口 `app/main.py`
- 创建健康检查接口 `GET /health`
- 创建基础配置与日志模块
- 创建 `requirements.txt`
- 创建 `requirements-dev.txt`
- 创建 `pyproject.toml`
- 创建 `.gitignore`
- 创建测试 `tests/test_health.py`
- 创建后端 README
- 创建本地虚拟环境 `.venv`
- 安装 FastAPI、Uvicorn、SQLAlchemy、pytest、httpx 等依赖

验证结果：

- `pytest` 通过，结果为 `1 passed`
- Uvicorn 可以启动
- `GET /health` 返回：

```json
{"status":"ok","service":"nk-historyguide-backend","version":"0.1.0"}
```

备注：

- 测试时出现 FastAPI/Starlette TestClient 的上游弃用警告，不影响当前阶段运行。

### 阶段 2：展品数据库与展品 API

已完成：

- 新增 SQLite 数据库初始化
- 新增 `Exhibit` SQLAlchemy 模型
- 新增展品 Pydantic schema
- 新增展品服务层
- 新增 `GET /api/exhibits`
- 新增 `GET /api/exhibits/{exhibit_id}`
- 支持展品筛选参数：`keyword`、`period`、`importance_min`
- 新增展品 API 测试
- 更新后端 README

展品模型当前字段：

- `id`
- `name`
- `description`
- `period`
- `keywords`
- `importance`
- `people`
- `time_range`
- `themes`
- `source_reference`

验证结果：

- `pytest` 通过，结果为 `5 passed`
- Uvicorn 可以启动
- `GET /health` 返回正常
- `GET /api/exhibits` 返回空列表 `[]`
- 运行后会创建本地 SQLite 文件 `historyguide.db`

设计决定：

- 当前不自动灌入校史展品事实，避免引入未经核验的历史内容。
- 后续真实展品数据必须来自校史馆资料、GeniOS 知识库或其他明确来源。

### 阶段 3：Visitor State

已完成：

- 新增 `VisitorState` SQLAlchemy 模型
- 新增 Visitor State Pydantic schema
- 新增 Visitor State 服务层
- 新增 `POST /api/visitor-states`
- 新增 `GET /api/visitor-states/{session_id}`
- 新增 `PATCH /api/visitor-states/{session_id}`
- 支持 `visitor_type`：`freshman`、`alumnus`、`tourist`
- 支持字段：`session_id`、`visitor_type`、`current_exhibit`、`visited_history`、`interest`、`remaining_time`
- 对 `current_exhibit` 和 `visited_history` 中引用的展品 id 做存在性校验
- 新增 Visitor State API 测试
- 更新后端 README

验证结果：

- `pytest` 通过，结果为 `10 passed`
- Uvicorn 可以启动
- `GET /health` 返回正常
- `POST /api/visitor-states` 可以创建参观 session
- `GET /api/visitor-states/{session_id}` 可以读取参观 session

设计决定：

- Visitor State 以一次真实参观 session 为中心，不以普通聊天会话为中心。
- 后端只保存参观上下文，不生成讲解内容。
- 引用展品时必须能在 Exhibit 数据中找到对应 id，避免 GeniOS 收到不可解释的上下文。

### 阶段 4：推荐接口

已完成：

- 新增推荐结果 schema
- 新增可解释规则推荐服务
- 新增 `GET /api/recommendations/{session_id}`
- 支持 `limit` 参数，范围 1 到 10
- 推荐依据包括：`visitor_type`、`remaining_time`、`interest`、`current_exhibit`、`visited_history` 和 Exhibit 数据
- 推荐结果包含：`exhibit_id`、`name`、`reason`、`priority`
- 推荐会排除已访问展品和当前展品
- 新增推荐接口测试
- 更新后端 README

验证结果：

- `pytest` 通过，结果为 `14 passed`
- Uvicorn 可以启动
- `GET /health` 返回正常
- `POST /api/visitor-states` 可以创建参观 session
- `GET /api/recommendations/{session_id}` 可以返回推荐结果
- 真实库暂无展品数据时，推荐接口正常返回空列表 `[]`

设计决定：

- MVP 推荐采用可解释规则策略，不调用大模型。
- 后端只给出结构化推荐和推荐理由，不生成讲解文本。
- 推荐接口为后续 GeniOS 上下文包提供候选展品依据。

### 阶段 5：GeniOS 上下文协作接口

已完成：

- 新增 GeniOS 上下文包 schema
- 新增 GeniOS 上下文组装服务
- 新增 `GET /api/genios/context/{session_id}`
- 支持 `recommendation_limit` 参数，范围 1 到 10
- 上下文包包含 Visitor State、当前展品、已访问展品、推荐展品、缺失展品引用、协作边界说明
- 缺失展品引用不会导致接口崩溃，会进入 `missing_exhibit_ids`
- 新增 GeniOS 上下文接口测试
- 更新后端 README

验证结果：

- `pytest` 通过，结果为 `17 passed`
- Uvicorn 可以启动
- `GET /health` 返回正常
- `POST /api/visitor-states` 可以创建参观 session
- `GET /api/genios/context/{session_id}` 可以返回结构化上下文包
- 真实库暂无展品数据时，上下文包正常返回空展品与空推荐列表

设计决定：

- 后端提供结构化上下文包，不调用大模型。
- GeniOS 负责对话、RAG、知识检索和讲解生成。
- 上下文包显式包含协作边界，避免后端角色越界。

### 阶段 6：可靠展品数据导入流程

已完成：

- 新增展品导入服务
- 新增展品 JSON seed 格式文档 `docs/exhibit_seed_format.md`
- 新增导入脚本 `scripts/import_exhibits.py`
- 新增非历史事实开发 fixture `data/example_exhibits.fixture.json`
- 新增批量创建展品服务函数
- 校验 JSON 必须为数组
- 校验必填字段和 `importance` 范围
- 校验 seed 文件内部重复 id
- 校验数据库中已存在 id，避免重复导入
- 新增导入流程测试
- 修复导入脚本直接运行时找不到 `app` 包的问题
- 更新后端 README

验证结果：

- `pytest` 通过，结果为 `23 passed`
- 导入命令可以成功导入 2 条非历史 fixture 展品
- `GET /api/exhibits` 可以读到导入后的 fixture 展品
- 重复导入同一 fixture 会被拒绝，并返回已存在 id 列表

设计决定：

- 开发 fixture 明确标注为非历史事实，避免伪造南开校史内容。
- 真实校史展品数据必须通过同一 JSON 格式导入，并在 `source_reference` 中保留来源说明。
- 导入脚本只负责写入经核验展品记录，不进行知识生成。

### 阶段 7：接口契约与演示流程文档

已完成：

- 新增 API 契约文档 `docs/api_contract.md`
- 新增本地端到端演示流程文档 `docs/local_demo_workflow.md`
- API 契约覆盖 Health、Exhibits、Visitor State、Recommendations、GeniOS Context
- 演示流程覆盖安装、导入 fixture、启动后端、健康检查、展品列表、创建 Visitor State、读取推荐、读取 GeniOS 上下文包
- README 新增接口契约和演示流程文档入口

验证结果：

- `pytest` 通过，结果为 `23 passed`
- 文档仅使用非历史 fixture 示例，未伪造南开校史事实

设计决定：

- API 契约面向前端与 GeniOS 对接，不引入新业务边界。
- 演示流程只展示后端主链路，不包含大模型生成、数字人、AR/VR 或无关前端功能。

### 阶段 8：API polish 与运行准备清单

已完成：

- 新增运行准备文档 `docs/operational_readiness.md`
- 补充一致的错误响应示例
- 补充开发 SQLite 数据库重置说明
- 补充 OpenAPI 检查说明
- 补充 MVP readiness checklist
- 新增 OpenAPI 合同测试 `tests/test_openapi_contract.py`
- README 新增运行准备文档入口

验证结果：

- `pytest` 通过，结果为 `25 passed`
- OpenAPI 核心路径检查通过
- OpenAPI 路径摘要包含：
  - `/health`
  - `/api/exhibits`
  - `/api/exhibits/{exhibit_id}`
  - `/api/visitor-states`
  - `/api/visitor-states/{session_id}`
  - `/api/recommendations/{session_id}`
  - `/api/genios/context/{session_id}`

设计决定：

- 暂时保留 FastAPI 默认 `422` 校验响应，不额外引入统一错误 envelope。
- 运行准备清单只覆盖后端 MVP，不扩展到 GeniOS 生成、数字人、AR/VR 或大型前端。

### 阶段 9：最终 MVP 核验与交付整理

已完成：

- 运行完整测试
- 按本地演示流程完成端到端核验
- 新增阶段性交付说明 `docs/mvp_handoff.md`
- 汇总已实现后端能力
- 列出 GeniOS、真实校史资料、前端/Web/H5 仍需完成的事项
- 更新后端 README

验证结果：

- `pytest` 通过，结果为 `25 passed`
- 重置本地 SQLite 数据库并重新导入 2 条非历史 fixture 展品
- `GET /health` 返回正常
- `GET /api/exhibits` 返回导入后的 fixture 展品
- `POST /api/visitor-states` 可以创建参观 session
- `GET /api/recommendations/{session_id}` 返回未访问展品推荐
- `GET /api/genios/context/{session_id}` 返回完整上下文包
- OpenAPI 核心路径可访问

设计决定：

- 当前后端 MVP 可用于本地演示、GeniOS 上下文集成、前端 API 集成和真实展品数据导入。
- 尚不声明完整生产系统完成，因为真实校史资料、GeniOS RAG、部署硬化和前端体验不属于当前后端 MVP 已完成范围。

### 阶段 10：部署配置与环境变量支持

已完成：

- 将核心配置改为支持环境变量读取
- 新增 `.env.example`
- 新增 `.dockerignore`
- 新增 `Dockerfile`
- 新增部署说明 `docs/deployment.md`
- 新增配置测试 `tests/test_config.py`
- README 新增部署说明入口

支持的环境变量：

- `HISTORYGUIDE_APP_NAME`
- `HISTORYGUIDE_APP_VERSION`
- `HISTORYGUIDE_SERVICE_ID`
- `HISTORYGUIDE_LOG_LEVEL`
- `HISTORYGUIDE_DATABASE_URL`

验证结果：

- `pytest` 通过，结果为 `27 passed`
- 环境变量覆盖 `HISTORYGUIDE_SERVICE_ID` 后，`GET /health` 返回自定义 service id

设计决定：

- 部署配置只覆盖后端服务运行，不引入 GeniOS 生成、数字人、AR/VR 或无关功能。
- 当前数据库仍以 SQLite 为 MVP 验证目标，PostgreSQL 迁移列为后续增强。

### 阶段 11：结构化参观总结接口

已完成：

- 新增 Visit Summary schema
- 新增 Visit Summary 服务层
- 新增 `GET /api/visits/{session_id}/summary`
- 新增结构化参观总结测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

接口返回内容：

- `session_id`
- `visitor_state`
- `visited_count`
- `visited_exhibits`
- `interests`
- `remaining_time`
- `missing_exhibit_ids`
- `genios_next_step`

验证结果：

- `pytest` 通过，结果为 `30 passed`
- 运行态创建 `summary-smoke-session` 后，`GET /api/visits/summary-smoke-session/summary` 返回结构化摘要
- OpenAPI 已包含 `/api/visits/{session_id}/summary`

设计决定：

- 参观总结接口只返回结构化摘要，不生成自然语言总结。
- GeniOS 可使用该摘要结合知识库生成有依据的参观回顾。

### 阶段 12：规则化参观路线规划接口

已完成：

- 新增 Route Plan schema
- 新增 Route Plan 服务层
- 新增 `GET /api/visit-routes/{session_id}/plan`
- 支持 `max_items` 参数，范围 1 到 10
- 路线条目来自未访问推荐候选展品
- 根据展品 `importance` 估算参观时长
- 按 `remaining_time` 控制计划总时长
- 新增路线规划接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

接口返回内容：

- `session_id`
- `remaining_time`
- `planned_minutes`
- `items`
- `planning_note`

验证结果：

- `pytest` 通过，结果为 `34 passed`
- 运行态创建 `route-smoke-session` 后，`GET /api/visit-routes/route-smoke-session/plan` 返回结构化路线计划
- OpenAPI 已包含 `/api/visit-routes/{session_id}/plan`

设计决定：

- 路线规划接口只返回结构化参观顺序，不做室内地图导航。
- 路线规划接口不生成讲解文本。
- 该接口面向前端路线提示和 GeniOS 路线感知对话输入。

### 阶段 13：Web/H5 集成准备 - CORS 配置

已完成：

- 新增 `HISTORYGUIDE_CORS_ORIGINS` 环境变量
- 新增逗号分隔环境变量解析
- FastAPI 在显式配置来源时启用 CORS middleware
- 默认不开放跨域来源
- 新增 CORS 配置测试
- 更新 `.env.example`
- 更新部署说明、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `35 passed`
- 已验证允许来源 `http://localhost:5173` 请求 `/health` 时返回 `access-control-allow-origin`

设计决定：

- CORS 仅作为 Web/H5 联调与部署配置能力，不开发前端页面。
- 默认不使用通配跨域，避免生产部署时无意开放浏览器来源。
- 该阶段仍不涉及 GeniOS 生成、大模型训练、数字人或 AR/VR。

### 阶段 14：展品导入来源校验增强

已完成：

- 在展品导入流程中新增 `source_reference` 非空校验
- 缺少来源说明的 seed 记录会被拒绝导入
- 新增来源校验测试
- 更新展品 seed 格式文档
- 更新运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `36 passed`

设计决定：

- 仅收紧导入流程，不强制改动数据库模型，以兼容已有开发记录。
- 真实校史展品进入系统时必须保留来源说明。
- 后端仍不生成或补写历史事实。

### 阶段 15：参观事件记录接口

已完成：

- 新增 Visitor Visit Event schema
- 新增参观事件服务函数
- 新增 `POST /api/visitor-states/{session_id}/visit-events`
- 记录真实参观中的扫码或进入展品事件
- 自动更新 `current_exhibit`
- 自动将展品追加到 `visited_history`
- 重复访问同一展品时不重复追加历史
- 可选更新 `remaining_time`
- 新增参观事件接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `40 passed`
- OpenAPI 已包含 `/api/visitor-states/{session_id}/visit-events`
- 运行态创建 `event-smoke-20260922142600` 后，`POST /api/visitor-states/{session_id}/visit-events` 返回 `current_exhibit=fixture-exhibit-002`、`visited_history=[fixture-exhibit-001, fixture-exhibit-002]`、`remaining_time=18`

设计决定：

- 参观事件接口用于真实展厅扫码或展品进入场景，减少前端手动拼接完整 Visitor State 的负担。
- 该接口只更新结构化参观状态，不生成讲解文本。
- 展品 id 仍必须存在，避免写入不可解释的参观上下文。

### 阶段 16：GeniOS 结构化交接包接口

已完成：

- 新增 GeniOS Handoff schema
- 新增 GeniOS Handoff 服务函数
- 新增 `GET /api/genios/handoff/{session_id}`
- Handoff 包聚合 GeniOS context、route plan、visit summary
- 支持 `recommendation_limit` 和 `route_max_items` 参数
- 新增 handoff 接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `42 passed`
- OpenAPI 已包含 `/api/genios/handoff/{session_id}`
- 运行态创建 `handoff-smoke-20260922143042` 后，`GET /api/genios/handoff/{session_id}` 返回 context、route_plan、visit_summary 和 handoff_note

设计决定：

- Handoff 包只聚合结构化后端数据，不调用大模型。
- GeniOS 仍负责对话、RAG、知识检索和讲解生成。
- 该接口用于减少 GeniOS 集成时多次调用的拼装成本。

### 阶段 17：展品导入 dry-run 校验

已完成：

- 新增 `validate_exhibits_for_import` 服务函数
- `scripts/import_exhibits.py` 新增 `--dry-run`
- dry-run 会校验 JSON 结构、必填字段、`importance` 范围、`source_reference` 非空、seed 内重复 id 和数据库已有 id
- dry-run 不写入展品记录
- 新增 dry-run 服务测试
- 更新展品 seed 格式文档、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `44 passed`
- 对当前开发库中已存在的 fixture 执行 dry-run 时，正确拒绝重复 id
- 对临时非历史 fixture seed 执行 dry-run 时，输出 `Validated 1 exhibit records. No records were imported.`

设计决定：

- 真实校史展品导入前应先 dry-run，降低误写数据库风险。
- dry-run 仍只校验结构与来源，不替代人工历史事实审核。
- 后端不生成或补写历史内容。

### 阶段 18：部署 readiness 检查接口

已完成：

- 新增 `GET /ready`
- readiness 接口执行轻量数据库检查
- 数据库可访问时返回 `status=ready` 和 `database=ok`
- 数据库检查失败时返回 `503`
- 新增 readiness 测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、部署说明、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `45 passed`
- OpenAPI 已包含 `/ready`
- 运行态 `GET /ready` 返回 `{"status":"ready","service":"nk-historyguide-backend","version":"0.1.0","database":"ok"}`

设计决定：

- `/health` 保持为基础存活检查。
- `/ready` 用于部署平台确认数据库连接状态。
- readiness 不检查 GeniOS、RAG 或生成能力，因为这些不属于后端职责。

### 阶段 19：展品数据导出备份流程

已完成：

- 新增 `exhibit_export_service.py`
- 新增 `scripts/export_exhibits.py`
- 支持将当前数据库展品记录导出为 seed 风格 JSON
- 导出时保持展品结构化字段和 UTF-8 JSON
- 新增展品导出测试
- 更新 README、展品 seed 格式文档、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `47 passed`
- 对当前开发库执行导出 smoke，输出 `Exported 2 exhibit records to <temp export path>.`

设计决定：

- 导出能力用于真实展品数据备份、迁移和重置前保护。
- 导出不做历史事实审核，也不生成缺失内容。
- 真实校史记录仍必须来自经核验资料，并保留 `source_reference`。

### 阶段 20：展品元数据 Facets 接口

已完成：

- 新增 Exhibit facets schema
- 新增 `get_exhibit_facets` 服务函数
- 新增 `GET /api/exhibits/facets`
- 返回展品总数，以及 `periods`、`keywords`、`people`、`themes` 的结构化计数
- 新增 facets 接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `48 passed`
- 运行态 `GET /api/exhibits/facets` 返回当前开发库 2 条 fixture 的 period、keyword、theme 统计

设计决定：

- Facets 用于 Web/H5 筛选器、数据巡检和 GeniOS 集成准备。
- Facets 只统计结构化展品元数据，不生成历史内容。
- 该接口不替代真实校史资料审核。

### 阶段 21：展品列表分页参数

已完成：

- `GET /api/exhibits` 新增 `limit` 参数，范围 1 到 200
- `GET /api/exhibits` 新增 `offset` 参数，默认 0
- 分页在过滤与排序后应用
- 新增分页测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `49 passed`
- 运行态 `GET /api/exhibits?limit=1&offset=1` 返回当前开发库排序后的第二条 fixture 展品

设计决定：

- 保持原有列表响应为数组，不引入新的分页 envelope，避免破坏现有前端/GeniOS 调用。
- 分页用于真实展品数据增长后的 Web/H5 浏览和轻量集成。
- 该能力只影响结构化展品查询，不生成历史内容。

### 阶段 22：Visitor State 列表查询

已完成：

- 新增 `list_visitor_states` 服务函数
- 新增 `GET /api/visitor-states`
- 支持 `visitor_type` 筛选
- 支持 `limit` 参数，范围 1 到 200
- 支持 `offset` 参数，默认 0
- 新增 Visitor State 列表测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `50 passed`
- 运行态 `GET /api/visitor-states?visitor_type=tourist&limit=1&offset=1` 返回符合筛选条件的 tourist session

设计决定：

- Visitor State 列表用于 Web/H5 session 恢复、联调和运维查看。
- 该接口只返回已存储的结构化 Visitor State，不推断用户画像。
- 该接口不生成讲解文本，也不扩展为聊天会话管理。

### 阶段 23：Visitor State 统计接口

已完成：

- 新增 Visitor State stats schema
- 新增 `get_visitor_state_stats` 服务函数
- 新增 `GET /api/visitor-states/stats`
- 返回 `total_sessions`
- 返回 `visitor_types`、`current_exhibits`、`interests` 的结构化计数
- 返回 `no_current_exhibit_count`
- 返回 `remaining_time` 的 min、max、average
- 新增 Visitor State stats 测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `51 passed`
- 运行态 `GET /api/visitor-states/stats` 返回当前开发库 session 分布统计

设计决定：

- Stats 用于本地演示、联调和轻量运维观察。
- Stats 只聚合已存储 Visitor State，不推断用户画像。
- Stats 不生成讲解文本，也不替代 GeniOS 对话/RAG。

### 阶段 24：展品数据质量报告接口

已完成：

- 新增 Exhibit quality report schema
- 新增 `get_exhibit_quality_report` 服务函数
- 新增 `GET /api/exhibits/quality-report`
- 返回 source_reference 覆盖率
- 返回 importance 分布
- 返回缺少 source_reference、keywords、themes、people 的展品 id 列表
- 新增质量报告接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `52 passed`
- 运行态 `GET /api/exhibits/quality-report` 返回当前开发库质量报告：来源、关键词、主题完整，people 字段为空的 fixture 被列出

设计决定：

- 质量报告用于真实展品数据导入后的结构化巡检。
- 质量报告不验证历史准确性，不生成缺失内容。
- 缺失项仍需由馆方资料、GeniOS 知识库或人工审核补齐。

### 阶段 25：GeniOS 能力发现接口

已完成：

- 新增 GeniOS capability schema
- 新增 `build_genios_capability_package` 服务函数
- 新增 `GET /api/genios/capabilities`
- 返回后端/GeniOS 协作边界
- 返回支持的访客类型：`freshman`、`alumnus`、`tourist`
- 返回推荐集成工作流
- 返回 GeniOS、Visitor State、推荐、路线、总结和质量报告相关结构化接口清单
- 新增 capabilities 接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `53 passed`

设计决定：

- capabilities 接口用于 GeniOS 或 Web/H5 对接前发现后端能力和边界。
- 该接口只返回结构化集成说明，不读取参观 session，不调用大模型。
- 后端仍不生成讲解文本；GeniOS 仍负责对话、RAG、知识检索和内容生成。

### 阶段 26：展品来源追踪报告接口

已完成：

- 新增 Exhibit source report schema
- 新增 `get_exhibit_source_report` 服务函数
- 新增 `GET /api/exhibits/source-report`
- 返回展品总数、已带来源数量、无来源数量
- 返回无来源展品 id 列表
- 按精确 `source_reference` 分组返回来源引用、数量和展品 id
- 将 source report 加入 GeniOS capabilities 端点清单
- 新增 source report 接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `54 passed`

设计决定：

- source report 用于真实展品数据导入后的来源分组巡检。
- source report 不判断来源质量，不验证历史准确性，不生成缺失来源文本。
- 该接口辅助馆方资料批次核对和 GeniOS grounding 准备。

### 阶段 27：数据库状态与迁移准备接口

已完成：

- 新增 `GET /api/system/database`
- 返回当前 SQLAlchemy backend、driver、persistence 类型
- 返回当前 schema 管理方式：`sqlalchemy_create_all_mvp`
- 返回迁移目标提示：`postgresql_with_formal_migrations`
- 避免暴露完整数据库 URL
- 新增数据库状态接口测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、部署说明、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `55 passed`

设计决定：

- 当前 MVP 仍以 SQLite 为已验证数据库后端。
- `/api/system/database` 只做部署与迁移状态可见性，不执行迁移。
- PostgreSQL 仍需正式迁移工具和 staging 验证后才能作为生产方案。

### 阶段 28：可选 API Key 保护

已完成：

- 新增 `HISTORYGUIDE_API_KEY` 配置
- 新增 `X-HistoryGuide-Api-Key` 业务 API 保护中间件
- 默认不启用，保持本地演示和现有测试调用不变
- 启用后业务 API 缺少或携带错误 key 返回 `401`
- 保持 `/health`、`/ready`、`/api/system/database`、OpenAPI 和 docs 公开，便于部署探针
- 新增 API key 配置测试
- 新增 security 测试
- 更新 API 契约、部署说明、运行准备、MVP handoff、README 和 `.env.example`

验证结果：

- `pytest` 通过，结果为 `59 passed`

设计决定：

- API Key 保护是部署硬化能力，不替代完整用户体系或角色权限。
- GeniOS 和 Web/H5 在部署启用 key 后需要统一传入 `X-HistoryGuide-Api-Key`。
- 本阶段不引入登录、用户账号、管理后台或无关权限系统。

### 阶段 29：参观事件流水

已完成：

- 新增 `VisitorVisitEventLog` 模型和 `visitor_visit_events` 表
- `POST /api/visitor-states/{session_id}/visit-events` 在更新 Visitor State 的同时写入事件流水
- 新增 `GET /api/visitor-states/{session_id}/visit-events`
- 事件流水返回 `id`、`session_id`、`exhibit_id`、`remaining_time`、`event_time`
- GeniOS capabilities 中将 visit event 能力更新为 `GET/POST`
- 新增事件流水接口测试
- 新增 OpenAPI 方法级测试，确认 visit-events 同时支持 GET 和 POST
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `62 passed`

设计决定：

- 事件流水用于真实参观过程中扫码或进入展品的结构化时间序列记录。
- 该能力不推断游客意图，不生成行为画像，不生成讲解文本。
- Visitor State 仍保留当前状态快照；visit event timeline 用于回放和连续上下文。

### 阶段 30：GeniOS 上下文包含参观事件流水

已完成：

- `GeniosContextPackage` 新增 `visit_events`
- `build_genios_context_package` 自动读取 session 的 visit event timeline
- `GET /api/genios/context/{session_id}` 返回参观事件流水
- `GET /api/genios/handoff/{session_id}` 的 `context` 中同步包含参观事件流水
- 新增 GeniOS context/handoff 测试断言
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `62 passed`

设计决定：

- GeniOS context 现在同时包含 Visitor State 当前快照与 visit event timeline。
- 事件流水只作为结构化连续参观上下文，不生成讲解文本，不推断游客画像。
- Handoff 通过复用 context 自动包含事件流水，避免 GeniOS 多次调用。

### 阶段 31：参观总结包含事件流水

已完成：

- `VisitSummary` 新增 `visit_events`
- `build_visit_summary` 自动读取 session 的 visit event timeline
- `GET /api/visits/{session_id}/summary` 返回参观事件流水
- Handoff 中的 `visit_summary` 同步包含事件流水
- 新增 Visit Summary 测试断言
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `62 passed`

设计决定：

- Visit Summary 现在包含已访问展品列表和事件流水两种结构化参观过程视角。
- Summary 仍不生成自然语言回顾；GeniOS 可基于该结构化数据生成 grounded recap。
- 事件流水不用于推断游客画像，只用于参观过程连续性。

### 阶段 32：Visitor State 与事件流水一致性报告

已完成：

- 新增 Visitor State integrity report schema
- 新增 `get_visitor_state_integrity_report` 服务函数
- 新增 `GET /api/visitor-states/integrity-report`
- 报告 session 总数、visit event 总数、有事件流水的 session 数量、issue 数量
- 检查最新事件展品是否与 `current_exhibit` 一致
- 检查事件流水中的展品是否缺失于 `visited_history`
- 检查存在 `visited_history` 但没有事件流水的 session
- 将 integrity report 加入 GeniOS capabilities
- 新增一致性报告测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `64 passed`

设计决定：

- integrity report 用于联调和运维巡检，帮助发现 Visitor State 快照与扫码/入展事件流水是否脱节。
- 该接口不修复数据、不推断游客意图、不生成行为画像。
- 正常参观事件 POST 仍会同时更新状态快照和写入事件流水。

### 阶段 33：单会话 Visitor State 一致性报告

已完成：

- `get_visitor_state_integrity_report` 支持按 `session_id` 过滤
- 新增 `GET /api/visitor-states/{session_id}/integrity`
- 单会话报告复用全局一致性检查规则
- session 不存在时返回 `404`
- 将单会话 integrity endpoint 加入 GeniOS capabilities
- 新增单会话一致性报告测试
- 更新 OpenAPI 合同测试
- 更新 API 契约、本地演示流程、运行准备、MVP handoff 和 README

验证结果：

- `pytest` 通过，结果为 `66 passed`
- 运行态创建 `session-integrity-smoke-20260922202703`
- `POST /api/visitor-states/{session_id}/visit-events` 成功写入事件
- `GET /api/visitor-states/{session_id}/integrity` 返回 `issue_count=0`
- 运行态 smoke 后已关闭服务，端口 `8033` 无残留

设计决定：

- 单会话 integrity endpoint 用于前端恢复、GeniOS handoff 前检查和真实参观联调。
- 该接口只检查结构化状态与事件流水是否一致，不修复数据、不推断游客意图、不生成讲解文本。
- 全局 integrity report 保留用于运维巡检；单会话 endpoint 用于当前活跃参观 session 的轻量检查。

### 阶段 34：参观事件流水分页读取

已完成：

- `list_visit_events` 支持 `limit` 和 `offset`
- `GET /api/visitor-states/{session_id}/visit-events` 支持可选分页参数
- 默认不传分页参数时仍返回完整 session 事件流水
- OpenAPI 合同测试确认 GET visit-events 暴露 `session_id`、`limit`、`offset`
- 新增 visit event timeline 分页测试
- 更新 GeniOS capabilities、README、API 契约、本地演示流程、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `67 passed`
- 运行态创建 `timeline-page-smoke-20260922203250`
- 写入 3 条 visit event
- `GET /api/visitor-states/{session_id}/visit-events?limit=1&offset=1` 返回第二条事件 `fixture-exhibit-002`
- 运行态 smoke 后已关闭服务，端口 `8034` 无残留

设计决定：

- 分页能力用于真实参观事件流水变长后的 Web/H5 回放和 GeniOS 聚焦读取。
- 默认读取全量事件的行为保持不变，避免影响 GeniOS context、handoff 和 visit summary 当前调用。
- 该能力只处理结构化参观过程数据，不推断游客意图、不生成行为画像、不生成讲解文本。

### 阶段 35：GeniOS 预检包

已完成：

- 新增 `GeniosPreflightCheck` 和 `GeniosPreflightPackage`
- 新增 `build_genios_preflight_package`
- 新增 `GET /api/genios/preflight/{session_id}`
- 预检包汇总展品引用、Visitor State integrity、visit event timeline 和推荐候选可用性
- `ready_for_handoff` 在存在 fail 检查时为 `false`
- 将 GeniOS preflight endpoint 加入 capabilities
- 新增 preflight ready、preflight missing-reference 和 404 测试
- 更新 OpenAPI 合同测试
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `70 passed`
- 运行态创建 `genios-preflight-smoke-20260922203927`
- 写入 1 条 visit event
- `GET /api/genios/preflight/{session_id}` 返回 `ready_for_handoff=true`
- preflight 四项检查均为 `pass`
- 运行态 smoke 后已关闭服务，端口 `8035` 无残留

设计决定：

- preflight 用于 GeniOS handoff 前的结构化 readiness 检查。
- 缺失展品引用或 Visitor State/事件流水结构漂移视为 fail；无事件或无推荐候选视为 warn。
- 该接口只返回结构化检查结果，不执行 RAG、不调用大模型、不生成讲解文本。

### 阶段 36：GeniOS Handoff 包含预检结果

已完成：

- `GeniosHandoffPackage` 新增 `preflight`
- `build_genios_handoff_package` 自动组装 `GeniosPreflightPackage`
- handoff 响应现在包含 preflight、context、route_plan、visit_summary 和 handoff_note
- capabilities 中 handoff 工作流与 endpoint 说明更新为包含 preflight
- 更新 handoff 测试断言
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `70 passed`
- 运行态创建 `handoff-preflight-smoke-20260922204439`
- 写入 1 条 visit event
- `GET /api/genios/handoff/{session_id}` 返回 `preflight.ready_for_handoff=true`
- handoff smoke 同时返回 4 个 preflight checks、1 个 route item、1 条 summary event
- 运行态 smoke 后已关闭服务，端口 `8036` 无残留

设计决定：

- handoff 单次调用即可携带 GeniOS 对接所需的 readiness、上下文、路线和总结结构。
- preflight 单独接口保留，便于前端或 GeniOS 在 handoff 前独立检查。
- 该能力仍只聚合结构化后端数据，不执行 RAG、不调用大模型、不生成讲解文本。

### 阶段 37：GeniOS Grounding 展品 ID

已完成：

- `GeniosContextPackage` 新增 `grounding_exhibit_ids`
- `build_genios_context_package` 输出用于展品级 RAG 的展品 id 种子
- grounding id 来源包括当前展品、已访问展品和推荐候选展品
- grounding id 会去重，并排除缺失展品引用
- Handoff 通过 context 自动包含 `grounding_exhibit_ids`
- capabilities integration notes 提醒 GeniOS 使用 `grounding_exhibit_ids`
- 新增 context、handoff 和 missing-reference 测试断言
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `70 passed`
- 运行态创建 `grounding-smoke-20260922205024`
- 写入 1 条 visit event
- `GET /api/genios/context/{session_id}` 返回 `grounding_exhibit_ids=[fixture-exhibit-001, fixture-exhibit-002]`
- `GET /api/genios/handoff/{session_id}` 的 context 中同步返回同样 grounding ids
- 运行态 smoke 后已关闭服务，端口 `8037` 无残留

设计决定：

- grounding ids 是 GeniOS 展品级 RAG 的结构化检索种子。
- 后端只提供展品 id，不生成历史讲解内容，不判断历史事实。
- 输出顺序以当前展品、已访问历史、推荐候选为基础，尽量贴近真实参观上下文。

### 阶段 38：GeniOS Grounding 包

已完成：

- 新增 `GeniosGroundingPackage`
- 新增 `build_genios_grounding_package`
- 新增 `GET /api/genios/grounding/{session_id}`
- grounding 包根据 `grounding_exhibit_ids` 返回对应展品记录
- grounding 包返回去重后的 `source_references`
- grounding 包保留 `missing_exhibit_ids` 和 collaboration contract
- 将 grounding endpoint 加入 GeniOS capabilities
- 新增 grounding package 和 404 测试
- 更新 OpenAPI 合同测试
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff

验证结果：

- `pytest` 通过，结果为 `72 passed`
- 运行态创建 `grounding-package-smoke-20260924151854`
- 写入 1 条 visit event
- `GET /api/genios/grounding/{session_id}` 返回 `grounding_exhibit_ids=[fixture-exhibit-001, fixture-exhibit-002]`
- grounding 包返回展品记录 `fixture-exhibit-001`、`fixture-exhibit-002`
- grounding 包返回 1 条去重后的 source reference，`missing_exhibit_ids=[]`
- 运行态 smoke 后已关闭服务，端口 `8038` 无残留

设计决定：

- grounding 包用于 GeniOS 展品级 RAG 准备，帮助 GeniOS 根据结构化展品记录和来源引用做后续检索。
- 后端不检索知识库段落、不判断历史准确性、不生成讲解文本。
- 该接口复用 context 的 grounding id 逻辑，避免 GeniOS 多处自行拼接展品上下文。

### 阶段 39：GeniOS Grounding 来源完整性

已完成：

- `GeniosGroundingPackage` 新增 `source_reference_count`
- `GeniosGroundingPackage` 新增 `sourced_exhibit_ids`
- `GeniosGroundingPackage` 新增 `unsourced_exhibit_ids`
- `GeniosGroundingPackage` 新增 `grounding_sources_complete`
- `GET /api/genios/grounding/{session_id}` 现在返回 grounding 展品来源覆盖状态
- `GET /api/genios/preflight/{session_id}` 新增 `grounding_source_references` 检查
- 当 grounding 展品缺少 `source_reference` 时，preflight 将该检查标记为 `fail`，且 `ready_for_handoff=false`
- GeniOS capabilities 增加 `grounding_sources_complete` 集成提示
- 新增未来源 grounding 展品测试场景
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff 文档

验证结果：

- `pytest` 通过，结果为 `73 passed, 2 warnings`
- 运行态创建 `grounding-source-smoke-20260924153807`
- 写入 1 条 visit event
- `GET /api/genios/grounding/{session_id}` 返回 `grounding_exhibit_ids=[fixture-exhibit-001, fixture-exhibit-002]`
- grounding 包返回 `source_reference_count=1`、`grounding_sources_complete=true`、`unsourced_exhibit_ids=[]`
- `GET /api/genios/preflight/{session_id}` 返回 `ready_for_handoff=true`
- preflight 五项检查均为 `pass`：`exhibit_references`、`grounding_source_references`、`visitor_state_integrity`、`visit_event_timeline`、`recommendations`
- 运行态 smoke 后已关闭服务，端口 `8039` 无残留

设计决定：

- Grounding 来源完整性用于 GeniOS 生成前的事实安全检查。
- 后端只报告来源覆盖状态，不检索知识库段落、不判断历史准确性、不生成讲解文本。
- 导入流程仍要求真实展品带有 `source_reference`；新增检查主要用于发现旧数据、人工写入数据或迁移数据中的来源缺口。

### 阶段 40：GeniOS Handoff 来源安全汇总

已完成：

- 新增 `GeniosSourceSafetySummary`
- `GeniosHandoffPackage` 顶层新增 `source_safety`
- `source_safety` 返回 `ready_for_generation`
- `source_safety` 返回 `grounding_sources_complete`
- `source_safety` 返回 `source_reference_count`
- `source_safety` 返回 `sourced_exhibit_ids`
- `source_safety` 返回 `unsourced_exhibit_ids`
- `source_safety` 返回 `missing_exhibit_ids`
- `source_safety` 返回 `blocking_check_names`
- `source_safety` 返回 `safety_note`
- Handoff 现在在单次响应中同时提供来源安全汇总、preflight、context、route plan 和 visit summary
- 新增 ready handoff source-safety 测试
- 新增 unsourced grounding handoff source-safety 测试断言
- 更新 README、API 契约、本地演示流程、运行准备和 MVP handoff 文档

验证结果：

- `pytest` 通过，结果为 `74 passed, 2 warnings`
- 运行态创建 `handoff-source-safety-smoke-20260924155338`
- 写入 1 条 visit event
- `GET /api/genios/handoff/{session_id}` 返回顶层 `source_safety`
- `source_safety.ready_for_generation=true`
- `source_safety.grounding_sources_complete=true`
- `source_safety.source_reference_count=1`
- `source_safety.unsourced_exhibit_ids=[]`
- `source_safety.blocking_check_names=[]`
- `preflight.ready_for_handoff=true`
- 运行态 smoke 后已关闭服务，端口 `8040` 无残留

设计决定：

- `source_safety` 是 GeniOS 生成前的顶层决策摘要，减少 GeniOS 或 Web/H5 对多个 preflight checks 的脆弱解析。
- `ready_for_generation` 只表示结构化后端上下文和来源状态可进入生成，不表示后端生成内容。
- 后端仍不执行 RAG、不调用大模型、不生成讲解文本；GeniOS 仍负责知识检索与最终讲解生成。

### 阶段 41：Web/H5 与 GeniOS 集成调用顺序文档

已完成：

- 新增 `docs/web_h5_genios_integration.md`
- 文档明确 Web/H5、FastAPI 后端、GeniOS 的职责边界
- 文档覆盖运行设置：`HISTORYGUIDE_CORS_ORIGINS`、`HISTORYGUIDE_API_KEY`、`X-HistoryGuide-Api-Key`
- 文档覆盖参观前数据检查：`/ready`、数据库状态、source report、quality report、capabilities
- 文档覆盖真实参观主流程：
  - `POST /api/visitor-states`
  - `POST /api/visitor-states/{session_id}/visit-events`
  - `GET /api/genios/context/{session_id}`
  - `GET /api/genios/grounding/{session_id}`
  - `GET /api/genios/preflight/{session_id}`
  - `GET /api/genios/handoff/{session_id}`
  - `GET /api/visits/{session_id}/summary`
- 文档强调 GeniOS 生成前必须检查 `source_safety.ready_for_generation=true`
- 文档列出 missing session、missing exhibit、unsourced grounding exhibit、Visitor State integrity failure 的处理建议
- 文档再次明确后端不生成讲解、不扩展为普通校史聊天机器人、不做数字人/AR/VR
- README 新增文档入口
- 运行准备文档新增集成文档说明和 checklist
- MVP handoff 文档新增集成文档说明
- 新增 `tests/test_documentation_contract.py`
- 文档契约测试确认 README 引用集成文档，并确认文档包含真实参观链路关键 API 与边界说明

验证结果：

- `tests/test_documentation_contract.py` 通过，结果为 `2 passed`
- `pytest` 通过，结果为 `76 passed, 2 warnings`
- 本阶段为文档与契约测试增强，未启动运行态服务

设计决定：

- 集成顺序文档用于指导 Web/H5 与 GeniOS 对接，不实现 Web/H5 页面、不编写 GeniOS Prompt、不执行 RAG。
- 默认推荐 GeniOS 使用 handoff 单次调用，并以 `source_safety.ready_for_generation` 作为生成前结构化安全门禁。
- 真实展品历史内容仍必须来自经核验资料和 GeniOS 知识库，后端不编造、不补写、不生成历史讲解。

### 阶段 42：真实展品 Seed 接入前审核清单

已完成：

- 新增 `docs/real_exhibit_seed_review.md`
- 审核清单明确 Codex 和后端只能做结构校验、来源字段检查、元数据完整性报告、来源分组报告和 grounding/source-safety 检查
- 审核清单明确 Codex 和后端不能编造展品描述、补写历史事实、替代馆方或专家审核、生成讲解文本、训练模型
- 审核清单覆盖每条真实展品记录导入前所需 source package
- 审核清单覆盖 seed 文件字段要求和人工审核要点
- 审核清单覆盖 dry-run gate：`python scripts\import_exhibits.py --dry-run <seed-file>`
- 审核清单覆盖导入前备份：`python scripts\export_exhibits.py <backup-file>`
- 审核清单覆盖导入后检查：`/ready`、source report、quality report、facets、capabilities
- 审核清单覆盖 GeniOS grounding/handoff 生成前检查：`grounding_sources_complete`、`unsourced_exhibit_ids`、`missing_exhibit_ids`、`source_safety.ready_for_generation`
- 审核清单列出 seed 文件应拒绝或暂缓导入的条件
- README 新增审核清单入口
- `docs/exhibit_seed_format.md` 新增真实展品导入前审核清单提示
- 运行准备文档新增审核清单说明和 readiness checklist
- MVP handoff 文档新增审核清单说明
- `tests/test_documentation_contract.py` 扩展审核清单契约测试

验证结果：

- `tests/test_documentation_contract.py` 通过，结果为 `3 passed`
- `pytest` 通过，结果为 `77 passed, 2 warnings`
- 本阶段为文档与契约测试增强，未启动运行态服务

设计决定：

- 真实展品 seed 接入前必须先经过人工来源审核和 dry-run；dry-run 只代表结构可导入，不代表历史准确性已被后端验证。
- 后端只负责保留和检查 `source_reference` 等结构化证据链，不判断来源质量、不生成缺失事实。
- GeniOS 生成前仍需依赖 grounding 与 handoff 的 source-safety 信号，特别是 `source_safety.ready_for_generation=true`。

### 阶段 43：生产化准备说明

已完成：

- 新增 `docs/production_hardening.md`
- 生产化说明明确当前已验证状态：FastAPI 启动、health/ready、SQLite MVP、可选 API key、CORS allowlist、导入 dry-run、导出、source/quality report、GeniOS context/grounding/preflight/handoff
- 生产化说明明确尚未完成的生产能力：正式迁移、PostgreSQL staging 验证、备份恢复自动化、托管 secrets、角色权限、集中日志监控、GeniOS 生产 RAG、Web/H5 生产体验
- 生产化说明覆盖环境变量门禁：`HISTORYGUIDE_API_KEY`、`HISTORYGUIDE_CORS_ORIGINS`、`HISTORYGUIDE_DATABASE_URL`
- 生产化说明覆盖部署前检查：`pytest`、`/health`、`/ready`、`/api/system/database`、`/openapi.json`
- 生产化说明覆盖数据备份门禁：`python scripts\export_exhibits.py backups\exhibits.before-change.json`
- 生产化说明明确 SQLite 的适用边界和不适用场景
- 生产化说明新增 PostgreSQL Migration Gate，强调不能只改 `HISTORYGUIDE_DATABASE_URL`
- 生产化说明覆盖 API key 检查、CORS 检查、运行监控 checklist、回滚 checklist
- 生产化说明保持边界：不训练模型、不替代 GeniOS、不执行 RAG、不生成讲解、不做数字人/AR/VR
- README 新增生产化说明入口
- `docs/deployment.md` 新增生产化说明链接和 PostgreSQL 边界提示
- 运行准备文档新增生产化说明入口和 checklist
- MVP handoff 文档新增生产化说明入口
- `tests/test_documentation_contract.py` 扩展生产化说明契约测试

验证结果：

- `tests/test_documentation_contract.py` 通过，结果为 `4 passed`
- `pytest` 通过，结果为 `78 passed, 2 warnings`
- 本阶段为文档与契约测试增强，未启动运行态服务

设计决定：

- 当前仍不声明完整生产系统完成；生产化说明只定义进入 shared/public/production-like 环境前必须补齐和验证的门禁。
- PostgreSQL 仍是迁移目标，不是仅通过数据库 URL 切换即可完成的生产能力。
- 生产化硬化聚焦后端运行、数据安全、备份回滚、API key、CORS 与监控，不扩展到大模型训练、GeniOS Prompt、数字人、AR/VR 或大型前端。

### 阶段 44：GeniOS Handoff 示例响应增强

已完成：

- `docs/api_contract.md` 的 GeniOS Handoff 部分新增完整 ready handoff response 示例
- 示例使用非历史 fixture 数据，避免伪造南开校史事实
- 示例覆盖顶层 `source_safety`
- 示例覆盖 `preflight.checks`
- 示例覆盖 `context.visitor_state`
- 示例覆盖 `context.current_exhibit`
- 示例覆盖 `context.visit_events`
- 示例覆盖 `context.recommendations`
- 示例覆盖 `context.grounding_exhibit_ids`
- 示例覆盖 `route_plan.items`
- 示例覆盖 `visit_summary.visit_events`
- 示例覆盖 `handoff_note`
- 示例强调 GeniOS 只有在 `source_safety.ready_for_generation=true` 后才进入生成
- README 新增完整 handoff 示例提示
- `docs/web_h5_genios_integration.md` 新增 API contract 示例引用
- MVP handoff 文档新增完整 handoff 示例说明
- `tests/test_documentation_contract.py` 新增 API contract handoff 示例契约测试

验证结果：

- `tests/test_documentation_contract.py` 通过，结果为 `5 passed`
- `pytest` 通过，结果为 `79 passed, 2 warnings`
- 本阶段为文档与契约测试增强，未启动运行态服务

设计决定：

- 完整 handoff 示例用于 GeniOS/Web/H5 对接验收，不代表后端生成讲解内容。
- 示例只使用非历史 fixture 数据；真实展品对接仍需先通过 `docs/real_exhibit_seed_review.md`。
- GeniOS 仍负责 RAG、知识检索与最终讲解生成；后端只提供结构化上下文、路线、总结与 source-safety 信号。

### 阶段 45：Alembic 迁移脚手架

已完成：

- `requirements.txt` 新增 Alembic 运行依赖
- 新增 `alembic.ini`
- 新增 `migrations/env.py`
- 新增 `migrations/script.py.mako`
- 新增初始迁移 `migrations/versions/0001_initial_schema.py`
- 初始迁移覆盖 `exhibits`、`visitor_states`、`visitor_visit_events` 和当前索引
- `GET /api/system/database` 的 `schema_management` 更新为 `sqlalchemy_create_all_mvp_with_alembic_scaffold`
- `GET /api/system/database` 的 `migration_target` 更新为 `alembic_staging_then_postgresql`
- 新增数据库迁移说明 `docs/database_migrations.md`
- README、API contract、deployment、operational readiness、MVP handoff、production hardening 文档已同步迁移边界
- `tests/test_documentation_contract.py` 新增 Alembic 脚手架与迁移文档契约测试

验证结果：

- `python -m pip install -r requirements-dev.txt` 成功安装 Alembic
- `pytest tests\test_health.py tests\test_documentation_contract.py` 通过，结果为 `10 passed, 2 warnings`
- 使用临时 SQLite 数据库执行 `alembic upgrade head` 成功
- 临时迁移库包含 `alembic_version`、`exhibits`、`visitor_states`、`visitor_visit_events`
- `pytest` 通过，结果为 `81 passed, 2 warnings`

设计决定：

- 本阶段只建立迁移脚手架和初始 schema，不移除本地 MVP 的 SQLAlchemy `create_all` 路径。
- Alembic 是 staging 与未来 PostgreSQL 生产化路径；仅切换 `HISTORYGUIDE_DATABASE_URL` 仍不代表生产就绪。
- PostgreSQL 生产使用前仍需 staging 迁移验证、真实展品备份、source/quality report、GeniOS grounding/preflight/handoff 检查。

### 阶段 46：结构化审计日志

已完成：

- 新增 `AuditLog` SQLAlchemy 模型
- 新增 `GET /api/audit-logs`
- 新增 `audit_log_service`
- 新增审计日志 schema
- 新增 Alembic 迁移 `migrations/versions/0002_audit_logs.py`
- `audit_logs` 表记录 `action`、`resource_type`、`resource_id`、`actor`、`details`、`created_at`
- 审计日志接口支持 `action`、`resource_type`、`resource_id`、`actor`、`limit`、`offset`
- Visitor State 创建会写入 `visitor_state_created`
- Visitor State 更新会写入 `visitor_state_updated`
- 参观事件记录会写入 `visit_event_recorded`
- 展品 seed 成功导入会写入 `exhibits_imported`
- README、API contract、operational readiness、MVP handoff、database migrations 文档已同步
- OpenAPI 契约测试加入 `/api/audit-logs` 和 `audit-logs` tag
- 新增 `tests/test_audit_logs.py`
- 文档契约测试覆盖审计日志 API 边界与 `0002_audit_logs` 迁移

验证结果：

- `pytest tests\test_documentation_contract.py tests\test_openapi_contract.py tests\test_audit_logs.py` 通过，结果为 `14 passed, 2 warnings`
- 使用临时 SQLite 数据库执行 `alembic upgrade head` 成功，依次运行 `0001_initial_schema` 和 `0002_audit_logs`
- 临时迁移库包含 `audit_logs` 和相关索引
- `pytest` 通过，结果为 `85 passed, 2 warnings`

设计决定：

- 审计日志用于真实参观状态变更和真实展品导入后的运维追踪，不用于游客画像推断。
- 审计日志不执行 RAG、不判断历史准确性、不生成讲解内容。
- 当前审计范围只覆盖关键状态变更和导入汇总，保持后端职责聚焦。

### 阶段 47：审计日志监控摘要

已完成：

- 新增 `GET /api/audit-logs/stats`
- 新增 `AuditLogStats` 和 `AuditLogCountItem` schema
- 新增 `get_audit_log_stats`
- stats 返回 `total_logs`、`actions`、`resource_types`、`actors`、`latest_created_at`
- OpenAPI 契约测试加入 `/api/audit-logs/stats`
- `tests/test_audit_logs.py` 新增空审计摘要和状态变更摘要测试
- README、API contract、operational readiness、MVP handoff 文档已同步
- 文档契约测试覆盖 audit log stats API

验证结果：

- `pytest tests\test_documentation_contract.py tests\test_openapi_contract.py tests\test_audit_logs.py` 通过，结果为 `16 passed, 2 warnings`
- `pytest` 通过，结果为 `87 passed, 2 warnings`

设计决定：

- 审计统计只做轻量运维摘要，用于 demo、staging 和监控交接。
- 统计项不推断游客画像，不判断历史事实，不生成讲解内容。
- 该能力服务生产化可观测性，不改变 GeniOS 负责 RAG 与内容生成的边界。

### 阶段 48：运营告警汇总

已完成：

- 新增 `GET /api/system/operational-alerts`
- 新增 `OperationalAlert` 和 `OperationalAlertsResponse` schema
- 新增 `operational_alert_service`
- operational alerts 汇总空展品数据、未来源展品、展品元数据缺口、Visitor State/visit event 漂移、审计日志缺失
- 告警分为 `warn` 和 `fail`
- OpenAPI 契约测试加入 `/api/system/operational-alerts`
- 新增 `tests/test_operational_alerts.py`
- README、API contract、operational readiness、MVP handoff 文档已同步
- 文档契约测试覆盖 operational alerts API 边界

验证结果：

- `pytest tests\test_operational_alerts.py tests\test_openapi_contract.py tests\test_documentation_contract.py` 通过，结果为 `15 passed, 2 warnings`
- `pytest` 通过，结果为 `91 passed, 2 warnings`

设计决定：

- 运营告警用于 demo、staging 和 GeniOS handoff 前的后端 readiness 汇总。
- 告警只基于结构化后端状态，不判断历史事实、不执行 RAG、不生成讲解内容。
- 该接口在配置 API Key 时属于受保护业务 API，不加入公开探针路径。

### 阶段 49：Operator API Key 保护

已完成：

- 新增 `HISTORYGUIDE_OPERATOR_API_KEY`
- 新增请求头 `X-HistoryGuide-Operator-Key`
- 审计日志接口 `/api/audit-logs` 和 `/api/audit-logs/stats` 可由 operator key 单独保护
- 运营告警接口 `/api/system/operational-alerts` 可由 operator key 单独保护
- 同时配置 `HISTORYGUIDE_API_KEY` 和 `HISTORYGUIDE_OPERATOR_API_KEY` 时：
  - 普通业务 API 要求 `X-HistoryGuide-Api-Key`
  - 审计和运营 API 要求 `X-HistoryGuide-Operator-Key`
  - 普通业务 key 不替代 operator key
- `.env.example` 已新增 operator key 配置
- README、API contract、deployment、operational readiness、production hardening、MVP handoff 文档已同步
- 配置测试、安全测试和文档契约测试已覆盖 operator key 边界

验证结果：

- `pytest tests\test_config.py tests\test_security.py tests\test_documentation_contract.py` 通过，结果为 `19 passed, 2 warnings`
- `pytest` 通过，结果为 `95 passed, 2 warnings`

设计决定：

- Operator key 是轻量运维接口保护，不是完整 RBAC 或用户账号系统。
- 本地 demo 默认不配置 operator key，保持低摩擦。
- 共享或生产化环境暴露审计/运营接口时建议配置独立 operator key，且不复用普通业务 API key。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run 和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 阶段 52：离线展品备份校验脚本

已完成：

- 新增 `scripts/verify_exhibit_backup.py`
- 新增 `tests/test_verify_exhibit_backup.py`
- 备份校验脚本不连接数据库
- 备份校验脚本不导入记录
- 备份校验脚本复用展品 seed 结构校验：
  - JSON 顶层必须是数组
  - 记录必须符合 Exhibit schema
  - 展品 ID 不能重复
  - `source_reference` 必须非空
- 新增 `--require-non-empty` 参数，用于真实备份恢复或迁移前防止空备份误用
- README、deployment、production hardening、operational readiness、real exhibit seed review、MVP handoff 文档已同步
- 文档契约测试覆盖备份校验说明

验证结果：

- `pytest tests\test_verify_exhibit_backup.py` 通过，结果为 `4 passed`
- `pytest tests\test_verify_exhibit_backup.py tests\test_documentation_contract.py` 通过，结果为 `17 passed`
- `pytest` 通过，结果为 `109 passed, 2 warnings`
- 更新测试数后，`pytest tests\test_documentation_contract.py` 通过，结果为 `13 passed`
- 实际运行 `python scripts\verify_exhibit_backup.py data\example_exhibits.fixture.json --require-non-empty` 通过，输出 `Verified 2 exhibit records in backup file. No database changes were made.`

设计决定：

- 备份校验服务真实展品数据迁移、恢复演练和生产化前数据安全检查。
- 校验只证明文件结构、字段、重复 ID 和来源引用存在，不证明历史准确性。
- 校验不导入展品、不写数据库、不修改 Visitor State、不写审计日志。
- 该能力属于数据管理和生产硬化，不改变 GeniOS 负责对话、RAG、知识检索和内容生成的边界。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、安全配置状态接口、只读部署自检脚本、离线展品备份校验脚本、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run、备份校验和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如要继续生产硬化，可补充更细的备份/恢复演练文档或集中日志接入说明。
4. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 最新阶段索引：阶段 54 为当前最新状态

当前最新完成项：

- `app/core/request_context.py` 请求 ID 追踪中间件已完成。
- 每个响应返回 `X-HistoryGuide-Request-Id`。
- API key 失败响应也返回 request id，便于联调排障。
- request id 用于日志关联，不是认证、访客身份、历史证据或游客画像来源。
- README、API contract、Web/H5 and GeniOS integration、production hardening、operational readiness、MVP handoff 已同步。
- 最新全量测试结果为 `119 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择，不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 54 为当前最新状态

当前最新完成项：

- `app/core/request_context.py` 请求 ID 追踪中间件已完成。
- 每个响应返回 `X-HistoryGuide-Request-Id`。
- API key 失败响应也返回 request id，便于联调排障。
- request id 用于日志关联，不是认证、访客身份、历史证据或游客画像来源。
- README、API contract、Web/H5 and GeniOS integration、production hardening、operational readiness、MVP handoff 已同步。
- 最新全量测试结果为 `119 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择，不要做大模型训练、数字人、AR/VR 或无关功能。

### 阶段 54：请求 ID 追踪与轻量请求日志

已完成：

- 新增 `app/core/request_context.py`
- 新增请求头常量 `X-HistoryGuide-Request-Id`
- 新增 request context 中间件：
  - 接受合法的调用方 request id
  - 对缺失或非法 request id 自动生成 UUID
  - 在每个响应中返回 `X-HistoryGuide-Request-Id`
  - 写入轻量 request completed 日志，包含 request id、method、path、status_code、elapsed_ms
- request id 中间件包住 API key 失败响应，401 响应也返回 request id
- 新增 `tests/test_request_context.py`
- README、API contract、Web/H5 and GeniOS integration、production hardening、operational readiness、MVP handoff 文档已同步
- 文档契约测试覆盖 request id 边界

验证结果：

- `pytest tests\test_request_context.py tests\test_security.py` 通过，结果为 `14 passed, 2 warnings`
- `pytest tests\test_request_context.py tests\test_documentation_contract.py` 通过，结果为 `19 passed, 2 warnings`
- `pytest` 通过，结果为 `119 passed, 2 warnings`
- 更新测试数后，`pytest tests\test_documentation_contract.py` 通过，结果为 `15 passed`

设计决定：

- request id 用于 Web/H5、GeniOS、operator 工具、后端日志和托管平台日志之间的排障关联。
- request id 不是认证信息、不是访客身份、不是历史证据、不是游客画像来源。
- request id 不参与 RAG、不进入讲解生成、不改变 Visitor State 数据模型。
- 该能力属于生产化可观测性和联调辅助，不改变 GeniOS 负责对话、RAG、知识检索和内容生成的边界。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、安全配置状态接口、请求 ID 追踪与轻量请求日志、只读部署自检脚本、离线展品备份校验脚本、隔离展品恢复演练脚本、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run、备份校验、恢复演练和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如要继续生产硬化，可补充集中日志接入说明、错误响应统一说明或更细的恢复/回滚演练文档。
4. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 最新阶段索引：阶段 54 为当前最新状态

当前最新完成项：

- `app/core/request_context.py` 请求 ID 追踪中间件已完成。
- 每个响应返回 `X-HistoryGuide-Request-Id`。
- API key 失败响应也返回 request id，便于联调排障。
- request id 用于日志关联，不是认证、访客身份、历史证据或游客画像来源。
- README、API contract、Web/H5 and GeniOS integration、production hardening、operational readiness、MVP handoff 已同步。
- 最新全量测试结果为 `119 passed, 2 warnings`。

### 阶段 51：只读部署自检脚本

已完成：

- 新增 `scripts/deployment_self_check.py`
- 自检脚本使用 Python 标准库，不新增依赖
- 支持参数：
  - `--base-url`
  - `--api-key`
  - `--operator-key`
  - `--timeout`
- 支持从环境变量读取：
  - `HISTORYGUIDE_BASE_URL`
  - `HISTORYGUIDE_API_KEY`
  - `HISTORYGUIDE_OPERATOR_API_KEY`
- 自检脚本调用只读接口：
  - `GET /health`
  - `GET /ready`
  - `GET /api/system/database`
  - `GET /openapi.json`
  - `GET /api/system/security-status`
  - `GET /api/system/operational-alerts`
- 自检脚本不会写入数据库
- 自检脚本不会打印配置的 key 值
- operator 检查优先使用 `X-HistoryGuide-Operator-Key`
- 仅有业务 key 时，operator 检查回退使用 `X-HistoryGuide-Api-Key`，适配未配置独立 operator key 的环境
- 新增 `tests/test_deployment_self_check.py`
- README、deployment、production hardening、operational readiness、MVP handoff 文档已同步
- 文档契约测试覆盖只读部署自检说明

验证结果：

- `pytest tests\test_deployment_self_check.py` 通过，结果为 `4 passed`
- `pytest tests\test_deployment_self_check.py tests\test_documentation_contract.py` 通过，结果为 `16 passed`
- `pytest` 通过，结果为 `104 passed, 2 warnings`
- 更新测试数后，`pytest tests\test_documentation_contract.py` 通过，结果为 `12 passed`

设计决定：

- 部署自检脚本服务 staging、demo 和真实联调前的运行时核验。
- 脚本只读取后端状态，不导入展品、不修改 Visitor State、不写审计日志。
- 脚本不检查历史准确性、不执行 RAG、不生成讲解内容。
- 该能力属于生产化与运维交接增强，不改变 GeniOS 负责对话、RAG、知识检索和内容生成的边界。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、安全配置状态接口、只读部署自检脚本、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run 和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如要继续生产硬化，可补充更细的备份/恢复演练文档或集中日志接入说明。
4. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 阶段 50：安全配置状态接口

已完成：

- 新增 `GET /api/system/security-status`
- 新增 `SecurityStatusResponse` schema
- 新增 `app/core/security.py` 统一维护公开探针路径、业务 API Key 请求头、Operator API Key 请求头、operator 路径
- `main.py` 中间件改为复用统一 security 常量
- `create_app()` 将运行时 settings 写入 `app.state.settings`
- security status 从当前 app 实例读取运行时配置，避免测试或部署实例配置和接口展示不一致
- security status 返回：
  - `business_api_key_configured`
  - `operator_api_key_configured`
  - `business_apis_require_api_key`
  - `operator_apis_require_operator_key`
  - 请求头名称
  - public probe paths
  - operator paths 和 operator path prefixes
- security status 不返回任何密钥值
- 配置 `HISTORYGUIDE_OPERATOR_API_KEY` 时，`GET /api/system/security-status` 要求 `X-HistoryGuide-Operator-Key`
- 仅配置 `HISTORYGUIDE_API_KEY` 时，`GET /api/system/security-status` 要求 `X-HistoryGuide-Api-Key`
- OpenAPI 契约测试加入 `/api/system/security-status`
- 安全测试覆盖默认状态、业务 key 保护、operator key 保护、密钥不泄露
- README、API contract、deployment、operational readiness、production hardening、MVP handoff 文档已同步
- 文档契约测试覆盖 security status 边界

验证结果：

- `pytest tests\test_security.py tests\test_openapi_contract.py tests\test_documentation_contract.py` 通过，结果为 `24 passed, 2 warnings`
- `pytest` 通过，结果为 `99 passed, 2 warnings`

设计决定：

- security status 用于部署核验、staging 检查、Web/H5 与 GeniOS 联调前的安全配置可见性。
- security status 不是完整 RBAC、不是用户账号系统、不暴露密钥值。
- security status 不检查历史准确性、不执行 RAG、不生成讲解内容。
- 该能力继续服务真实参观场景后端生产化，不改变 GeniOS 负责对话、RAG、知识检索和内容生成的边界。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、安全配置状态接口、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run 和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如要继续生产硬化，可补充更细的备份/恢复演练文档或集中日志接入说明。
4. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 阶段 53：隔离展品恢复演练脚本

已完成：

- 新增 `scripts/rehearse_exhibit_restore.py`
- 新增 `tests/test_rehearse_exhibit_restore.py`
- 恢复演练脚本将备份导入隔离的 in-memory SQLite 数据库
- 恢复演练脚本不使用、不修改配置的应用数据库
- 恢复演练脚本导入后运行展品来源报告和质量报告
- 恢复演练脚本会检查导入数量和恢复数量一致
- 默认拒绝导入 0 条记录的备份
- 支持 `--allow-empty` 用于明确允许空备份的特殊场景
- README、deployment、production hardening、operational readiness、real exhibit seed review、MVP handoff 文档已同步
- 文档契约测试覆盖恢复演练说明

验证结果：

- `pytest tests\test_rehearse_exhibit_restore.py` 通过，结果为 `4 passed`
- `pytest tests\test_rehearse_exhibit_restore.py tests\test_verify_exhibit_backup.py tests\test_documentation_contract.py` 通过，结果为 `22 passed`
- `pytest` 通过，结果为 `114 passed, 2 warnings`
- 实际运行 `python scripts\rehearse_exhibit_restore.py data\example_exhibits.fixture.json` 通过，输出 `Restore rehearsal passed: imported=2, sourced=2, unsourced=0, quality_issue_count=2. No configured database changes were made.`

设计决定：

- 恢复演练服务真实展品数据恢复、重置、迁移和环境搬迁前的数据安全检查。
- 恢复演练只验证当前后端模型可以恢复备份记录，不证明历史准确性。
- 恢复演练不修改真实数据库、不修改 Visitor State、不写真实审计日志。
- 该能力属于数据管理和生产硬化，不改变 GeniOS 负责对话、RAG、知识检索和内容生成的边界。

## 当前工程边界

后端 MVP 主链路已经完成，并已补充参观事件记录与事件流水分页读取、Visitor State 列表查询、统计、全局与单会话一致性报告、结构化审计日志与监控摘要、运营告警汇总、安全配置状态接口、只读部署自检脚本、离线展品备份校验脚本、隔离展品恢复演练脚本、GeniOS 能力发现、GeniOS 预检包、GeniOS grounding 展品 ID、grounding 包与来源完整性检查、handoff 来源安全汇总、handoff 完整示例响应、Web/H5 与 GeniOS 集成调用顺序文档、真实展品 seed 接入前审核清单、生产化准备说明、Alembic 迁移脚手架、数据库迁移说明、包含预检结果和事件流水的结构化交接包、包含事件流水和 grounding ids 的上下文包、包含事件流水的结构化参观总结、规则化参观路线规划、展品列表分页、展品元数据 facets、展品数据质量报告、展品来源追踪报告、Web/H5 CORS 集成准备、可选业务 API Key 保护、可选 Operator API Key 保护、展品导入来源校验、导入 dry-run、展品导出备份、部署 readiness 和数据库状态可见性能力。

仍需外部或后续集成：

- 真实校史馆展品数据
- GeniOS Agent、Prompt、RAG 与内容生成
- Web/H5 体验
- 生产托管细节与生产硬化

## 下一步期望

下一阶段建议根据项目需要选择集成方向。

可选方向：

1. 接入经核验校史馆展品数据。
2. 与 GeniOS Agent 对接上下文包。
3. 为 Web/H5 提供页面或接口联调。
4. 根据部署环境继续补充生产硬化。
5. 如取得校史馆空间拓扑数据，再增强路线规划精度。
6. 如决定进入生产化，在 staging 验证 Alembic 迁移，并补充角色权限、集中日志或监控告警。

近期后端可继续推进的轻量方向：

1. 如进入真实数据阶段，先根据 `docs/real_exhibit_seed_review.md` 审核 seed 文件，再执行 dry-run、备份校验、恢复演练和导入。
2. 如进入生产化实现阶段，先根据 `docs/database_migrations.md` 在 staging 数据库验证 Alembic 迁移。
3. 如要继续生产硬化，可补充集中日志接入说明或更细的恢复/回滚演练文档。
4. 如取得校史馆空间拓扑数据，再增强路线规划精度；未取得前不做虚构地图导航。

注意：

- 不要在此阶段实现大模型调用。
- 不要开发数字人、AR/VR、复杂前端或无关扩展。
- GeniOS 仍负责对话、RAG、知识检索和内容生成；后端只提供结构化上下文与数据服务。

### 最新阶段索引：阶段 53 为当前最新状态

当前最新完成项：

- `scripts/rehearse_exhibit_restore.py` 隔离展品恢复演练脚本已完成。
- `scripts/verify_exhibit_backup.py` 离线展品备份校验脚本仍可用于文件结构检查。
- `scripts/deployment_self_check.py` 只读部署自检脚本仍可用于运行时部署检查。
- 恢复演练脚本导入到隔离的 in-memory SQLite 数据库，不修改配置的应用数据库。
- 恢复演练脚本检查可恢复记录数、来源报告和质量报告。
- 恢复演练脚本不能证明历史准确性，真实内容仍需校史馆/专家审核。
- README、deployment、production hardening、operational readiness、MVP handoff 已同步。
- 最新全量测试结果为 `114 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择，不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 54 为当前最新状态

当前最新完成项：

- `app/core/request_context.py` 请求 ID 追踪中间件已完成。
- 每个响应返回 `X-HistoryGuide-Request-Id`。
- API key 失败响应也返回 request id，便于联调排障。
- request id 用于日志关联，不是认证、访客身份、历史证据或游客画像来源。
- README、API contract、Web/H5 and GeniOS integration、production hardening、operational readiness、MVP handoff 已同步。
- 最新全量测试结果为 `119 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择，不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 55 为当前最新状态

当前最新完成项：

- `scripts/deployment_self_check.py` 已在每条检查结果中输出返回的 `X-HistoryGuide-Request-Id`。
- 部署自检 request id 仅用于现场排障和日志关联，不是认证、访客身份、历史证据或游客画像来源。
- 部署自检仍然只调用只读端点，不写数据库，不打印业务 API key 或 operator API key。
- README、deployment、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 最新全量测试结果为 `119 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充集中日志字段规范或 staging Alembic 验证记录；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 56 为当前最新状态

当前最新完成项：

- 新增 `HISTORYGUIDE_LOG_FORMAT` 配置，默认 `text`，可设为 `json` 供集中日志平台采集。
- 新增 `JsonLogFormatter`，JSON 日志包含 `event`、`service_id`、`request_id`、`http_method`、`path`、`status_code`、`elapsed_ms` 等稳定字段。
- 请求完成日志继续保留 request id，并额外携带结构化字段，便于 Web/H5、GeniOS、部署自检和后端日志关联。
- 结构化日志字段仅用于运维排障和日志关联，不是认证、访客身份、游客画像、历史证据或 GeniOS prompt 输入。
- README、deployment、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 最新全量测试结果为 `122 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging Alembic 验证记录、角色权限边界说明或集中日志平台接入示例；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 57 为当前最新状态

当前最新完成项：

- 新增 `scripts/rehearse_migrations.py`，默认在隔离临时 SQLite 数据库运行 `alembic upgrade head`。
- 迁移演练会验证当前 Alembic revision 和核心表：`alembic_version`、`exhibits`、`visitor_states`、`visitor_visit_events`、`audit_logs`。
- 迁移演练默认删除临时数据库，可用 `--keep-database` 保留隔离文件供人工检查。
- `migrations/env.py` 支持 Alembic Config 传入的隔离数据库 URL，并保留既有应用 logger，避免迁移演练禁用请求日志。
- 迁移演练不修改配置的应用数据库、不导入记录、不验证真实校史内容、不证明历史准确性，也不代表 PostgreSQL 已生产可用。
- README、database migrations、deployment、production hardening、MVP handoff 和文档契约测试已同步。
- 实际运行 `python scripts\rehearse_migrations.py` 成功，结果为 `revision=0002_audit_logs, tables=5, database=temporary database removed`。
- 最新全量测试结果为 `125 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充角色权限边界说明、集中日志平台接入示例或 staging 实库验证记录；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 58 为当前最新状态

当前最新完成项：

- 新增 `GET /api/system/access-policy`，返回粗粒度访问边界：`public_probe`、`business_api`、`operator_api`、`local_operator_workflow`。
- `access-policy` 不返回配置的 key 值、不授予访问权限，不是用户账号体系或 full RBAC。
- 当 `HISTORYGUIDE_OPERATOR_API_KEY` 已配置时，`access-policy` 和其他 operator endpoint 一样要求 `X-HistoryGuide-Operator-Key`。
- `scripts/deployment_self_check.py` 已纳入 `GET /api/system/access-policy` 只读检查，并输出 request id 方便日志关联。
- README、API contract、deployment、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 最新全量测试结果为 `128 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充集中日志平台接入示例、staging 实库验证记录或真实数据导入前的操作清单；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 59 为当前最新状态

当前最新完成项：

- 新增 `scripts/validate_runtime_config.py` 运行时配置校验脚本，支持 `--profile local|staging|production`。
- 校验项包括 business API key、operator API key、operator key 分离、CORS wildcard 风险、database URL profile 风险、log level、log format。
- 脚本不连接数据库、不打印 secret values，不导入记录，不验证真实校史内容，不调用 GeniOS、不运行 RAG、不生成讲解内容。
- `.env.example` 新增 `HISTORYGUIDE_LOG_FORMAT=text`，与配置模型保持一致。
- README、deployment、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 实际运行 `python scripts\validate_runtime_config.py --profile production` 成功暴露生产配置风险，结果为 fails=3、warnings=3，未打印 secret values。
- 最新全量测试结果为 `133 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充集中日志平台接入示例、staging 实库验证记录或真实数据导入前的操作清单；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 60 为当前最新状态

当前最新完成项：

- 新增 `docs/centralized_logging.md`，说明集中日志平台接入方式、稳定字段、request id 关联流程、建议过滤器和脱敏边界。
- 新增 `docs/examples/structured_request_log.json`，作为 JSON request log 样例。
- 测试已校验样例字段包含 `event`、`service_id`、`request_id`、`http_method`、`path`、`status_code`、`elapsed_ms`。
- README、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 集中日志说明明确：日志字段只用于运维关联，不是认证、访客身份、游客画像、历史证据、source reference、GeniOS prompt input、RAG 内容或生成讲解内容。
- 最新全量测试结果为 `134 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 实库验证记录模板或真实数据导入前的操作清单；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 61 为当前最新状态

当前最新完成项：

- 新增 `docs/staging_validation_record.md`，用于记录 staging 或 production-like 环境验证证据。
- 新增 `docs/examples/staging_validation_record.example.md`，包含占位示例，并明确示例不是 staging 已验证证据。
- 模板覆盖 runtime config、migration、data safety、runtime endpoint、historical content safety、GeniOS handoff、centralized logging 等 gate。
- 模板明确：记录不证明历史准确性、不替代校史馆/专家审核、不训练模型、不运行 RAG、不生成讲解内容。
- README、production hardening、operational readiness、MVP handoff 和文档契约测试已同步。
- 最新全量测试结果为 `135 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充真实数据导入前操作清单、staging 实库验证脚本边界或 Web/H5 联调检查清单；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 62 为当前最新状态

当前最新完成项：

- 新增 `docs/real_data_import_runbook.md`，形成真实展品数据导入前到导入后的端到端操作清单。
- Runbook 覆盖 manual source review、runtime config、migration、backup、seed dry-run、import、post-import backend checks、GeniOS handoff checks、logging and evidence、stop conditions。
- `docs/staging_validation_record.md` 增加 “Real data import runbook reviewed” 记录项。
- README、operational readiness、MVP handoff 和文档契约测试已同步。
- Runbook 明确：不创建、推断、改写或生成历史事实；不替代校史馆/专家审核；不训练模型、不运行 RAG、不生成讲解内容。
- 最新全量测试结果为 `136 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 Web/H5 联调检查清单或 staging 实库验证脚本边界；不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 63 为当前最新状态

当前最新完成项：

- 新增 `docs/web_h5_integration_checklist.md`，作为 Web/H5 浏览器联调和现场 demo 前的验收清单。
- Checklist 覆盖 runtime prerequisites、CORS、business/operator API key header、request id 证据、public/operator probe、Visitor State session、QR scan/visit event、exhibit source checks、structured UI data、GeniOS handoff gates、logging evidence 和 Stop Conditions。
- Checklist 明确 `source_safety.ready_for_generation=true` 与 `grounding_sources_complete=true` 是展示 GeniOS 生成讲解前的关键门槛。
- Checklist 明确后端不运行 RAG、不生成讲解内容、不实现前端页面、不做数字人、不做 AR/VR、不替代 GeniOS。
- README、operational readiness、MVP handoff 和文档契约测试已同步。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `22 passed`。
- 最新全量测试结果为 `137 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 实库验证脚本边界或部署环境实际验证记录；若进入真实联调，先按 `docs/web_h5_integration_checklist.md` 和 `docs/real_data_import_runbook.md` 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 64 为当前最新状态

当前最新完成项：

- 新增 `scripts/validate_staging_database.py`，用于对配置的 staging/production-like 目标数据库做只读验证。
- 脚本检查 database connectivity、核心表、当前 Alembic head、exhibit count、空 `source_reference`、Visitor State count、visit-event count 和 audit-log count。
- 脚本支持 `--database-url`、`--require-exhibits`、`--require-sourced-exhibits`、`--require-audit-logs`。
- 脚本对 SQLite 文件路径做存在性检查，避免只因连接检查而意外创建缺失的 SQLite 文件。
- 脚本明确不运行 migration、不导入记录、不写 audit log、不验证历史准确性、不运行 RAG、不生成讲解内容。
- 新增 `tests/test_validate_staging_database.py`，覆盖 migrated database、空展品强制失败、未来源展品强制失败、缺失 SQLite 文件不创建、CLI 只读边界输出。
- README、database migrations、production hardening、operational readiness、staging validation record、MVP handoff 和文档契约测试已同步。
- 组合测试 `pytest tests\test_validate_staging_database.py tests\test_documentation_contract.py` 通过，结果为 `28 passed`。
- 最新全量测试结果为 `143 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充部署环境实际验证记录示例、GeniOS handoff 联调证据模板或更细的备份/回滚演练；若进入真实联调，先按 `docs/web_h5_integration_checklist.md`、`docs/real_data_import_runbook.md` 和 `scripts/validate_staging_database.py` 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 65 为当前最新状态

当前最新完成项：

- 新增 `docs/genios_handoff_evidence_template.md`，用于每次 GeniOS handoff 联调、demo 或 staging 验证时记录证据。
- 模板覆盖 run metadata、pre-handoff gates、visit context evidence、GeniOS backend package evidence、GeniOS consumption evidence、logging evidence、pass criteria 和 stop conditions。
- 模板要求记录 `GET /api/genios/context/{session_id}`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}` 的 request id 和关键字段。
- 模板明确 `grounding_sources_complete=true` 与 `source_safety.ready_for_generation=true` 是生成讲解展示前的关键门槛。
- 模板明确不定义 GeniOS prompt、不运行 RAG、不生成讲解内容、不训练模型、不做数字人、不做 AR/VR，也不能替代校史馆/专家审核。
- README、operational readiness、staging validation record、MVP handoff 和文档契约测试已同步。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `24 passed`。
- 最新全量测试结果为 `144 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充部署环境实际验证记录示例或更细的备份/回滚演练；若进入 GeniOS 联调，先按 `docs/genios_handoff_evidence_template.md`、`docs/web_h5_genios_integration.md` 和 `docs/web_h5_integration_checklist.md` 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 66 为当前最新状态

当前最新完成项：

- 新增 `docs/examples/genios_handoff_evidence.example.md`，作为 GeniOS handoff 证据模板的非历史 fixture/placeholder 示例。
- 示例覆盖 pre-handoff gates、visit context evidence、GeniOS backend package evidence、GeniOS consumption evidence、logging evidence、pass criteria 和 stop conditions 的填写方式。
- 示例包含 `fixture-exhibit-001`、示例 request id、`grounding_sources_complete=true`、`source_safety.ready_for_generation=true` 等占位值。
- 示例明确：不是 staging 或真实校史馆环境已验证证据，不是历史内容、Prompt、RAG 内容或校史来源证据。
- `docs/genios_handoff_evidence_template.md` 增加示例入口说明。
- README、operational readiness、staging validation record、MVP handoff 和文档契约测试已同步。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `24 passed`。
- 最新全量测试结果为 `144 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充更细的备份/回滚演练或部署环境实际验证记录；若进入 GeniOS 联调，使用 `docs/genios_handoff_evidence_template.md` 复制填写真实证据，不要把 `docs/examples/genios_handoff_evidence.example.md` 当作真实验证。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 67 为当前最新状态

当前最新完成项：

- 新增 `docs/backup_rollback_drill.md`，作为生产化变更、真实数据导入、迁移、Web/H5 或 GeniOS handoff 联调前后的备份与回滚演练清单。
- Drill 覆盖 Pre-Change Runtime Gate、Backup Gate、Change Gate、Post-Change Validation Gate、Rollback Decision 和 Rollback Execution Record。
- Drill 串联现有工具：`scripts/export_exhibits.py`、`scripts/verify_exhibit_backup.py --require-non-empty`、`scripts/rehearse_exhibit_restore.py`、`scripts/validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`scripts/deployment_self_check.py`。
- Drill 要求回滚后重新检查 `GET /api/exhibits/source-report`、`GET /api/genios/handoff/{session_id}`、`source_safety.ready_for_generation`、`grounding_sources_complete` 和 request id 关联。
- Drill 明确不证明历史准确性、不替代校史馆/专家审核、不训练模型、不运行 RAG、不生成讲解内容、不定义 GeniOS prompt、不做数字人、不做 AR/VR。
- README、production hardening、operational readiness、staging validation record、MVP handoff 和文档契约测试已同步。
- 文档契约测试第一次发现边界措辞不够显式，已修正文档；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `25 passed`。
- 最新全量测试结果为 `145 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充部署环境实际验证记录示例或更细的 operator runbook；若进入真实数据或 GeniOS 联调，按 `docs/backup_rollback_drill.md`、`docs/real_data_import_runbook.md` 和 `docs/genios_handoff_evidence_template.md` 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 68 为当前最新状态

当前最新完成项：

- 新增 `docs/operator_runbook.md`，作为后端操作者执行本地 demo、真实数据 dry-run/import、staging migration validation、Web/H5 integration check、GeniOS handoff evidence run、backup and rollback drill、incident triage 的总入口。
- Runbook 串联 `validate_runtime_config.py`、`deployment_self_check.py`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run`、`rehearse_migrations.py`、`validate_staging_database.py` 等现有工具。
- Runbook 覆盖 Web/H5 gate、GeniOS handoff gate、readiness/auth/source-safety/Visitor State drift incident triage 和证据保存要求。
- Runbook 明确不训练模型、不替代 GeniOS、不运行 RAG、不生成讲解内容、不定义 GeniOS prompt、不证明历史准确性、不替代校史馆/专家审核、不做数字人、不做 AR/VR。
- README、operational readiness、production hardening、MVP handoff 和文档契约测试已同步。
- 文档契约测试过程中发现边界措辞和 MVP handoff 路径引用不够显式，已修正；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `26 passed`。
- 最新全量测试结果为 `146 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充部署环境实际验证记录示例；若进入实际操作，先从 `docs/operator_runbook.md` 选择 run type，再按对应 runbook 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 69 为当前最新状态

当前最新完成项：

- 新增 `docs/examples/deployment_environment_validation.example.md`，作为部署环境验证记录的 placeholder 示例。
- 示例覆盖 Runtime Config Evidence、Read-Only Deployment Self-Check Evidence、Database Validation Evidence、Data Safety Evidence、Web/H5 Evidence、GeniOS Handoff Evidence、Centralized Logging Evidence 和 Final Decision。
- 示例串联 `validate_runtime_config.py --profile staging`、`deployment_self_check.py`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py` 等命令。
- 示例包含 `GET /api/system/access-policy`、`GET /api/system/security-status`、`GET /api/genios/handoff/{session_id}`、`grounding_sources_complete`、`source_safety.ready_for_generation`、`HISTORYGUIDE_LOG_FORMAT=json` 和 request id 关联字段。
- 示例明确：仅为占位格式示例，不是任何真实 staging、production-like 或校史馆部署已验证证据；不证明历史准确性、不替代校史馆/专家审核、不训练模型、不运行 RAG、不生成讲解内容、不定义 GeniOS prompt、不做数字人、不做 AR/VR。
- README、operator runbook、operational readiness、production hardening、MVP handoff 和文档契约测试已同步。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `26 passed`。
- 最新全量测试结果为 `146 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若进入实际部署验证，复制真实记录时不要把 `docs/examples/deployment_environment_validation.example.md` 当作已验证证据；若继续生产硬化，可优先补充更细的 incident response checklist。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 70 为当前最新状态

当前最新完成项：

- 新增 `docs/incident_response_checklist.md`，作为真实参观 demo、Web/H5 联调、GeniOS handoff、staging 验证或生产化检查失败时的后端事故响应清单。
- Checklist 覆盖 First Five Minutes 证据保留、readiness/database failure、repeated 401/access boundary failure、source-safety/generated explanation block、Visitor State drift、Web/H5 scan/browser integration failure、GeniOS handoff failure、logging/request correlation failure、data corruption/rollback trigger 和 evidence package。
- Checklist 串联 `GET /ready`、`GET /api/system/database`、`GET /api/system/access-policy`、`GET /api/system/security-status`、`GET /api/system/operational-alerts`、`GET /api/exhibits/source-report`、`GET /api/exhibits/quality-report`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/visitor-states/{session_id}/visit-events`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}` 和 `POST /api/visitor-states/{session_id}/visit-events`。
- Checklist 明确 `source_safety.ready_for_generation`、`grounding_sources_complete`、`missing_exhibit_ids`、`unsourced_exhibit_ids`、`X-HistoryGuide-Request-Id`、`HISTORYGUIDE_API_KEY`、`HISTORYGUIDE_OPERATOR_API_KEY`、`HISTORYGUIDE_CORS_ORIGINS`、`HISTORYGUIDE_LOG_FORMAT=json` 等事故排查证据点。
- README、operator runbook、operational readiness、production hardening、MVP handoff 和文档契约测试已同步。
- Checklist 明确：不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不证明历史准确性。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `27 passed`。
- 最新全量测试结果为 `147 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 production-like monitoring alert examples 或 staging 真实验证记录；若进入实际事故处理，先按 `docs/operator_runbook.md` 选择 run type，再按 `docs/incident_response_checklist.md` 保留证据和分流。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 71 为当前最新状态

当前最新完成项：

- 新增 `docs/monitoring_alert_examples.md`，作为 production-like 监控与告警规则示例文档。
- 新增 `docs/examples/operational_alerts_attention_required.example.json`，作为 `GET /api/system/operational-alerts` 的 attention_required 占位响应样例。
- 监控示例覆盖 backend readiness、repeated auth failure、source-safety block、Visitor State drift、GeniOS handoff slow/failing、audit evidence missing、rollback_candidate escalation 和 dashboard panels。
- 监控示例串联 `GET /ready`、`GET /api/system/database`、`GET /api/system/access-policy`、`GET /api/system/security-status`、`GET /api/system/operational-alerts`、`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}`。
- 监控示例明确关注 `HISTORYGUIDE_LOG_FORMAT=json`、`X-HistoryGuide-Request-Id`、`source_safety.ready_for_generation`、`grounding_sources_complete`、`missing_exhibit_ids`、`unsourced_exhibit_ids`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000` 等真实联调与现场运行信号。
- README、centralized logging、operator runbook、operational readiness、production hardening、MVP handoff、incident response checklist 和文档契约测试已同步。
- 监控示例明确：不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不证明历史准确性。
- 文档契约测试第一次发现边界措辞不够精确，已修正；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `28 passed`。
- 最新全量测试结果为 `148 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 真实验证记录填写示例或 operator evidence package checklist；若进入实际部署或现场 demo，先按 `docs/operator_runbook.md` 选择 run type，并结合 `docs/monitoring_alert_examples.md`、`docs/incident_response_checklist.md` 做监控和排障。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 72 为当前最新状态

当前最新完成项：

- 新增 `docs/operator_evidence_package_checklist.md`，用于 local demo、staging validation、verified exhibit data import、Web/H5 integration check、GeniOS handoff run、incident response、monitoring setup 或 rollback-sensitive change 后打包操作者证据。
- Checklist 覆盖 Package Metadata、Required Evidence Files、Runtime Evidence、Data And Migration Evidence、Visit Flow Evidence、GeniOS Handoff Evidence、Monitoring And Incident Evidence、Audit Evidence、Redaction Checklist 和 Final Package Decision。
- Checklist 串联 `validate_runtime_config.py --profile staging`、`deployment_self_check.py --base-url`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run`、`rehearse_migrations.py`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`。
- Checklist 覆盖真实参观主链路证据：`POST /api/visitor-states`、`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/visitor-states/{session_id}/visit-events`、`GET /api/recommendations/{session_id}`、`GET /api/visit-routes/{session_id}/plan`、`GET /api/visits/{session_id}/summary`。
- Checklist 覆盖 GeniOS handoff 证据：`GET /api/genios/context/{session_id}`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}`、`grounding_sources_complete`、`source_safety.ready_for_generation`、`missing_exhibit_ids`、`unsourced_exhibit_ids`。
- Checklist 覆盖 monitoring/incident/audit 证据：`GET /api/system/operational-alerts`、`GET /api/audit-logs/stats`、`GET /api/audit-logs`、`X-HistoryGuide-Request-Id`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000`、`rollback_candidate`。
- `docs/staging_validation_record.md` 增加 Operator evidence package path 与 Evidence package completed 字段。
- README、operator runbook、operational readiness、production hardening、MVP handoff、incident response checklist、monitoring alert examples 和文档契约测试已同步。
- Checklist 明确：不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不证明历史准确性、不替代校史馆/专家审核。
- 文档契约测试第一次发现边界措辞不够精确，已修正；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `29 passed`。
- 最新全量测试结果为 `149 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 真实验证记录填写示例、production readiness decision checklist 或更强的后端只读验证脚本；若进入实际部署或现场 demo，按 `docs/operator_runbook.md` 执行，并用 `docs/operator_evidence_package_checklist.md` 打包证据。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 73 为当前最新状态

当前最新完成项：

- 新增 `docs/production_readiness_decision_checklist.md`，用于 production-like run、public demo、museum-site rehearsal 或 real visitor-facing backend run 前做 go/no-go 决策。
- Checklist 覆盖 Decision Metadata、Required Evidence、Runtime Configuration、Read-Only Runtime Self-Check、Database And Migration、Data Safety And Backup、Visit Flow、GeniOS Handoff And Source Safety、Monitoring And Incident Preparedness、Evidence Package 和 Final Decision Rules。
- Checklist 串联 `validate_runtime_config.py --profile staging|production`、`deployment_self_check.py --base-url`、`rehearse_migrations.py`、`alembic upgrade head`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run`。
- Checklist 覆盖 runtime endpoints：`GET /health`、`GET /ready`、`GET /api/system/database`、`GET /api/system/access-policy`、`GET /api/system/security-status`、`GET /api/system/operational-alerts`。
- Checklist 覆盖真实参观主链路与 GeniOS handoff：`POST /api/visitor-states`、`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/visitor-states/{session_id}/visit-events`、`GET /api/recommendations/{session_id}`、`GET /api/visit-routes/{session_id}/plan`、`GET /api/visits/{session_id}/summary`、`GET /api/genios/context/{session_id}`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}`。
- Checklist 明确 `source_safety.ready_for_generation=true`、`grounding_sources_complete=true`、`missing_exhibit_ids`、`unsourced_exhibit_ids`、`X-HistoryGuide-Request-Id`、`HISTORYGUIDE_API_KEY`、`HISTORYGUIDE_OPERATOR_API_KEY`、`HISTORYGUIDE_CORS_ORIGINS`、`HISTORYGUIDE_LOG_FORMAT=json`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000`、`unsourced_exhibits`、`visitor_state_integrity_issues`、`audit_logs_empty`、`rollback_candidate` 等决策信号。
- `docs/staging_validation_record.md` 增加 Production readiness decision checklist completed 与 Production readiness decision 字段。
- README、operational readiness、production hardening、operator runbook、operator evidence package checklist、MVP handoff 和文档契约测试已同步。
- Checklist 明确：通过测试本身不是 production readiness evidence；不证明历史准确性、不替代校史馆/专家审核、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR。
- 文档契约测试两次发现精确命令/精确措辞缺口，已修正；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `30 passed`。
- 最新全量测试结果为 `150 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充更强的后端只读验证脚本或 staging 真实验证记录填写示例；若进入实际部署或现场 demo，按 `docs/operator_runbook.md`、`docs/operator_evidence_package_checklist.md` 和 `docs/production_readiness_decision_checklist.md` 执行。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 74 为当前最新状态

当前最新完成项：

- 新增 `scripts/validate_backend_readiness.py`，作为运行中后端的更强只读 readiness validator。
- 脚本支持 `--base-url`、`--api-key`、`--operator-key`、`--session-id`、`--require-exhibits`、`--require-sourced-exhibits`、`--require-audit-logs`、`--require-clean-operational-alerts`、`--require-visit-events`。
- 基础检查覆盖 `GET /ready`、`GET /api/system/database`、`GET /api/system/operational-alerts`、`GET /api/exhibits/source-report`、`GET /api/exhibits/quality-report`、`GET /api/audit-logs/stats`。
- 传入 `--session-id` 后额外检查 `GET /api/visitor-states/{session_id}/integrity`、`GET /api/visitor-states/{session_id}/visit-events`、`GET /api/recommendations/{session_id}`、`GET /api/visit-routes/{session_id}/plan`、`GET /api/visits/{session_id}/summary`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}`。
- 脚本会输出每项检查的 PASS/FAIL、status、`X-HistoryGuide-Request-Id` 与关键摘要；不会打印 business/operator key 值。
- 新增 `tests/test_validate_backend_readiness.py`，覆盖核心只读 gate、session/GeniOS source-safety、source-safety blocked path、key 脱敏输出、required audit logs failure。
- README、operational readiness、production hardening、production readiness decision checklist、operator evidence package checklist、MVP handoff 和文档契约测试已同步。
- 脚本明确：只做 read-only backend validation，不写数据库、不验证历史准确性、不运行 RAG、不生成讲解内容、不打印 key values。
- 组合测试 `pytest tests\test_validate_backend_readiness.py tests\test_documentation_contract.py` 通过，结果为 `36 passed`。
- 最新全量测试结果为 `156 passed, 2 warnings`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 真实验证记录填写示例或围绕 `validate_backend_readiness.py` 增加 operator 使用样例；若进入实际部署或现场 demo，先运行 `validate_runtime_config.py`、`deployment_self_check.py`、`validate_staging_database.py` 和 `validate_backend_readiness.py`，再用 evidence package 与 production readiness checklist 做决策。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 75 为当前最新状态

当前最新完成项：

- 新增 `docs/examples/backend_readiness_validation.example.md`，作为 `scripts/validate_backend_readiness.py` 输出记录的 placeholder 示例。
- 示例覆盖 runtime command 与 visit-session command，包含 readiness、database status、operational alerts、exhibit source report、audit log stats、Visitor State integrity、GeniOS grounding、GeniOS preflight、GeniOS handoff 等 PASS 摘要。
- 示例要求记录 `X-HistoryGuide-Request-Id`、`source_safety.ready_for_generation=True`、`grounding_sources_complete=True`、`missing_exhibit_ids=[]`、`unsourced_exhibit_ids=[]` 和 `blocking_check_names=[]`。
- README、operational readiness、production hardening、operator runbook、operator evidence package checklist、production readiness decision checklist、MVP handoff 和文档契约测试已同步。
- 示例明确：仅为占位格式示例，不是任何真实 staging、production-like 或校史馆部署已验证证据；不写数据库、不打印 key values、不验证历史准确性、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不替代校史馆/专家审核。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `31 passed`。
- 最新全量测试结果为 `156 passed, 2 warnings`。
- Git 状态检查仍显示当前目录不是 Git 仓库：`fatal: not a git repository (or any of the parent directories): .git`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 staging 真实验证记录填写示例，或增加围绕 operator evidence package 的真实运行归档模板；若进入实际部署或现场 demo，先运行 `validate_runtime_config.py`、`deployment_self_check.py`、`validate_staging_database.py` 和 `validate_backend_readiness.py`，再用 `docs/examples/backend_readiness_validation.example.md` 作为格式参考记录真实输出。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 76 为当前最新状态

当前最新完成项：

- 新增 `docs/examples/operator_evidence_package.example.md`，作为 operator evidence package 的 placeholder 归档样例。
- 示例串联 Runtime Evidence、Data And Migration Evidence、Visit Flow Evidence、GeniOS Handoff Evidence、Monitoring And Incident Evidence、Audit Evidence、Redaction Checklist 和 Final Package Decision。
- 示例覆盖 `validate_runtime_config.py --profile staging`、`deployment_self_check.py --base-url`、`validate_backend_readiness.py --base-url`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、展品备份/恢复演练、Visitor State、visit-events、recommendations、route plan、visit summary、GeniOS handoff、audit logs、monitoring signals。
- 示例要求保留 `X-HistoryGuide-Request-Id`、`source_safety.ready_for_generation=true`、`grounding_sources_complete=true`、`missing_exhibit_ids=[]`、`unsourced_exhibit_ids=[]`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000`、`rollback_candidate` 和最终 `proceed_with_warnings`/blocked/rollback 决策字段。
- README、operational readiness、production hardening、operator runbook、operator evidence package checklist、production readiness decision checklist、MVP handoff 和文档契约测试已同步。
- 示例明确：仅为占位格式示例，不是任何真实 staging、production-like 或校史馆部署已验证证据；不证明历史准确性、不替代校史馆/专家审核、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `31 passed`。
- 最新全量测试结果为 `156 passed, 2 warnings`。
- Git 状态检查仍显示当前目录不是 Git 仓库：`fatal: not a git repository (or any of the parent directories): .git`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充 production readiness 决策填写示例，或把 staging 真实验证记录样例与 operator evidence package 样例进一步串联；若进入实际部署或现场 demo，复制 `docs/examples/operator_evidence_package.example.md` 的结构填写真实命令输出，不要把 placeholder 当作真实验证。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 77 为当前最新状态

当前最新完成项：

- 新增 `docs/examples/production_readiness_decision.example.md`，作为 production readiness go/no-go 决策填写的 placeholder 示例。
- 示例覆盖 Decision Metadata、Required Evidence Attached、Gate 1 Runtime Configuration、Gate 2 Read-Only Runtime Self-Check、Gate 3 Database And Migration、Gate 4 Data Safety And Backup、Gate 5 Visit Flow、Gate 6 GeniOS Handoff And Source Safety、Gate 7 Monitoring And Incident Preparedness、Gate 8 Evidence Package 和 Final Decision。
- 示例串联 `validate_runtime_config.py --profile staging|production`、`deployment_self_check.py --base-url`、`validate_backend_readiness.py --base-url`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run`。
- 示例覆盖真实参观主链路和 GeniOS handoff 决策信号：`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/genios/handoff/{session_id}`、`source_safety.ready_for_generation=true`、`grounding_sources_complete=true`、`missing_exhibit_ids=[]`、`unsourced_exhibit_ids=[]`。
- 示例覆盖监控与 go/no-go 信号：`X-HistoryGuide-Request-Id`、`HISTORYGUIDE_API_KEY`、`HISTORYGUIDE_OPERATOR_API_KEY`、`HISTORYGUIDE_CORS_ORIGINS`、`HISTORYGUIDE_LOG_FORMAT=json`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000`、`unsourced_exhibits`、`visitor_state_integrity_issues`、`audit_logs_empty`、`rollback_candidate`。
- 示例明确 allowed final decisions：`proceed`、`proceed_with_warnings`、`blocked`、`rollback_required`，并强调 passing tests alone are not production readiness evidence。
- README、operational readiness、production hardening、operator runbook、production readiness decision checklist、MVP handoff 和文档契约测试已同步。
- 示例明确：仅为占位格式示例，不是任何真实 staging、production-like、museum-site 或 production 部署已验证证据；不证明历史准确性、不替代校史馆/专家审核、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR。
- 文档契约测试第一次发现样例缺少 `blocked` 决策词，已补齐；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `31 passed`。
- 最新全量测试结果为 `156 passed, 2 warnings`。
- Git 状态检查仍显示当前目录不是 Git 仓库：`fatal: not a git repository (or any of the parent directories): .git`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先把 staging validation record、operator evidence package 和 production readiness decision 三个示例之间的引用链再压实，或补充真实部署运行前的最终 operator checklist；若进入实际部署或现场 demo，复制 `docs/examples/production_readiness_decision.example.md` 的结构填写真实命令输出和真实决策，不要把 placeholder 当作真实验证。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 78 为当前最新状态

当前最新完成项：

- 新增 `docs/operator_final_prerun_checklist.md`，作为 production-like run、public demo、museum-site rehearsal 或 real visitor-facing backend run 启动前最后阶段的后端 operator checklist。
- Checklist 串联 Required Inputs、Environment And Access、Read-Only Backend State、Data/Migration/Rollback、Real Visit Session、GeniOS Handoff Source Safety、Monitoring And Incident Readiness、Final Decision 和 Final Operator Statement。
- Checklist 明确真实记录输入包括 `docs/staging_validation_record.md`、`docs/operator_evidence_package_checklist.md`、`docs/production_readiness_decision_checklist.md`、`docs/genios_handoff_evidence_template.md`、`docs/web_h5_integration_checklist.md`、`docs/backup_rollback_drill.md`、`docs/monitoring_alert_examples.md` 和 `docs/incident_response_checklist.md`。
- Checklist 明确 placeholder examples 只能作为格式参考，不能当作真实 staging、production-like、museum-site 或 production evidence。
- Checklist 覆盖最后运行前命令链：`validate_runtime_config.py --profile staging|production`、`deployment_self_check.py --base-url`、`validate_backend_readiness.py --base-url`、`rehearse_migrations.py`、`alembic upgrade head`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`export_exhibits.py`、`verify_exhibit_backup.py`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run`。
- Checklist 覆盖真实参观主链路、GeniOS handoff source-safety、request-id correlation、monitoring signals、incident owner、rollback owner、final proceed/blocked/rollback decision。
- README、operational readiness、production hardening、operator runbook、production readiness decision checklist、MVP handoff 和文档契约测试已同步。
- Checklist 明确：不证明历史准确性、不替代校史馆/专家审核、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不替代 GeniOS、不认证 Web/H5 或 GeniOS 生产就绪。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `32 passed`。
- 最新全量测试结果为 `157 passed, 2 warnings`。
- Git 状态检查仍显示当前目录不是 Git 仓库：`fatal: not a git repository (or any of the parent directories): .git`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充现场演示后复盘/回填记录模板，或进入实际 staging/demo 前按 `docs/operator_final_prerun_checklist.md` 填写真实证据。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 79 为当前最新状态

当前最新完成项：

- 新增 `docs/operator_post_run_review.md`，作为 local demo、staging validation、Web/H5 integration check、GeniOS handoff evidence run、production-like run、museum-site rehearsal 或 real visitor-facing backend run 结束后的后端复盘/回填模板。
- 模板覆盖 Run Metadata、Evidence Chain、Runtime Outcome、Request Id Evidence、Visit Flow Review、GeniOS Handoff Review、Data And Audit Review、Monitoring And Incident Review、Evidence Package Update、Follow-Up Decisions。
- 模板串联 `docs/operator_final_prerun_checklist.md`、`docs/staging_validation_record.md`、`docs/operator_evidence_package_checklist.md`、`docs/production_readiness_decision_checklist.md`、`docs/genios_handoff_evidence_template.md`、`docs/web_h5_integration_checklist.md`、`docs/backup_rollback_drill.md`、`docs/incident_response_checklist.md` 和 `docs/monitoring_alert_examples.md`。
- 模板覆盖运行后结果信号：`GET /health`、`GET /ready`、`GET /api/system/operational-alerts`、`status_code = 401`、`status_code >= 500`、`elapsed_ms > 1000`、`rollback_candidate`。
- 模板覆盖 request id evidence、Visitor State 主链路、GeniOS handoff source-safety、audit logs、monitoring/incident/rollback、operator evidence package update 和 follow-up owner。
- 模板明确 post-run decision 可为 `closed_clean`、`closed_with_warnings`、`follow_up_required`、`incident_follow_up_required`、`rollback_follow_up_required`。
- README、operational readiness、production hardening、operator runbook、operator final pre-run checklist、MVP handoff 和文档契约测试已同步。
- 模板明确：不证明历史准确性、不替代校史馆/专家审核、不运行 RAG、不生成讲解内容、不训练模型、不定义 GeniOS prompts、不实现数字人、不实现 AR/VR、不认证 Web/H5 或 GeniOS 生产就绪。
- 文档契约测试先后发现模板缺少 `POST /api/visitor-states` 和 `GET /api/audit-logs/stats` 的显式接口名，已补齐；复测 `pytest tests\test_documentation_contract.py` 通过，结果为 `33 passed`。
- 最新全量测试结果为 `158 passed, 2 warnings`。
- Git 状态检查仍显示当前目录不是 Git 仓库：`fatal: not a git repository (or any of the parent directories): .git`。

下一步继续前请先阅读本文件和两份定位/边界文档。后续建议继续在真实数据接入、GeniOS 对接、Web/H5 联调、生产硬化中选择。若继续生产硬化，可优先补充一份“真实数据接入前最终 checklist”或开始面向真实展品 seed 的更细导入/审核边界强化；若进入实际 staging/demo，按 `docs/operator_final_prerun_checklist.md` 执行运行前检查，并在结束后用 `docs/operator_post_run_review.md` 回填真实结果。不要做大模型训练、数字人、AR/VR 或无关功能。

### 最新阶段索引：阶段 80 为当前最新状态

当前最新完成项：

- 新增并接入 `docs/real_data_preimport_final_checklist.md`，作为导入真实校史馆展品 seed 前的最终后端 gate。
- Checklist 覆盖 Required Inputs、Source Package And Manual Review、Seed Structure、Runtime And Migration、Backup And Restore、Seed Dry-Run、Pre-Import Runtime Evidence、Import Authorization、Immediate Post-Import Checks、GeniOS Source-Safety Smoke、Evidence Update 和 Stop Conditions。
- Checklist 串联 `docs/real_exhibit_seed_review.md`、`docs/exhibit_seed_format.md`、`docs/staging_validation_record.md`、`docs/backup_rollback_drill.md`、`docs/operator_evidence_package_checklist.md`、`docs/production_readiness_decision_checklist.md` 和 `docs/operator_post_run_review.md`。
- Checklist 明确导入前命令链：`validate_runtime_config.py --profile staging|production`、`rehearse_migrations.py`、`alembic upgrade head`、`validate_staging_database.py --require-exhibits --require-sourced-exhibits --require-audit-logs`、`export_exhibits.py`、`verify_exhibit_backup.py --require-non-empty`、`rehearse_exhibit_restore.py`、`import_exhibits.py --dry-run <verified-seed-file>`、`deployment_self_check.py --base-url`、`validate_backend_readiness.py --base-url`。
- Checklist 明确导入后和 GeniOS source-safety smoke：`GET /api/exhibits/source-report`、`GET /api/exhibits/quality-report`、`GET /api/audit-logs?action=exhibits_imported`、`GET /api/audit-logs/stats`、`GET /api/system/operational-alerts`、`POST /api/visitor-states`、`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/visitor-states/{session_id}/integrity`、`GET /api/genios/grounding/{session_id}`、`GET /api/genios/preflight/{session_id}`、`GET /api/genios/handoff/{session_id}`。
- README、operational readiness、real data import runbook、real exhibit seed review checklist、operator runbook、MVP handoff 和文档契约测试已同步。
- Checklist 明确：不创建/推断/改写/生成历史事实，不证明历史准确性，不替代校史馆/专家审核，不运行 RAG，不生成讲解内容，不训练模型，不定义 GeniOS prompts，不实现数字人，不实现 AR/VR。
- 文档契约测试 `pytest tests\test_documentation_contract.py` 通过，结果为 `34 passed`。
- 最新全量测试结果为 `159 passed, 2 warnings`。

下一步期望：

- 当前 Codex 后端职责内的 MVP、数据管理、Visitor State、展品管理、GeniOS 协作接口、运行脚本、测试和交付文档已形成闭环。
- 后续若继续推进，应以外部真实输入为触发：真实校史馆展品 source package、真实 GeniOS Agent/RAG 配置、Web/H5 客户端、staging/production-like 环境或现场 demo 运行证据。
- 在没有这些外部输入前，不建议继续无目标追加文档或功能；应结束当前自动推进任务。
- 不要做大模型训练、数字人、AR/VR 或无关功能。

### GeniOS/Coze 平台接入检查：2026-09-30

当前结果：

- 已按要求重新阅读本上下文记录和 `NK_HistoryGuide_Codex开发边界与实施路线.md`，并查看 `historyguide-backend/docs/web_h5_genios_integration.md`、`docs/api_contract.md`、`docs/deployment.md` 中的接入约束。
- 本机 `http://127.0.0.1:8000` 当前未运行，`GET /health` 和 `GET /openapi.json` 均连接失败。
- 即使本机后端启动，Coze/NK-GeniOS 云端通常也不能访问 `127.0.0.1`；真实平台接入需要一个 Coze 可访问的公网 HTTPS 后端地址。
- 当前后端已有可用于平台接入的接口：`POST /api/visitor-states`、`POST /api/visitor-states/{session_id}/visit-events`、`GET /api/genios/handoff/{session_id}`，并支持 `X-HistoryGuide-Api-Key`。
- 不应在缺少公网后端 URL、业务 API Key 和发布确认时修改或发布 Coze/NK-GeniOS Agent。

下一步期望：

- 若要继续真实接入平台，先提供或部署一个公网 HTTPS backend base URL，并配置 `HISTORYGUIDE_API_KEY`。
- 接入时优先在 Coze/NK-GeniOS 中配置 HTTP 工具/工作流调用 `GET /api/genios/handoff/{session_id}`，并要求 Agent 只有在 `source_safety.ready_for_generation=true` 时才生成讲解。
- 发布 Coze/NK-GeniOS Agent 前需要用户明确确认。

### 本地后端自检：2026-10-03

当前结果：

- 已按规则读取本上下文记录、`NK_HistoryGuide_Codex开发边界与实施路线.md` 和差异化定位文档。
- 本地虚拟环境可用：Python 3.12.14、FastAPI 0.141.1、SQLAlchemy 2.0.54、Pydantic 2.13.5。
- 启动本地后端：`http://127.0.0.1:8000`。
- `GET /health` 通过，返回 `status=ok`。
- `GET /ready` 通过，返回 `status=ready`、`database=ok`。
- `GET /openapi.json` 通过，HTTP 200。
- `scripts/deployment_self_check.py --base-url http://127.0.0.1:8000` 通过基础探针；发现 operational alerts 为 `attention_required`。
- operational alerts 展开后显示：展品来源完整；本地开发库存在旧 Visitor State/timeline integrity drift；fixture 展品 people 元数据为空；自检前 audit log 为空。
- 新建本地非历史 fixture session：`selfcheck-20261003-001`。
- Visitor State 创建、visit event 记录、`GET /api/genios/handoff/selfcheck-20261003-001` 均通过。
- session 级 readiness validator 通过：Visitor State integrity issue_count=0、visit_event_count=1、recommendation_count=1、route_plan item_count=1、GeniOS grounding/preflight/handoff 均 PASS，`source_safety.ready_for_generation=True`。
- 全量测试通过：`159 passed, 2 warnings`；警告来自 FastAPI/Starlette/anyio 上游弃用提示，不是业务失败。

下一步期望：

- 当前本地后端可用于本机联调和接口验证。
- 这不是 Coze/NK-GeniOS 平台真实接入完成，因为平台仍无法访问本机 `127.0.0.1`。
- 若继续接入平台，需要提供平台可访问的 HTTPS backend base URL，并配置业务 API Key；正式发布 Agent 前仍需用户明确确认。

### Coze/NK-GeniOS 临时接入尝试：2026-10-03

当前结果：

- 已启动本地 FastAPI 后端，并配置临时 `HISTORYGUIDE_API_KEY`；未在记录中保存完整 key 值。
- 本地验证通过：`GET /health` 正常；业务接口在无 `X-HistoryGuide-Api-Key` 时返回 401，带临时 key 时可访问。
- 已通过 `npx localtunnel --port 8000` 建立临时 HTTPS 隧道：`https://eighty-cars-matter.loca.lt`。
- 临时公网验证通过：`GET https://eighty-cars-matter.loca.lt/health` 正常；带临时 key 调用 `GET /api/genios/capabilities` 正常。
- 检查 `https://eighty-cars-matter.loca.lt/openapi.json`，确认包含 `/api/genios/handoff/{session_id}`；但当前 OpenAPI 未声明 `X-HistoryGuide-Api-Key` securitySchemes，Coze 若导入完整 OpenAPI 可能仍需手动配置 header。
- 尝试使用浏览器工具进入 Coze/NK-GeniOS 编排页配置工具；原始 in-app browser 标签页截图显示页面处于加载中白屏，DOM/AX 读取为空或超时。
- 新开 in-app browser 标签页会跳转到南开统一身份认证页，说明新标签无法复用原登录态；未自动处理登录。
- 因平台页面不可稳定读取/操作，本次未修改 Coze/NK-GeniOS 配置、未创建工具、未发布 Agent。

下一步期望：

- 若继续平台接入，需要先让 Coze/NK-GeniOS 编排页在浏览器中稳定加载到可编辑状态，或提供可访问的正式/staging 后端 URL 与平台工具配置入口。
- 临时隧道只适合短时联调；正式接入应使用稳定 HTTPS 后端，并在 Coze 工具中配置 `X-HistoryGuide-Api-Key`。
- Agent 发布仍需用户明确确认。

### Coze/NK-GeniOS 页面进入后的第二次接入尝试：2026-10-03

当前结果：

- 用户反馈内置浏览器已进入 Coze/NK-GeniOS 编排页。
- 已重新启动本地 FastAPI 后端，并生成一次性临时 `HISTORYGUIDE_API_KEY`；key 仅保存在本地临时文件 `.tmp_historyguide_api_key`，未写入本文档。
- 已重新建立临时 HTTPS 隧道：`https://honest-ears-guess.loca.lt`。
- 公网验证通过：`GET /health` 正常；带临时 key 的 `GET /api/genios/capabilities` 正常；`GET /openapi.json` 正常且包含 `/api/genios/handoff/{session_id}`。
- 浏览器工具可看到 in-app browser 中的 Coze 标签页，但读取原 Coze 标签页内容、截图、标题/DOM 文本均超时并触发工具重置。
- 因无法可靠读取或确认页面实际控件位置，本次未在 Coze 页面中盲点、未输入临时 API Key、未创建工具、未保存配置、未发布 Agent。

下一步期望：

- 若继续接入，建议用户在 Coze 页面中手动进入“工具/插件/工作流/HTTP API”配置页，并停在新增接口表单处，再让 Codex 填写；或提供截图/字段名。
- 手动配置时使用：base URL 为当前临时隧道或正式 HTTPS 后端；核心接口为 `GET /api/genios/handoff/{session_id}?recommendation_limit=3&route_max_items=5`；header 需要 `X-HistoryGuide-Api-Key`。
- 临时隧道每次都会变化，不适合长期配置；正式接入仍应使用稳定 HTTPS 后端。

### Coze/NK-GeniOS 精简 OpenAPI 接入修正：2026-10-03

当前结果：

- 完整后端 `/openapi.json` 在 Coze 自定义插件中创建后显示 `0 个工具`，说明平台无法从完整 OpenAPI 中自动生成工具。
- 新增公共只读端点：`GET /openapi-genios-handoff.json`。
- 该端点只描述 1 个工具：`GET /api/genios/handoff/{session_id}`，operationId 为 `get_genios_handoff`。
- 精简 OpenAPI 声明 `HistoryGuideApiKey`，header 名称为 `X-HistoryGuide-Api-Key`。
- 已更新 `app/main.py`、`app/core/security.py`、`app/api/routes/genios_openapi.py` 和 OpenAPI 契约测试。
- 测试通过：`pytest tests\test_openapi_contract.py` 结果为 `4 passed, 2 warnings`；`pytest tests\test_documentation_contract.py` 结果为 `34 passed`。
- 当前可用临时隧道：`https://plain-facts-do.loca.lt`。
- 已验证：
  - `GET https://plain-facts-do.loca.lt/health` 返回正常。
  - `GET https://plain-facts-do.loca.lt/openapi-genios-handoff.json` 返回精简 OpenAPI，包含唯一路径 `/api/genios/handoff/{session_id}` 和 header security `X-HistoryGuide-Api-Key`。

下一步期望：

- 在 Coze/NK-GeniOS 自定义插件里不要继续使用完整 `/openapi.json`。
- 新建插件时将插件 URL 改为：`https://plain-facts-do.loca.lt/openapi-genios-handoff.json`。
- Header 继续使用 `X-HistoryGuide-Api-Key` 与当前临时 key；临时隧道和 key 只用于联调。
- 若 Coze 成功生成 1 个工具，再回到 Agent 编排页添加该插件并测试 `get_genios_handoff`。
- 不要上架插件、不要发布 Agent，除非用户明确确认。

### Coze/NK-GeniOS 本地 OpenAPI 文件导入准备：2026-10-03

当前结果：

- Coze/NK-GeniOS 的“导入工具”弹窗要求本地上传 OpenAPI JSON/YAML 文件，而不是直接填写 URL。
- 已生成本地上传文件：`historyguide-backend/coze_genios_handoff_openapi.json`。
- 该文件只包含 1 个工具：`GET /api/genios/handoff/{session_id}`，operationId 为 `get_genios_handoff`。
- 旧临时隧道 `https://plain-facts-do.loca.lt` 已超时不可用。
- 已重新建立临时隧道：`https://spicy-dolls-rescue.loca.lt`。
- 文件中的 server URL 已更新为当前临时隧道：`https://spicy-dolls-rescue.loca.lt`。
- 文件声明 API Key header：`X-HistoryGuide-Api-Key`。
- 已确认 JSON 可解析，且只暴露 `/api/genios/handoff/{session_id}`，避免 Coze 再导入完整后端 OpenAPI 后显示 `0 个工具`。
- 已确认 `GET https://spicy-dolls-rescue.loca.lt/health` 返回正常。

下一步期望：

- 在当前 Coze/NK-GeniOS “导入工具”弹窗中保持 `OpenApi` 选中，上传 `historyguide-backend/coze_genios_handoff_openapi.json`，然后点击“确定”。
- 若平台要求鉴权，选择 header/API Key 类方式，Key 使用 `X-HistoryGuide-Api-Key`，Value 使用当前本地临时 key 文件中的值。
- 导入成功后应出现 `1 个工具` 或工具名 `get_genios_handoff`；若仍显示 `0 个工具`，不要继续发布，先截图回传。
- 不要上架插件、不要发布 Agent，除非用户明确确认。

### Coze/NK-GeniOS 工具导入后 Debug 状态：2026-10-03

当前结果：

- 用户截图显示 Coze/NK-GeniOS 已识别出 1 个工具，名称为 `Get GeniOS handoff package`，请求方法为 `GET`，但 Debug 状态为“未通过”。
- 本地后端仍正常：`GET http://127.0.0.1:8000/health` 返回正常。
- 旧临时隧道 `https://spicy-dolls-rescue.loca.lt` 已超时不可用。
- 已重新启动 localtunnel，当前可用临时公网地址为：`https://ugly-fireant-27.loca.lt`。
- 已更新本地上传文件 `historyguide-backend/coze_genios_handoff_openapi.json`，server URL 改为 `https://ugly-fireant-27.loca.lt`。
- 已创建 Debug 用 Visitor State：`demo-session-001`。
- 已验证带 `X-HistoryGuide-Api-Key` 调用 `GET https://ugly-fireant-27.loca.lt/api/genios/handoff/demo-session-001?recommendation_limit=3&route_max_items=5` 返回 200，并包含 `source_safety.ready_for_generation=true`。

下一步期望：

- 因平台中已导入的工具可能仍保存旧 server URL，优先在工具“查看详情”中检查/修改 base URL 为 `https://ugly-fireant-27.loca.lt`；若不能修改，则用已更新的 `coze_genios_handoff_openapi.json` 重新导入一次。
- Debug 参数使用 `session_id=demo-session-001`，`recommendation_limit=3`，`route_max_items=5`。
- 鉴权 header 使用 `X-HistoryGuide-Api-Key` 和当前本地临时 key。
- Debug 通过后再添加到 Agent 编排；不要上架插件、不要发布 Agent，除非用户明确确认。

### Coze/NK-GeniOS Debug 版 OpenAPI 文件：2026-10-03

当前结果：

- 用户反馈工具详情页持续弹“未知错误”，当前工具列表仍显示 `Debug 未通过`。
- 已确认后端和当前公网隧道不是问题：带 `X-HistoryGuide-Api-Key` 调用 `GET https://ugly-fireant-27.loca.lt/api/genios/handoff/demo-session-001?recommendation_limit=3&route_max_items=5` 返回成功。
- 已新增 Debug 版上传文件：`historyguide-backend/coze_genios_handoff_openapi_debug.json`。
- Debug 版文件仍只暴露 1 个工具：`GET /api/genios/handoff/{session_id}`。
- Debug 版文件把 `X-HistoryGuide-Api-Key` 从 security scheme 改为显式 header 参数，并把 200 输出 schema 简化为普通 object，以规避平台在鉴权配置或复杂嵌套输出解析时弹“未知错误”。

下一步期望：

- 在 Coze/NK-GeniOS 插件工具列表中删除当前 `Debug 未通过` 的工具，或新建一个插件重新导入。
- 使用 `historyguide-backend/coze_genios_handoff_openapi_debug.json` 重新导入。
- 导入后输入参数应包含 4 项：`session_id`、`recommendation_limit`、`route_max_items`、`X-HistoryGuide-Api-Key`。
- Debug 时填写：`session_id=demo-session-001`、`recommendation_limit=3`、`route_max_items=5`、`X-HistoryGuide-Api-Key=<当前临时 key>`。
- Debug 通过前不要上架插件、不要发布 Agent。

### Coze/NK-GeniOS Flat Handoff 兼容接口：2026-10-03

当前结果：

- 后端日志显示 NK-GeniOS/Coze 平台请求已经能打到本地后端公网隧道，且 `GET /api/genios/handoff/demo-session-001` 返回过 `200 OK`；因此“Debug 未通过”不是网络不通、API Key 错或 session 不存在。
- 判断失败集中在平台对复杂嵌套 JSON 输出的配置/校验。
- 新增平台友好接口：`GET /api/genios/handoff-flat/{session_id}`。
- Flat 接口仍基于正式 handoff 包构建，只把输出压平成字符串、数字、布尔字段；不生成讲解内容、不调用大模型、不做 RAG。
- 新增 schema：`GeniosFlatHandoffPackage`。
- 新增本地上传文件：`historyguide-backend/coze_genios_handoff_flat_openapi.json`。
- 当前可用临时隧道已切换为：`https://major-trees-happen.loca.lt`。
- 已验证带 `X-HistoryGuide-Api-Key` 调用 `GET https://major-trees-happen.loca.lt/api/genios/handoff-flat/demo-session-001?recommendation_limit=3&route_max_items=5` 返回 200。
- 相关测试通过：`pytest tests\test_genios_context.py tests\test_openapi_contract.py` 结果为 `18 passed, 2 warnings`。

下一步期望：

- 在 Coze/NK-GeniOS 插件工具中删除或暂时忽略旧的 `get_genios_handoff` 工具。
- 使用 `historyguide-backend/coze_genios_handoff_flat_openapi.json` 重新导入。
- 导入后工具名应为 `get_genios_flat_handoff`，输入为 `session_id`、`recommendation_limit`、`route_max_items`、`X-HistoryGuide-Api-Key`。
- Debug 参数使用：`session_id=demo-session-001`、`recommendation_limit=3`、`route_max_items=5`、`X-HistoryGuide-Api-Key=<当前临时 key>`。
- Debug 通过后，再把 flat 工具接入 Agent 编排；不要上架插件、不要发布 Agent，除非用户明确确认。

### 服务器部署进展：2026-10-04

当前结果：

- 已确认 `historyguide.catlifepet.top` 解析到服务器公网 IP `47.100.9.190`。
- 服务器为 Ubuntu 22.04，公网 IP `47.100.9.190`。
- 已安装 Caddy `v2.11.7` 和 Python `3.10.12`。
- 已上传部署包到 `/opt/nk-historyguide/historyguide-backend-deploy.zip` 并解压。
- 已创建 Python venv 并安装运行依赖、测试依赖。
- 服务器 Python 3.10 不支持 `datetime.UTC`，已在服务器上临时修正 `app/core/logging.py` 为 `timezone.utc`；本地代码也已同步修正。
- 服务器测试通过：`pytest tests/test_genios_context.py tests/test_openapi_contract.py` 结果为 `18 passed, 1 warning`。
- 已导入非历史 fixture 展品数据，结果为 `Imported 2 exhibit records.`。
- 已创建 `nk-historyguide.service` 并启动，systemd 状态显示 `active (running)`。
- 注意：当前 systemd service 使用了 `HISTORYGUIDE_API_KEY_FILE`，但项目配置实际读取的是 `HISTORYGUIDE_API_KEY`；下一步需要修正为 `EnvironmentFile` 或直接设置 `HISTORYGUIDE_API_KEY`。

下一步期望：

- 在服务器创建 `/opt/nk-historyguide/historyguide.env`，写入 `HISTORYGUIDE_API_KEY`、`HISTORYGUIDE_DATABASE_URL`、`HISTORYGUIDE_LOG_FORMAT`。
- 修改 systemd service 使用 `EnvironmentFile=/opt/nk-historyguide/historyguide.env` 后重启。
- 创建/确认 `demo-session-001` Visitor State。
- 配置 Caddy：`historyguide.catlifepet.top { reverse_proxy 127.0.0.1:8000 }`。
- 验证 `https://historyguide.catlifepet.top/health` 和带 API key 的 `/api/genios/handoff-flat/demo-session-001`。

### 服务器 HTTPS 与 Flat Handoff 验证完成：2026-10-04

当前结果：

- 已放弃 Caddy 对外监听，因为服务器已有 nginx 占用 `80/443`，保留 nginx 以避免影响原有站点。
- 已新增 nginx 站点配置 `/etc/nginx/conf.d/nk-historyguide.conf`，将 `historyguide.catlifepet.top` 反代到 `127.0.0.1:8000`。
- 已使用 certbot 为 `historyguide.catlifepet.top` 签发并部署 HTTPS 证书。
- 证书路径：`/etc/letsencrypt/live/historyguide.catlifepet.top/fullchain.pem` 和 `privkey.pem`。
- certbot 已配置自动续期任务。
- 本地公网验证通过：`GET https://historyguide.catlifepet.top/health` 返回 `status=ok`。
- 服务器上已创建/确认 `demo-session-001`，并验证带服务端 production API key 调用 `GET https://historyguide.catlifepet.top/api/genios/handoff-flat/demo-session-001?recommendation_limit=3&route_max_items=5` 返回成功。
- 返回结果包含 `ready_for_generation=true`、`grounding_sources_complete=true`、`recommendation_count=2`、`planned_minutes=14`。
- 本地 NK-GeniOS flat OpenAPI 上传文件已更新：`historyguide-backend/coze_genios_handoff_flat_openapi.json` 的 server URL 改为 `https://historyguide.catlifepet.top`。
- 已确认该 OpenAPI 文件只暴露 `/api/genios/handoff-flat/{session_id}`，operationId 为 `get_genios_flat_handoff`，输入参数为 `session_id`、`recommendation_limit`、`route_max_items`、`X-HistoryGuide-Api-Key`。

下一步期望：

- 回到 NK-GeniOS 插件页面，使用 `historyguide-backend/coze_genios_handoff_flat_openapi.json` 重新导入工具。
- Debug 使用：`session_id=demo-session-001`、`recommendation_limit=3`、`route_max_items=5`、`X-HistoryGuide-Api-Key=<服务器 /opt/nk-historyguide/.historyguide_api_key 中的 hg-prod key>`。
- Debug 通过后，再把 `get_genios_flat_handoff` 添加到 Agent 编排。
- 不要上架插件、不要发布 Agent，除非用户明确确认。

### NK-GeniOS Flat 工具接入完成：2026-10-07

当前结果：

- `NK HistoryGuide Flat Handoff` 插件中的 `Get flat GeniOS handoff package` 已完成 Debug，平台状态显示“通过”。
- 用户已将该工具添加到 NK-GeniOS Agent。
- 当前后端、稳定 HTTPS 域名、API Key 鉴权、`demo-session-001` 和 flat handoff 工具链路已打通。
- 尚未验证 Agent 是否会按提示主动调用工具，也尚未验证工具结果与知识库/RAG 的联合回答。
- 尚未发布 Agent；发布前仍需要用户明确确认。

下一步期望：

- 在 Agent 提示词中明确工具调用条件、固定联调参数和 source-safety 规则。
- 在 Agent 调试对话中验证工具调用记录，参数使用 `session_id=demo-session-001`、`recommendation_limit=3`、`route_max_items=5`。
- 只有当 `ready_for_generation=true` 且 `grounding_sources_complete=true` 时，Agent 才可以结合知识库生成讲解；否则应说明资料不足，不得编造。
- 工具调用验证通过后，再接入经核验的校史知识库和真实 visitor session；正式发布前轮换此前暴露过的 API Key，并同步更新插件鉴权配置。

### NK-GeniOS Agent 工具调用验证通过：2026-10-07

当前结果：

- 单 Agent 模式已保留，`NK HistoryGuide Flat Handoff` 插件继续挂载在 Agent 的插件区域。
- Agent 提示词已加入强制工具调用规则与 `demo-session-001` 联调参数。
- 调试请求要求返回 `ready_for_generation`、`route_exhibit_ids` 和 `recommendation_exhibit_ids` 原始值。
- Agent 返回 `ready_for_generation=true`，`route_exhibit_ids=fixture-exhibit-002,fixture-exhibit-001`，`recommendation_exhibit_ids=fixture-exhibit-002,fixture-exhibit-001`，确认 Agent 已获取 flat handoff 工具的真实结果。
- 当前返回仍是非历史事实开发 fixture，不可作为真实校史讲解内容，也不应据此发布面向真实用户的 Agent。

下一步期望：

- 先用自然语言问题复测 Agent 是否持续主动调用工具。
- 接入经校史馆/专家核验的真实展品 seed，并保证展品 id 与知识库检索标识可对应。
- 验证 `ready_for_generation`、source safety、路线顺序和知识库引用联合生效后，再准备发布。
- 正式发布前轮换此前暴露过的 API Key，并同步更新插件 Header；发布 Agent 仍需用户明确确认。

### NK-GeniOS Agent 自然语言联动复测通过：2026-10-07

当前结果：

- 用户以“还剩 20 分钟，请先读取参观状态，再安排接下来的参观顺序”进行自然语言复测。
- Agent 返回基于当前参观状态的路线，并保持后端顺序 `fixture-exhibit-002 -> fixture-exhibit-001`，确认日常问法也能触发并使用 handoff 结果。
- Flat 插件、Agent 强制调用规则和自然语言路线回答均已完成联调，不需要切换多 Agent，也不需要继续修改插件。
- 工作区文件检查未发现真实校史馆展品 source package；当前仅有项目定位文档、开发文档和 `data/example_exhibits.fixture.json` 非历史事实 fixture。

下一步期望：

- 由用户提供经核验的校史馆展品资料、展签、馆方文档或可追溯来源文件。
- 将真实资料整理为 exhibit seed，并进行人工来源审核、dry-run、备份和正式导入。
- 真实展品 id 需要与 NK-GeniOS 知识库中的展品标识形成稳定对应，再进行完整 RAG 联调。
- 在真实资料接入、API Key 轮换和发布前检查完成之前，不发布面向真实用户的 Agent。

### 首批公开来源资料清洗完成：2026-10-12

当前结果：

- 输入文件为 `南开大学校史与展陈资料汇编_公开来源核验版_2026-10-09(1).md`，原文件保持不变。
- 新增可重复执行的清洗脚本：`historyguide-backend/scripts/clean_nankai_history_markdown.py`。
- 清洗输出位于 `historyguide-backend/data/cleaned/nankai_history_public_2026-10-09/`。
- 共解析 75 条公开来源、105 条展品／建筑／图版候选、266 条知识 chunks。
- 105 个候选编号无重复，所有引用来源号均可在来源目录解析。
- 89 条候选标记为公开来源已核，16 条保留限制语；全部保持 `import_ready=false`。
- 243 条 chunks 标记为公开来源已核，23 条保留限制语；没有把路线建议混入知识库正文。
- 第7.3节和第11节已移入待馆方补齐清单，第8节路线建议单独保存，第10节书目仅作为复核入口，第12节拆为来源索引。
- 已生成工作人员审核 CSV，预留馆藏号、现场位置、重要度、版权状态、审核人和审核结论字段。
- 已记录输入文件 SHA-256，便于后续确认资料版本未被替换。
- 已生成交付包：`南开校史资料_清洗交付包_2026-10-12.zip`。

验证证据：

- 清洗脚本编译通过。
- JSON、JSONL、CSV 均可解析。
- 候选 ID、后端建议 ID、chunk ID 均无重复。
- 所有候选均未被误标记为可直接导入。
- 清洗知识库不包含路线章节和馆方缺口章节。

下一步期望：

- 先由工作人员审核 `exhibit_candidates.review.csv`，补充馆藏号、当前位置、重要度和版权状态。
- 联系校史馆补齐现行展品清单、展签、馆藏卡、讲解稿、现场动线和图片授权。
- 只有审核结论为通过的候选，才能转换成正式 exhibit seed 并执行 dry-run。
- 后续可以为工作人员增加知识库导入界面，但当前不要绕过人工审核直接导入本批候选。

### “测试样例”知识库导入包完成：2026-10-12

当前结果：

- 新增可重复执行的打包脚本：`historyguide-backend/scripts/build_test_sample_knowledge_base.py`。
- 知识库名称固定为 `测试样例`，状态为 `test_only`，并明确 `publish_allowed=false`。
- 导入目录位于 `historyguide-backend/data/knowledge_bases/测试样例/`。
- 已按主题生成 9 份知识文档和 1 份来源索引，作为 NK-GeniOS 推荐导入文件。
- 已生成备用单文件 `测试样例_完整知识库.md`；若已导入分主题文档，不得再导入该文件，以免检索内容重复。
- 已生成压缩包：`测试样例_知识库导入包_2026-10-12.zip`。
- 每份知识文档均标注“测试样例、非馆方最终审定稿、不得对外发布”，并要求保留待核限制语。
- 导入包不包含路线建议、馆方待补资料、书目审阅稿、展品候选表和 RAG 中间 JSONL。
- 当前后端不承载知识库检索；该包应上传到 NK-GeniOS 的知识库模块，不得写入正式 exhibit 数据库。

验证证据：

- `manifest.json` 中知识库名称为 `测试样例`，共登记 11 份知识文档（10 份推荐导入、1 份备用完整稿）。
- 12 份 Markdown 文件均存在；所有知识文档均有测试用途声明。
- 未检出参观路线章节、待补资料章节或 `fixture-exhibit` 示例编号。
- 压缩包生成成功，大小 56,681 字节。

当前阻塞与续接动作：

- 内置浏览器已打开 NK-GeniOS 地址，但被重定向至南开大学统一身份认证页；当前浏览器会话未保留登录状态。因此尚未在平台上点击创建和上传，不能声称平台导入已经完成。
- 页面恢复后，在“知识库”中新建名为 `测试样例` 的知识库，导入 `00_` 至 `08_` 九份主题文档和 `99_来源索引.md`。
- 导入后先做检索验证，再绑定 Agent；验证成功前不进行下一步，不发布 Agent。
