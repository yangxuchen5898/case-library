# Roadmap

## Phase 1: Skills Testbench & Audit Prototype

**Goal:** 建立可量化的 skill 测试体系，开发审核 skill 原型，完成 alpha 版本基础能力验证。

**Deliverables:**
- 分类准确率测试框架（pytest + 人工标注数据集）
- 审核 skill 原型（硬审核自动化 + 软审核辅助人工）
- 事实核查基础设施（web fetch / 爬虫）
- 测试数据集（基于已有思政案例素材）

**Requirements:** REQ-01, REQ-02, REQ-03, REQ-04, REQ-05

**Plans:** 4 plans in 3 waves

**Status:** Planned

Plans:
- [ ] 01-01-PLAN.md — LLM API client module + environment configuration
- [ ] 01-02-PLAN.md — Classification test framework with ground truth dataset
- [ ] 01-03-PLAN.md — Fact verification infrastructure (web fetch + crawler)
- [ ] 01-04-PLAN.md — Audit skill prototype (hard checks + soft AI-assisted checks)

---

## Phase 2: Alpha Release & Skill Optimization

**Goal:** 基于 testbench 反馈优化 skills，完成 alpha 版本发布。

**Status:** Planned
