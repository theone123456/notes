# AI Agent 开发学习计划

> 适用背景：熟悉 Python · 每周可投入 5-10 小时 · 目标为求职/转行 · AI 零基础
> 总周期：约 5-6 个月（23 周）
>
> 掌握程度标注：
> - 【必须】求职硬性要求，面试必考
> - 【建议】拉开差距的加分项
> - 【了解】知道概念、能聊两句即可

---

## 学习路线总览

| 阶段 | 主题 | 时长 | 核心产出 |
|---|---|---|---|
| 0 | AI 与大模型基础认知 | 2 周 | API 调用封装类 |
| 1 | Prompt 工程与工具调用 | 3 周 | 带工具的命令行助手 |
| 2 | **Agent 核心原理（手写）** | 4 周 | **纯手写通用 Agent** |
| 3 | RAG 检索增强 | 3 周 | 知识库问答系统 |
| 4 | 主流框架与 MCP | 4 周 | LangGraph 重构 + MCP Server |
| 5 | 多 Agent 与工程化 | 4 周 | 完整多 Agent 应用 |
| 6 | 求职冲刺 | 3 周 | 3 个项目 + 简历 + 面试题库 |

---

## 阶段 0：AI 与大模型基础认知（第 1-2 周）

**目标**：建立对 LLM 的正确直觉，能独立封装 API 调用。

| 知识点 | 程度 |
|---|---|
| LLM 训练过程概念（预训练/微调/对齐） | 【了解】 |
| Token 与 tokenizer、按 token 计费、中文 token 特点 | 【必须】 |
| 上下文窗口（context window）及其限制 | 【必须】 |
| 幻觉（hallucination）的成因 | 【必须】 |
| 主流模型格局：GPT/Claude/Gemini、DeepSeek/Qwen/GLM | 【了解】 |
| 注册 API Key，跑通第一次调用（推荐 DeepSeek/通义，成本低） | 【必须】 |
| Chat Completions 结构：system/user/assistant 三种角色 | 【必须】 |
| 核心参数：temperature、top_p、max_tokens | 【必须】 |

**产出**：
- [x] 一个 Python 类 `LLMClient`，封装 API 调用，支持多轮对话并保存历史（2026-09-05 · Day 8-12 逐日达成并超出基线：历史持久化、错误重试、token 统计与成本估算、命令行界面、11 用例测试、docs；仓库 github.com/theone123456/llm_client）

---

## 阶段 1：Prompt 工程与工具调用（第 3-5 周）

**目标**：掌握 LLM 应用的两大基石——结构化输出和 Function Calling。

| 知识点 | 程度 |
|---|---|
| Prompt 工程原则：角色设定、少样本示例（few-shot）、思维链 CoT | 【必须】 |
| 结构化输出：JSON mode + Pydantic 解析校验 | 【必须】 |
| **Function Calling 完整流程**：定义工具 → 模型决策 → 执行 → 结果回填 → 循环 | 【必须，Agent 的基石】 |
| 流式输出（stream） | 【建议】 |
| 错误处理：超时、重试、rate limit、JSON 解析失败兜底 | 【必须】 |
| Token 成本估算与上下文预算管理 | 【必须】 |
| 多模态输入（图片理解） | 【了解】 |

**产出**：
- [ ] 命令行助手，接入 2-3 个真实工具（如天气 API、计算器、文件读写）
- [ ] 信息抽取 demo：从一段自然语言提取结构化 JSON 并校验

---

## 阶段 2：Agent 核心原理——手写 Agent（第 6-9 周）★ 全计划核心

**目标**：不依赖任何框架，从零理解 Agent 的本质。**这是面试最大的筹码。**

| 知识点 | 程度 |
|---|---|
| Agent 定义：LLM（大脑）+ 工具（手脚）+ 记忆 + 循环 | 【必须】 |
| **ReAct 范式**：Reason → Act → Observe 循环 | 【必须】 |
| 手写 Agent 主循环（while + tool_calls 分发） | 【必须，最重要】 |
| 终止条件设计：模型自主判断完成 / 最大步数 / 死循环防护 | 【必须】 |
| Agent 系统提示词设计（角色、工具说明、输出规范） | 【必须】 |
| 工具注册机制：name/description/JSON Schema 参数定义 | 【必须】 |
| 短期记忆：对话历史管理、截断与摘要压缩策略 | 【必须】 |
| 长期记忆：向量库存取历史经验 | 【建议】 |
| Planning：plan-and-execute 任务分解模式 | 【建议】 |
| 自我反思（Reflexion）机制 | 【了解】 |
| 论文：ReAct、Toolformer、Reflexion | 【了解】 |

**产出**：
- [ ] 纯手写（仅用 requests/openai SDK）一个通用 Agent 框架，具备：工具注册装饰器、多轮 ReAct 循环、对话记忆、执行错误后自动恢复。约 300 行代码，整理成规范的 GitHub 仓库

---

## 阶段 3：RAG 检索增强（第 10-12 周）

**目标**：掌握企业落地最广的场景，国内岗位高频要求。

