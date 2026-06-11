# 质量门禁

当前强制门禁由 Docker Compose 容器执行。本机没有完整项目运行环境，除纯文档检查外，
不要在宿主机直接运行项目依赖、测试或构建。

## 标准门禁

```bash
docker compose up -d --build
curl -fsS http://127.0.0.1:8001/api/constants
curl -fsS http://127.0.0.1:18080/
docker compose ps
docker compose run --rm app make check
docker compose config --quiet
git diff --check
```

`make check` 当前包含：

- `ruff check backend`
- 后端提交流集成测试 `tests/backend/integration/test_submit_flow.py`
- 前端依赖安装和 `npm run build`

## E2E

前端 Playwright smoke 也应在容器环境中运行；仅在已确认宿主机环境完整时才可临时
使用本机命令。

```bash
docker compose -f docker-compose.dev.yml --profile e2e run --rm e2e
```

容器化 E2E：

```bash
docker compose -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.dev.yml --profile e2e run --rm e2e
```

当前 `e2e` profile 运行 mock E2E 命令 `npm run test:e2e:mock`，对应
`frontend/tests/audit.spec.js`：

- `chromium-desktop`：默认管理员强制改密、创建流作者身份不读旧草稿、教师创建/AI
  自查/提交、教师历史版本、管理员版本化段落批注、退回修改后教师查看人工批注并复制
  版本再提交、管理员通过再提交版本、公开检索、案例库公开字段白名单、首页公开详情
  来源材料和内部审核信息不渲染。
- `chromium-mobile`：创建案例基本信息、案例内容、分类选择三个关键屏的可读性和截图。

当前矩阵中移动端只跑移动专属可读性测试；桌面专属验收流在移动项目中显式 skip。
Playwright 截图、trace、video 和 `.last-run.json` 写入
`frontend/test-results/playwright/`，该目录已忽略，不提交。`agent-runs/` 仅用于
worker/agent prompt、rmux capture 和一次性报告，不作为测试产物目录。

当前 E2E 中 AI 审核成功路径使用 Playwright route mock，验证的是前端只读版本、
段落批注和提交流程，不证明外部模型 API 已被真实调用。AI disabled 场景有前端提示
回归测试，验证后端返回 `disabled` 时页面不崩溃且展示明确错误。

真实 AI 外呼 smoke 是显式 opt-in，不属于默认门禁。仅在 `.env` 中配置真实
`AI_BASE_URL`、`AI_API_KEY`、`AI_MODELS`、`AI_DEFAULT_MODEL` 且显式启用
`AI_REVIEW_ENABLED=true` 时运行：

```bash
docker compose run --rm -e AI_REVIEW_ENABLED=true app make real-ai-smoke
```

该命令通过后端 `/api/cases/{case_id}/ai-review` 触发外部 OpenAI-compatible
provider，不打印 key、base URL 或完整 prompt。无 key 或 disabled 时应验证
disabled/unconfigured 提示，而不是声称真实 AI 已通过。

## 允许缩小门禁的情况

纯文档修改可只运行：

```bash
git diff --check
```

并在汇报中说明未运行完整 Compose 门禁。

## 扩展方向

- 为 AI JSON contract 增加更严格的 schema 边界测试；当前已覆盖 disabled、
  parse_failed、invalid_contract 和主成功路径。
- 为前端批注页增加 Playwright 截图/交互测试。
