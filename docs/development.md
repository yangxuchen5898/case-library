# 开发指南

## 本地启动

本项目强制使用 Docker Compose / Dev Container 作为开发和验证环境。本机没有完整
项目运行环境，不应在宿主机直接安装依赖、运行后端、运行前端或执行测试。

```bash
docker compose up -d --build
```

服务地址：

- 后端：`http://127.0.0.1:8001`
- 前端：`http://127.0.0.1:18080`
- Swagger：`http://127.0.0.1:8001/docs`

## 网络问题

若 Docker 拉取镜像或安装依赖失败，先确认是否是网络问题：

```bash
curl -I --max-time 8 https://github.com
curl -I --max-time 8 https://registry-1.docker.io/v2/
```

当前环境中 Docker Hub 直连可能超时。若需要代理，应通过本机环境变量、Docker daemon
代理配置或团队约定的开发环境配置显式启用，不要把个人 shell 函数写入仓库配置。

```bash
curl -I --max-time 8 https://registry-1.docker.io/v2/
```

代理可用时，Docker Registry 应返回 `401 Unauthorized`，这是未登录 registry 的正常响应。

## 常用命令

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose run --rm app make check
docker compose config --quiet
docker compose down
```

允许在宿主机执行的操作仅限于：git、文档编辑、文件搜索、网络诊断、Docker/Compose
控制命令。所有项目运行、依赖安装、lint、测试、构建都必须在容器内完成。

## 前端依赖异常

如果 Vite 或 node_modules 损坏，只重置前端依赖卷：

```bash
docker compose stop frontend
docker volume rm case-library_frontend_node_modules
docker compose up -d frontend
```

## 开发约束

- 不提交 `.env`、密钥、私有 URL、代理地址。
- 不提交原始运行数据、Mongo dump、上传材料。
- 不从历史目录整文件复制实现。
- 不在宿主机安装或运行项目依赖；使用容器。
- 改 API 时同步 schema、测试和 `docs/api.md`。
- 改 AI 行为时同步 `docs/ai.md` 和相关测试。
- 改产品流程时先更新 `docs/prd.md`。

## PR 与合并规范

- 每个 PR 应聚焦一个 GitHub Issue 或一个明确维护切片，不混入无关重构、格式化或本地工具状态。
- PR 描述必须说明变更范围、验证证据、关联 issue，以及未运行检查的原因。
- 新建、重新打开、标记 ready for review 或更新 PR 后，应触发 Codex review。也可以在 PR 中评论
  `@codex review` 手动触发。
- 合并前必须确认该 PR 当前 head，也就是最后一发 commit，已经完成 Codex review。旧 commit
  上的 review 不能作为新提交后的合并依据。
- 本仓库已在 PR #100 验证 `@codex review` 可用：`chatgpt-codex-connector` 会回复审查结果。
- 如果 Codex review 检查早于机器人回复而失败，在 Codex 回复后重新运行该检查，或 push 新提交
  触发检查重跑。
- 机器人审查、人工审查和 CI 反馈必须逐条处理。已修复的评论说明修复提交；不采纳的评论说明理由。
- 所有 PR review conversations 必须在合并前 resolve。未 resolve 的 review thread 视为阻塞合并；
  即使评论已 outdated，只要 GitHub 仍显示未 resolve，也需要手动 resolve。
- 如果 resolve review thread 后治理检查未自动重跑，在 GitHub Actions 中手动 rerun 对应检查，
  或 push 新提交触发检查重跑。
- 合并前必须确保必需检查通过，包括 CI、Codex review 检查和 unresolved review thread 检查。
- 不要在 PR 评论里粘贴密钥、`.env` 内容、私有 URL、代理配置或未脱敏数据。

推荐分支保护或 ruleset 设置：

- 禁止直接 push 到主干分支，所有变更通过 PR 合并。
- 要求通过 CI 和 PR 治理检查。
- 要求所有 review conversations resolved。
- push 新提交后 dismiss stale reviews。
