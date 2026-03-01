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
# 前端: http://localhost:3000
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
