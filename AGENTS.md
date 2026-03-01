# Repository Guidelines

## 项目结构与模块职责
- `backend/app/`：FastAPI 全异步后端，按 `api/v1`、`services`、`models`、`schemas`、`crud` 分层。
- `backend/alembic/versions/`：数据库迁移脚本（PostgreSQL 17 + pgvector）。
- `backend/tests/`：后端测试（API 集成 + 流水线单元），公共夹具在 `conftest.py`。
- `frontend/src/`：Vue 3 + TypeScript 前端（`views`、`components`、`stores`、`api`、`router`）。
- 根目录：`docker-compose.yml`、`.env.example` 负责本地整体运行配置。

## 构建、测试与开发命令
- `docker compose up --build`：启动 `postgres + backend + frontend` 全栈。
- `cd backend && pip install -r requirements.txt`：安装后端依赖。
- `cd backend && alembic upgrade head`：执行迁移。
- `cd backend && uvicorn app.main:app --reload`：本地启动后端。
- `cd backend && pytest`：运行后端全部测试；单测示例：`pytest tests/test_api.py::test_login_success`。
- `cd frontend && npm install && npm run dev`：启动前端开发环境。
- `cd frontend && npm run build`：类型检查并构建。
- `cd frontend && npm test`：运行 Vitest；单测示例：`npx vitest run src/xxx.test.ts`。

## 编码规范与实现约束
- Python 使用 4 空格缩进；TypeScript/Vue 保持现有风格（2 空格、组合式 API）。
- 命名：Python 用 `snake_case`，类与 Vue 组件文件用 `PascalCase`，组合函数用 `useXxx`。
- API 层只做参数校验与编排，核心逻辑放在 `services`。
- 处理流水线按顺序实现并保持幂等：`RSS抓取 -> 初步处理 -> 相似性判断 -> 重要性判断`。
- 认证为单用户 JWT：用户名/密码来自环境变量，不新增用户表；前端 token 存 `localStorage`。

## 测试要求
- 后端使用 `pytest + pytest-asyncio + httpx`；外部依赖（LLM、RSS、抓取）必须 mock。
- 新增或修改 API 时，至少覆盖成功、鉴权失败、参数异常三类场景。
- 核心业务（分类、去重、重要性判断、快报生成）必须有测试，不强制覆盖率数字。
- 前端重点覆盖交互逻辑（筛选、勾选缓存、滚动进度、拖拽排序等）。

## 提交与 PR 规范
- 分支：`feature/xxx`、`fix/xxx`；`main` 保持可部署。
- 提交信息遵循 Conventional Commits：`feat:`、`fix:`、`refactor:`、`docs:`、`test:`。
- PR 必须包含：变更说明、测试结果（命令与结论）、涉及配置/迁移说明；UI 改动附截图。

## 安全与配置
- 先执行 `cp .env.example .env`，禁止提交真实密钥。
- 生产环境必须替换 `JWT_SECRET` 和默认管理员凭据。
- 合并涉及模型或字段变更的代码前，确认 Alembic 迁移可执行且可回滚。
