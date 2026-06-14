# AI Agent 规则

本文件记录 Claude Code 或其他 AI agent 在本仓库工作的补充规范。通用开发规范以
`AGENTS.md` 为准；如需为特定 agent 增加额外约束，可以新增或修改对应的 agent
专属文件，但不要修改 `AGENTS.md`。

## 仓库边界

- 只在当前仓库内工作，不从历史目录或外部项目整文件复制实现。
- 本地 agent 提示词、运行记录、截图、审查草稿和临时报告应放在已忽略目录中，不要提交。
- 不提交与本地编排工具、个人 shell 函数、代理、窗口管理器或临时会话有关的习惯配置。

## 密钥与数据

- 不打印、提交或暴露 `AI_API_KEY`、`.env`、账号表、Mongo dump、上传材料、浏览器会话、
  私有 token、代理地址或私有服务地址。
- `.env.example` 只能包含配置名和非敏感示例。
- 产品 AI 调用必须经过后端，浏览器端不得接收模型供应商凭据。
- 原始运行数据和上传材料不得进入 git，除非已经转化为经过审查的 fixture 或文档。

## AI 产品语义

`AI 审核` 表示作者侧提交前自查，是供人工专家审核参考的建议材料，不代表自动通过、
自动退回或管理员审核。

当前 alpha 语义：

- prompt 元数据入口：`GET /api/prompts?category=alpha`
- AI 自查入口：`POST /api/cases/{case_id}/ai-review`
- AI 自查会生成绑定版本的只读段落批注快照
- `workflow/*` prompt 和 `POST /api/ai/chat` 是兼容接口，不是 alpha 教师自查主路径
- 提交给人工审核的 advisory 记录位于 `ai_reviews`，最多保留 3 条
- AI 禁用或不可用时，不伪造 AI 输出

修改 AI 行为时，同步 `docs/api.md`、`docs/project.md`、`docs/prd.md`、`docs/ai.md` 和相关
GitHub Issue。

## Worker 行为

- 一次只处理一个 GitHub Issue 或一个聚焦维护切片。
- 未经明确授权，不提交、不推送、不删除 worktree、不删除 Docker volume、不关闭 issue。
- 不读取 secrets，不扩大任务范围。
- 运行与改动范围匹配的检查，并说明未运行的检查。
- 如果 worker prompt 要求 `DONE <role>` 结尾，最终报告必须包含该哨兵行。

## PR Review 纪律

- 处理 PR review feedback 时，不能只修改代码；修完对应反馈后必须及时 resolve 对应的
  GitHub review conversation。
- resolve review conversation 前，必须先在对应 thread 下回复处理结果。修复类回复写
  `已在 commit <hash> 修复：<根因和改法>`；不采纳时写
  `Rebuttal：<不采纳原因和风险判断>`。没有回复说明不得直接 resolve。
- 合并前看的是当前 PR head，也就是最后一发 commit 的 review 状态。旧 commit 上的
  Codex review 或人工 review 不能作为新提交后的合并依据。
- Draft PR 上被 skipped 的治理检查不代表最终可合并；标记 ready for review 后必须重新
  确认 Codex review、review conversations 和 CI 状态。
- 读取 Codex review 时要查 PR reviews 和 review comments，不要只看 issue comments；
  GitHub 页面里的 inline review 可能不会出现在普通 PR timeline comments 中。

## 验证

实现或脚手架改动完成前，使用 `docs/project.md` 中的质量门禁；小范围文档变更可以只跑
最小检查，并在汇报中说明原因。

```bash
docker compose run --rm app make check
docker compose config --quiet
git diff --check
```
