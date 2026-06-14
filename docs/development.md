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

## 演示账号与 E2E seed

默认 `docker compose up` 不再创建固定密码的 E2E 演示账号和演示案例。
`scripts/seed_e2e_accounts.py` 只在 `ENABLE_DEMO_SEED=true` 时执行。

开发/E2E 环境使用 dev compose，默认启用 seed：

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

如需在 dev 环境下也关闭 seed：

```bash
ENABLE_DEMO_SEED=false docker compose -f docker-compose.dev.yml up -d --build
```

手动触发 seed：

```bash
make dev-seed
```

容器化 E2E 入口使用同一套 dev compose seed 路径：

```bash
make smoke-e2e
```

`make smoke-e2e` 会启动 `docker-compose.dev.yml`。如果已经用默认
`docker compose up -d --build` 启动了服务，两个 compose 项目会占用同一组本地端口；
请先执行 `docker compose down`，或本次直接从 dev compose 启动。

## 开发约束

- 不提交 `.env`、密钥、私有 URL、代理地址。
- 不提交原始运行数据、Mongo dump、上传材料。
- 不从历史目录整文件复制实现。
- 不在宿主机安装或运行项目依赖；使用容器。
- 改 API 时同步 schema、测试和 `docs/api.md`。
- 改 AI 行为时同步 `docs/ai.md` 和相关测试。
- 改产品流程时先更新 `docs/prd.md`。
