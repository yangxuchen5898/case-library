## 变更范围

-

## 关联 Issue

- Closes #

## 验证

- [ ] `docker compose up -d --build`
- [ ] `curl -fsS http://127.0.0.1:8001/api/constants`
- [ ] `curl -fsS http://127.0.0.1:18080/`
- [ ] `docker compose ps`
- [ ] `docker compose run --rm app make check`
- [ ] `docker compose config --quiet`
- [ ] `git diff --check`

未运行的检查及原因：

- 示例：本次仅修改文档，未运行完整 Docker 门禁。

## 合并前检查

- [ ] 当前 PR 最后一发 commit 已完成 Codex review 和 Copilot review；Codex 可用 `@codex review` 触发，Copilot 需从 Reviewers 菜单请求或依赖仓库自动 review
- [ ] 已处理所有 AI review 和人工 review 反馈；修复回复写明 `已在 commit <hash> 修复：...`，不采纳回复写明 `Rebuttal：...`
- [ ] 所有 review conversations 已先回复、再 resolve
- [ ] CI 和 PR 治理检查均通过
- [ ] 未提交 `.env`、密钥、私有 URL、代理配置、原始数据或本地工具状态
