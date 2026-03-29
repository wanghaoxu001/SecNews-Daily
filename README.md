# SecNews-Daily

网安情报快报系统 — 每天从 RSS 源抓取安全新闻，经 LLM 翻译/摘要/分类/去重/重要性判断后，由用户筛选编辑并导出快报。

## 快速启动

```bash
# 1. 复制环境变量
cp .env.example .env
# 编辑 .env 设置数据库密码、JWT Secret、管理员凭证

# 2. 启动所有服务
docker compose up --build

# 3. 访问
# 前端: http://localhost:3002
# 后端 API: http://localhost:8000/api/health
# API 文档: http://localhost:8000/docs
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_USER` | 数据库用户名 | `secnews` |
| `POSTGRES_PASSWORD` | 数据库密码 | `secnews_dev_password` |
| `POSTGRES_DB` | 数据库名 | `secnews` |
| `DATABASE_URL` | 异步数据库连接串 | `postgresql+asyncpg://...` |
| `JWT_SECRET` | JWT 签名密钥 | `change-me-to-a-random-string` |
| `ADMIN_USERNAME` | 管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 管理员密码 | `admin123` |
| `LOG_LEVEL` | 日志等级 | `INFO` |
| `LOG_TO_FILE` | 是否写入文件日志 | `true`（Compose 默认） |
| `LOG_FILE_PATH` | 日志文件路径 | `logs/backend.log` |
| `LOG_FILE_MAX_BYTES` | 单文件最大大小（字节） | `10485760` |
| `LOG_FILE_BACKUP_COUNT` | 滚动保留文件数 | `7` |

## 日志持久化

- 后端日志同时输出到容器 stdout 与滚动文件日志。
- `docker-compose` 默认挂载 `./logs/backend:/app/logs`，容器重建后日志仍保留在宿主机。
- 常用查看命令：`docker compose logs -f backend`（stdout）和 `tail -f logs/backend/backend.log`（文件）。

## 开发

```bash
# 后端
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev

# 测试
cd backend && pytest
cd frontend && npx vitest
```

说明：CSV 打标功能依赖后端文件上传解析，后端依赖中已包含 `python-multipart`。如果是增量更新本地环境，重新执行一次 `pip install -r requirements.txt`。

## CSV 打标

### 功能入口

- 登录后可从顶部导航进入 `CSV 打标` 页面。
- 前端路由为 `/tagger`。
- 后端接口挂载在 `/api/v1/tagging-tasks`。

### 使用流程

1. 上传固定模板 CSV 文件。
2. 系统创建打标任务，并从第一条样本开始逐条展示。
3. 点击 `标记重要` 或使用快捷键进行打标，结果会立即保存到后端。
4. 全部样本完成后，点击 `标记完成`。
5. 如需写入重要性样本库，再点击 `导入样本库`。

### CSV 模板要求

- 文件编码必须为 `UTF-8` 或 `UTF-8 with BOM`。
- 表头固定为 `title,summary,category,reason`。
- `title` 和 `category` 不能为空。
- 至少包含 1 行数据。

示例：

```csv
title,summary,category,reason
Apache 漏洞预警,公开 POC 已出现,重大漏洞风险提示,已有利用链
常规版本更新,,其他,例行更新
```

### 页面操作说明

- `标记重要`：将当前样本标为重要；再次点击会在“重要”和“不重要”之间切换。
- `下一条`：保存当前位置并前进一条。
- `上一条`：返回上一条样本。
- `标记完成`：仅当全部样本都已打标时可用。
- `导入样本库`：仅当任务状态为已完成时可用，已存在的重复样本会自动跳过。

快捷键：

- `Space`：将当前样本标为重要并前进。
- `Enter`：前进到下一条。
- `ArrowUp`：返回上一条。

### 本地开发注意事项

- 首次拉取或更新后端后，执行 `cd backend && alembic upgrade head`，确保 `tagging_tasks` 和 `tagging_task_items` 表已创建。
- 如果前端通过 Vite 本地开发服务器访问后端，可通过 `VITE_API_PROXY_TARGET` 覆盖代理目标；默认使用 Docker Compose 服务名 `http://backend:8000`。

## 架构

### 处理流水线

1. **RSS 抓取** — 遍历启用源，按 URL 去重入库
2. **新闻处理** — 翻译标题/摘要 + LLM 分类（五类）
3. **相似性判断** — 实体匹配 + 语义相似度 + 关键词 + LLM 判定
4. **重要性判断** — 策略模式，基于分类典型样本 + LLM 判断

### 技术栈

- **Backend**: Python 3.12 / FastAPI / SQLAlchemy 2.0 / PostgreSQL 17 (pgvector) / APScheduler
- **Frontend**: Vue 3 / TypeScript / Vite / Naive UI / Pinia
- **Deployment**: Docker Compose
