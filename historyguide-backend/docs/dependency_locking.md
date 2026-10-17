# Python 依赖锁与复验

`requirements.txt`、`requirements-dev.txt` 是直接依赖的允许范围，供维护者修改；
`requirements.lock`、`requirements-dev.lock` 是本轮解析和测试的精确版本及 SHA-256
门禁。普通接管、回归和部署应从锁文件安装，避免再次解析范围源时得到未经测试的版本。
锁文件不含本机临时路径或私密索引配置。

## 安装

在 `historyguide-backend` 中创建 Python 3.11+ 的独立环境后安装开发锁：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r requirements-dev.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

运行环境仅需 `requirements.lock`：

```powershell
python -m pip install --require-hashes -r requirements.lock
python -m pip check
```

需要公开镜像时显式指定索引，例如在安装命令中增加
`--index-url https://pypi.tuna.tsinghua.edu.cn/simple`，并在验证记录中注明来源。
不要把带凭据的索引地址提交到仓库或粘贴到聊天。哈希校验确认下载包匹配锁文件允许的
字节，不能独立证明上游作者、发布过程或索引本身可信。

## 维护

本轮使用 `uv pip compile` 以 Python 3.11 为最低版本做通用平台解析，运行锁中的包
使用已测试开发锁作为约束；开发锁同时受运行锁和已有开发锁约束，保持两套环境一致：

```powershell
uv pip compile requirements.txt --constraint requirements-dev.lock --universal --python-version 3.11 --generate-hashes --no-annotate --no-header -o requirements.lock
uv pip compile requirements-dev.txt --constraint requirements.lock --constraint requirements-dev.lock --universal --python-version 3.11 --generate-hashes --no-annotate --no-header -o requirements-dev.lock
```

这些命令用已有锁约束当前版本，不会自动完成依赖升级。升级某包时须显式更新其允许
范围及约束，再重建两个锁文件；在新环境从锁文件安装并运行相关回归，核对运行锁与
开发锁交集版本一致。检查生成差异和条件依赖后再交付，勿保留生成时的本机路径注释。
公开镜像可通过编译命令的 `--index-url` 指定；本轮使用清华镜像。

通用锁中的条件项不保证已实测所有平台。运行依赖包含 `psycopg[binary]`，供
staging/production 使用 PostgreSQL；本地 SQLite 回归不会加载该驱动，也不能替代
PostgreSQL 并发验收。当前运行锁与开发锁的版本项数量应以重建后的锁文件为准；
Linux 的 `uvloop` 与 Windows 的 `colorama` 按环境标记选择。2026-10-14 在 Windows
Python 3.12.13 的独立虚拟环境 `D:\华为杯\.runtime\lockcheck` 实际以
`uv pip install --require-hashes --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-dev.lock`
安装 32 个适用包，退出码 0。此记录证明该平台的锁安装通过，未证明 Linux 构建或
Python 3.11 实际运行通过，也未完成上游包来源独立核验。

Dockerfile 已改为使用运行锁并启用 `--require-hashes`；锁文件不锁定镜像自身的摘要。
本轮本机 Docker daemon 未启动，尚无新镜像构建或容器内复验结果。构建时记录基础
镜像摘要、软件包索引、最终镜像摘要，再执行目标平台回归及迁移预演。
本轮技术证据与未通过的上线门禁见 `local_validation_2026-10-14.md`。
