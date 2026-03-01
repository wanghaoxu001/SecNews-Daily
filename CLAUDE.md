# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SecNews-Daily — 网安情报快报系统。单用户系统，每天从 RSS 源抓取安全新闻，经 LLM 翻译/摘要/分类/去重/重要性判断后，由用户筛选编辑并导出 PDF 快报。

## Tech Stack

- **Backend**: Python 3.12 / FastAPI（全异步），SQLAlchemy 2.0 async + Alembic + PostgreSQL 17（pgvector），APScheduler 定时任务
- **Frontend**: Vue 3 (Composition API) + TypeScript + Vite，Naive UI，Pinia，vuedraggable
- **Deployment**: Docker Compose（backend + frontend + postgres）
- **Auth**: JWT（用户名密码来自环境变量，不建用户表）

## Build & Run Commands

```bash
# Backend
cd backend
pip install -r requirements.txt    # or: uv sync
alembic upgrade head               # run migrations
uvicorn app.main:app --reload      # dev server

# Frontend
cd frontend
npm install
npm run dev                        # Vite dev server
npm run build                      # production build

# Tests
cd backend && pytest               # all backend tests
pytest tests/test_xxx.py::test_fn  # single test
cd frontend && npx vitest          # all frontend tests
npx vitest run src/xxx.test.ts     # single test

# Docker
docker compose up --build
```

## Architecture

### Backend Processing Pipeline

四个模块按序串联，定时或手动触发，每个模块也可单独执行：

1. **RSS 抓取** — 遍历启用源，按 URL 去重入库（status=pending），单源失败不阻塞
2. **新闻初步处理** — 对 pending 新闻：获取中文摘要（有摘要则翻译，无则抓正文生成）→ 翻译标题 → LLM 分类为五类之一 → status=processed。幂等设计，失败可断点重跑
3. **相似性判断** — 对 processed 新闻，与近 N 天已发布快报新闻对比：实体匹配 + pgvector 语义相似度 + TF-IDF 关键词重叠加权初筛，超阈值候选送 LLM 最终判定
4. **重要性判断** — 策略模式，当前子模块 A：取同分类典型样本构建 prompt（利用 prompt caching），LLM 返回是否重要 + 理由

### Core Data Models

- **RssSource** — RSS 源配置
- **News** — 新闻主表，含原文/译文/分类/处理状态/embedding(vector)/相似性标记/重要性标记
- **Briefing / BriefingItem** — 快报及条目，条目从 News 预填充标题摘要
- **LlmConfig** — 按 task_type（translate/summarize/classify/similarity/importance/embedding）配置模型参数，有全局 default 记录可继承
- **TaskConfig** — 定时任务 cron 配置
- **ImportanceExample** — 重要性判断的典型样本
- **ProcessingConfig** — 各模块可调参数 key-value 表

### Key Enums

- `ProcessStatus`: pending → processing → processed → similarity_checked → completed / failed
- `NewsCategory`: 金融业网络安全事件 / 重大网络安全事件 / 重大数据泄露事件 / 重大漏洞风险提示 / 其他

### Frontend Pages

- **登录页** — 简洁登录，token 存 localStorage
- **今日新闻** — 卡片列表 + 筛选 + 勾选 + 详情抽屉 + 浏览进度条 + 生成快报
- **快报列表 / 编辑页** — 按分类分组，拖拽排序，编辑标题摘要，PDF 导出（暂置灰）
- **管理页面** — LLM 配置 / RSS 源管理 / 定时任务 / 处理参数 / 重要性样本 / 重要性策略

## Git Conventions

- `main` 始终可部署；功能分支 `feature/xxx`，修复分支 `fix/xxx`
- Conventional Commits: `feat:` / `fix:` / `refactor:` / `docs:` / `test:`
- 合并前须通过全部测试

## Key Dependencies

- **Backend**: feedparser (RSS), Crawl4AI (正文抓取), httpx (async LLM 调用, OpenAI 兼容接口), langdetect (语言检测), jieba (中文分词)
- **Frontend**: axios, vuedraggable (SortableJS)

## Testing Strategy

- 后端：API 路由集成测试 + 处理流水线各模块单元测试，LLM/外部依赖用 mock
- 前端：交互逻辑组件单元测试（勾选缓存、滚动进度、筛选等）
- 核心业务逻辑必须有测试覆盖
