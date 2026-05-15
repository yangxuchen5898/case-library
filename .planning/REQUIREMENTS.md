# Requirements

## REQ-01: Classification Test Framework
**Type:** Functional
**Phase:** Phase 1

建立分类 skill 的准确率测试框架：
- 调用 OpenAI API（通过环境变量配置 base_url/api_key/model）
- API 返回 JSON 格式分类结果
- 解析 JSON 并与人工标注对比
- pytest 自动化测试，准确率 ≥ 80%
- 测试数据集基于已有思政案例素材（第一批5个案例）

## REQ-02: Audit Skill Prototype
**Type:** Functional
**Phase:** Phase 1

开发审核 skill 原型：
- 硬审核：格式合规检查（字数、结构必填项）
- 软审核：LLM 标记疑似问题（风格过度、表述存疑），高亮提醒但不自动拦截
- 政治/事实标准：严格把控政治方向、价值导向和事实表述
- 输出审核报告，支持人工复核

## REQ-03: Fact Verification Infrastructure
**Type:** Functional
**Phase:** Phase 1

建立事实核查基础设施：
- web fetch 验证引用来源、政策文件、数据是否真实存在
- 爬虫能力用于素材真实性验证
- 被审核 skill 调用

## REQ-04: LLM API Configuration
**Type:** Non-functional
**Phase:** Phase 1

支持可配置的 LLM API：
- 环境变量：OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL
- 生产环境支持 deepseek 和 qwen
- 学校已提供 OpenAI 兼容 API，已测试可用

## REQ-05: Test Dataset
**Type:** Functional
**Phase:** Phase 1

构建测试数据集：
- 基于已有5个思政案例作为第一批测试素材
- 人工标注分类标签（TYPE_A/B/C + 主题）
- 标注审核标准参考（政治/事实/风格）