| 知识点 | 程度 |
|---|---|
| 为什么需要 RAG：私有数据、知识时效、降低幻觉 | 【必须】 |
| Embedding 原理（概念层面即可，不求数学推导） | 【必须】 |
| 文档加载解析：PDF / Word / Markdown / 网页 | 【必须】 |
| **分块策略（chunking）**：固定长度、重叠窗口、按语义/结构分块 | 【必须】 |
| 向量数据库：Chroma 上手 | 【必须】 |
| Qdrant / Milvus / FAISS | 【了解】 |
| 完整检索流程：query → embedding → 相似度检索 → 拼接上下文 | 【必须】 |
| 混合检索：向量 + BM25 关键词 | 【建议】 |
| Rerank 重排序提升精度 | 【建议】 |
| RAG 评估：检索命中率、答案忠实度 | 【了解】 |
| GraphRAG 等前沿方向 | 【了解】 |

**产出**：
- [ ] 个人知识库问答系统——导入自己的文档后可提问并引用出处。要求**先纯手写实现一遍**，再用 LlamaIndex 实现一遍做对比

---

## 阶段 4：主流框架与 MCP（第 13-16 周）

**目标**：掌握工业界主流开发方式，达到岗位 JD 要求。

| 知识点 | 程度 |
|---|---|
| LangChain 核心抽象：ChatModel / PromptTemplate / OutputParser / Tool | 【必须】 |
| LCEL 链式调用语法 | 【建议】 |
| **LangGraph**：状态图、节点与边、条件路由、checkpointer 断点续跑 | 【必须，当前 Agent 开发主流框架】 |
| LangSmith 链路追踪 | 【建议】 |
| **MCP（Model Context Protocol）**：Host/Client/Server 架构、tools/resources/prompts 三大原语 | 【必须，行业标准协议】 |
| 手写一个 MCP Server | 【必须】 |
| 横向了解：OpenAI Agents SDK、CrewAI、AutoGen、Dify/Coze 低代码平台 | 【了解】 |

**产出**：
- [ ] 用 LangGraph 重构阶段 2 的手写 Agent，对比两者差异（写进 README，面试可讲）
- [ ] 开发一个可用的 MCP Server（如本地文件检索、数据库查询），并在 Claude Desktop 等客户端中验证

---

## 阶段 5：多 Agent 系统与工程化（第 17-20 周）

**目标**：具备完整应用的工程能力。

| 知识点 | 程度 |
|---|---|
| 多 Agent 协作模式：路由分发、流水线、supervisor 监督者 | 【必须（至少精通一种）】 |
| Agent 间通信与共享状态 | 【建议】 |
| 人工介入（human-in-the-loop）审批机制 | 【建议】 |
| 评估（evals）：构建测试集、LLM-as-judge 自动评分 | 【必须（入门级）】 |
| 可观测性：tracing、日志、每步耗时与 token 统计 | 【建议】 |
| 安全护栏：prompt injection 防御、工具权限控制、输出过滤 | 【必须（概念与基本手段）】 |
| 服务化：FastAPI 封装 Agent 为 HTTP 接口 | 【必须】 |
| 异步并发处理（asyncio 处理并发请求） | 【建议】 |
| 前端：Streamlit / Gradio 快速搭界面 | 【建议】 |
| Docker 容器化部署 | 【建议】 |

**产出**：
- [ ] 一个完整的多 Agent 应用，例如"研究员 + 写手 + 审校"自动报告生成系统：带 Web 界面、FastAPI 后端、Docker 部署

---

## 阶段 6：求职冲刺（第 21-23 周）

**目标**：把学习成果转化为 offer。

| 任务 | 程度 |
|---|---|
| 项目整理：GitHub 仓库规范化（README、架构图、效果演示 GIF） | 【必须】 |
| 简历：项目用 STAR 法则描述，量化指标（准确率、耗时、成本） | 【必须】 |
| 面试高频题准备（见下方清单） | 【必须】 |
| 机器学习基础八股（转行可能被问） | 【了解】 |

**面试必背题清单**：
1. Agent 的运行循环原理？如何防止死循环和失控？
2. Function Calling 中模型返回非法参数怎么办？
3. 幻觉的成因与缓解手段（RAG、提示词约束、结构化输出）
4. 长对话的上下文管理策略（截断/摘要/向量检索记忆）
5. RAG 效果差如何排查和优化（分块 → 检索 → rerank → 生成逐层分析）
6. 什么场景需要多 Agent，什么场景单 Agent 就够？
7. prompt injection 是什么，如何防御？

**产出**：
- [ ] 3 个核心项目仓库 + 简历 + 个人面试题库

---

## 学习资源（按优先级）

1. **官方文档（第一优先）**：Anthropic 的 Agent 构建指南（质量极高）、OpenAI Cookbook、LangChain/LangGraph 文档、MCP 官网
2. **免费课程**：DeepLearning.AI 短课程平台（每门 1-2 小时，有 Agent、RAG、MCP 专题）
3. **论文（了解级）**：ReAct、Toolformer、Reflexion
4. **源码阅读**：GitHub 上高星开源 Agent 项目，对照阶段 2 的手写代码理解
5. **信息源**：各模型厂商官方博客、Hugging Face 博客

## 学习方法建议

- **时间配比**：50% 写代码、30% 啃官方文档、20% 看课程/文章——看懂 ≠ 会写
- **手写优先于框架**：先裸写一遍再用框架，面试时"我知道框架背后做了什么"是降维打击
- **每阶段必须交付产出物**，没有产出就退回重学
- **把 AI 当导师**：概念看不懂就让它换方式解释，写完代码让它 review
