# 馆员工作台

`GET /operator` 提供与后端同源的中文工作台。页面支持来源原文和展品的 JSON
预览/导入、资料详情、来源审批/撤销、展品来源关联、展品审批/撤销及审计记录。
这是本地实现；真实馆员验收、馆方签字资料和 staging 部署仍需单独记录。

## Windows 本地启动

在 `historyguide-backend` 下准备 Python 3.11+ 的 `.venv`，按
`docs/dependency_locking.md` 从 `requirements-dev.lock` 安装开发依赖后运行：

```powershell
.\scripts\start_local_workspace.ps1
```

按隐藏输入提示选择**新的本地操作员密钥**，再打开
`http://127.0.0.1:8000/operator`，输入同一个密钥和实际审核人姓名。
可通过 `-Port 8001` 改端口。该脚本只监听回环地址，使用独立的
`.local/workspace.db`，只对不存在的本地库执行首次迁移，不读取旧线上密钥文件。
已有本地库版本不匹配时启动失败，须先备份、预演并按迁移文档处理。
退出时恢复此前的进程环境变量。若 PowerShell 执行策略禁止脚本，使用获组织允许的
终端执行方式；不要为本项目全局关闭安全策略。

共享环境必须先通过运行配置、备份和迁移门禁，并配置独立操作员密钥、HTTPS 和
工作人员访问限制。工作台复用当前密钥体系，不提供个人账号、身份认证或完整 RBAC。
姓名只是审计字段，馆方须另行核实实际审核身份。

## 来源流程

1. 打开原始档案或获授权的原文，人工整理最多 20 条 JSON 记录。原文不经模型改写。
2. 在工作台选择“来源原文”，选择 UTF-8 `.json` 文件或粘贴内容。
3. “校验并预览”仅检查字段、重复 ID、数据库冲突及正文指纹，不写入数据或审计。
4. 核对内容并勾选确认后导入。所有记录固定为 `draft`，重复 ID 或事务失败整批回滚。
5. 在“来源审核”查看完整摘录和原始出处，确认实际审批责任人后逐条批准或撤销。
   已撤销来源不能再批准，应以新的版本 ID 重新提交。

支持数组或以下对象格式（仅字段示意，不能当正式资料导入）：

```json
{
  "sources": [
    {
      "id": "S01",
      "title": "资料标题",
      "source_uri": "museum-archive:原始档案号",
      "content_text": "经人工核对的原文摘录"
    }
  ]
}
```

来源 ID 须与 Coze 引用 ID 对应，使用 1～64 个 ASCII 安全字符
`[A-Za-z0-9][A-Za-z0-9._:-]*`。正文最多 100,000 字符，标题最多 200 字符，出处最多
2,000 字符；空白内容和额外字段（如伪造 `status=approved`）被拒绝。
清洗包仅有来源元数据和候选知识，不是此格式的已核对来源原文，不自动导入或批准。
日期、授权、原文版本及馆方签字记录仍需放入出处描述或独立的馆方资料清单。

## 展品流程

选择“展品记录”，上传现有展品 seed JSON 数组，或用 `{"exhibits": [...]}` 包装。
每批同样最多 20 条。字段见 `docs/exhibit_seed_format.md`；工作台额外检查稳定 ID、
非空描述/时期/出处及模型长度上限。展品数据与导入审计在**同一事务**提交，CLI 也复用
该事务逻辑。导入不生成审批、不自动关联来源。

在“展品治理”核对详情，关联已有来源 ID；所有关联来源均已批准且正文指纹一致后，
由馆员批准展品。展品变更、来源撤销或指纹失效会在详情中显示门禁问题。
开发 fixture 展品不能批准。撤销展品审批后，新讲解需重新准备并审核。

来源撤销不会抹除展品既有审批的历史记录，应以当前 `approval_issue` 判定能否进入讲解。
来源修订以新 ID 导入并重新关联、核对和审批；不要通过修改 fixture 名称绕过门禁。
JSON 中的 `source_reference` 不会自动创建来源记录或展品关联。

## API 与权限

下列接口均要求 `X-HistoryGuide-Operator-Key`。未配置操作员密钥时返回 503，
缺失或错误密钥返回 401，业务密钥不能替代操作员密钥。

| 接口 | 行为 |
| --- | --- |
| `POST /api/evidence/sources/batch/preview` | 来源只读预览 |
| `POST /api/evidence/sources/batch` | 原子导入来源草稿 |
| `POST /api/evidence/exhibits/batch/preview` | 展品只读预览 |
| `POST /api/evidence/exhibits/batch` | 原子导入待审批展品 |
| `GET /api/evidence/exhibits` | 分页查询展品、审批状态、来源 ID 与当前门禁问题 |
| `GET /api/evidence/exhibits/{exhibit_id}` | 展品治理详情 |

批准、撤销和关联来源复用既有 `/api/evidence` API，操作记录复用
`GET /api/audit-logs`。预览不占用 ID，提交时再次验证；其他操作员抢先导入时返回 409。
上传限制为 8 MiB，服务端在 JSON 解析前按流累计限制大小，含无 Content-Length 请求。
上传不会写入服务器文件，也不会读取客户端路径或从提供的 URI 抓取内容。

页面支持 JSON 数组并在发送时包装为 `sources` 或 `exhibits` 对象；直接调用 API 时
必须使用对应的对象格式。字段错误返回 422、冲突返回 409、超限返回 413。预览成功后
编辑正文须重新预览，提交前核对本批记录和实际审核人。审核人姓名须非空且最多 80 字符，
与来源/展品审批存储字段上限一致；姓名字段不能代替身份核验。

页面壳及两份静态资源公开，包含零资料或配置密钥；资料必须经鉴权后读取。
密钥仅保留在页面内存，不放入 URL、Cookie 或浏览器存储；退出/刷新清除。
401 会立即清除连接、关闭详情并取消在途请求。页面和证据响应使用 `Cache-Control: no-store`，
页面 CSP 限制同源脚本、样式和请求并禁止被嵌入。原文只以文本呈现，原始出处链接仅允许
HTTP/HTTPS，并使用 `noopener noreferrer`。实际部署仍需 HTTPS、访问限制与日志脱敏。

## 后续验收

工程回归：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
npm --prefix tests/browser ci
npm --prefix tests/browser test
```

浏览器回归会自行创建隔离测试库、随机测试密钥及仅监听回环地址的服务，结束后关闭
服务并移除测试库；不接受线上地址或密钥作为输入。Windows 默认使用已安装的 Edge
或 Chrome，可通过 `BROWSER_EXECUTABLE_PATH` 指定本机浏览器；其他环境先按
Playwright 文档安装 Chromium。桌面/手机截图和脱敏结果写入忽略的
`.local/browser-artifacts/`。测试资料是非历史工程样例。

本地 API/浏览器测试只证明工程行为，不证明史实正确或馆方批准。
此页面不承担 Coze 同步、按句语义支持检查、工作流强制 finalize、线上密钥轮换或发布。
仍需真实来源与展品、馆员试用签收、Coze 双路径轨迹和独立的 staging/生产运维证据。

本次 Windows 续做的环境、首轮失败及最终回归记录见
`docs/local_validation_2026-10-14.md`；历史服务器 staging 记录不能证明本轮代码已部署。
