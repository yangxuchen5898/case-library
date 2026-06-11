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
`frontend/tests/e2e/alpha-audit.spec.js` 和 `frontend/tests/e2e/ai-errors.spec.js`：

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

前端测试目录当前先按 E2E 分到 `frontend/tests/e2e/`，并已把 AI 错误提示回归从
主 alpha audit spec 拆出。后续仍应按 #89 继续补 `unit/`、`component/`、
`visual/` 或等价分层，并继续把 `alpha-audit.spec.js` 拆成职责更单一的 spec。

真实 AI 外呼 smoke 是显式 opt-in，不属于默认门禁。仅在 `.env` 中配置真实
`AI_BASE_URL`、`AI_API_KEY`、`AI_MODELS`、`AI_DEFAULT_MODEL` 且显式启用
`AI_REVIEW_ENABLED=true` 时运行：

```bash
docker compose run --rm -e AI_REVIEW_ENABLED=true app make real-ai-smoke
```

该命令通过后端 `/api/cases/{case_id}/ai-review` 触发外部 OpenAI-compatible
provider，不打印 key、base URL 或完整 prompt。无 key 或 disabled 时应验证
disabled/unconfigured 提示，而不是声称真实 AI 已通过。

## Alpha 覆盖矩阵

| 场景 | 当前证据 | 备注 |
| --- | --- | --- |
| 教师创建正文、来源材料、类型和主题 | 后端集成 + mock E2E | E2E 使用 deterministic seed 账号。 |
| AI 成功生成只读版本和段落批注 | 后端集成 + mock E2E | E2E mock AI 响应，不证明外部模型。 |
| AI disabled/unavailable 作者提示 | 后端集成 + `ai-errors.spec.js` | 页面不显示生成版本或批注成功态。 |
| 真实外部 AI API 后端调用 | `make real-ai-smoke` | opt-in，需要 `.env` 和 `AI_REVIEW_ENABLED=true`。 |
| 教师历史版本只读可复制 | mock E2E | 覆盖复制后退回再提交路径。 |
| 管理员段落批注、通过、退回 | 后端集成 + mock E2E | 覆盖非管理员权限的主要后端边界。 |
| 公开 API/UI 不泄露内部审核字段 | 后端集成 + mock E2E | 覆盖正文、元数据、标签、来源材料公开显示。 |
| 移动端创建关键屏可读 | mock E2E | 当前只覆盖创建流三个关键屏，不是完整移动端验收。 |

未充分覆盖：前端 unit/component 测试、稳定视觉 baseline、真实 AI 质量评估、移动端完整
审核/公开链路。

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
