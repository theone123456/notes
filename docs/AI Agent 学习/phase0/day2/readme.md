# Day 2 学习笔记：第一次 API 调用

> 环境与配置：火山引擎方舟（豆包）· OpenAI 兼容接口
> 产出脚本：`hello_llm.py`

## ChatCompletion 响应对象解析

> 来源：`print(response)` 加餐探索。SDK 中的响应是一个 Pydantic 类型化对象，支持属性访问和 IDE 自动补全。

### 结构总览

```text
response (ChatCompletion)
├── id
├── choices[] (Choice)
│   ├── finish_reason
│   ├── index
│   ├── logprobs
│   └── message (ChatCompletionMessage)
│       ├── content
│       ├── refusal
│       ├── role
│       ├── annotations
│       ├── audio
│       ├── function_call
│       ├── tool_calls
│       └── reasoning_content
├── created
├── model
├── object
├── moderation
├── service_tier
├── system_fingerprint
└── usage (CompletionUsage)
    ├── prompt_tokens
    ├── completion_tokens
    ├── total_tokens
    ├── completion_tokens_details (CompletionTokensDetails)
    │   ├── accepted_prediction_tokens
    │   ├── audio_tokens
    │   ├── reasoning_tokens
    │   ├── rejected_prediction_tokens
    │   └── text_tokens
    └── prompt_tokens_details (PromptTokensDetails)
        ├── audio_tokens
        ├── cache_write_tokens
        ├── cached_tokens
        ├── image_tokens
        └── text_tokens
```

**重要度标记**：★ 必须掌握　☆ 后续阶段重点（Agent 核心）　○ 了解即可

### 顶层字段

| 字段 | 类型 | 重要度 | 说明 |
|---|---|---|---|
| `choices` | list[Choice] | ★ | 候选回复列表，默认只有 1 条（请求参数 `n>1` 时会有多条） |
| `usage` | CompletionUsage | ★ | 本次调用的 token 消耗统计（Day 4 深入） |
| `id` | str | ○ | 本次响应的唯一标识（如 `chatcmpl-xxx`），排查问题、对账单时用 |
| `created` | int | ○ | 响应生成的 Unix 时间戳（秒） |
| `model` | str | ○ | 实际服务的模型名，可能与请求时传入的不同（可能带具体版本号） |
| `object` | str | ○ | 对象类型，固定为 `"chat.completion"` |
| `system_fingerprint` | str | ○ | 模型版本指纹，用于标识背后模型/系统的具体状态 |
| `service_tier` | str | ○ | 服务等级（如 default / priority），一般不关心 |
| `moderation` | object | ○ | 内容审核相关信息，部分服务商才返回 |

### choices[i] -- 候选回复

| 字段 | 类型 | 重要度 | 说明 |
|---|---|---|---|
| `message` | ChatCompletionMessage | ★ | 消息主体，回复内容在这里 |
| `finish_reason` | str | ★ | **生成结束的原因**，取值见下方详解 |
| `index` | int | ○ | 该候选在列表中的序号，默认 0 |
| `logprobs` | object | ○ | 每个 token 的对数概率（需请求时显式开启），可观察模型"信心" |

#### finish_reason 常见取值（面试高频）

| 取值 | 含义 |
|---|---|
| `stop` | 正常结束（说完了，或碰到停止词） |
| `length` | 达到 `max_tokens` 上限被**截断**--回答突然中断时先查它 |
| `tool_calls` | 模型决定调用工具，正文停在"该调工具了"（**阶段 1/2 的核心信号**） |
| `content_filter` | 内容被安全策略拦截 |

### choices[i].message -- 消息对象

| 字段 | 类型 | 重要度 | 说明 |
|---|---|---|---|
| `content` | str | ★ | **模型回复的正文**，日常 90% 的代码就是在取这个值 |
| `role` | str | ★ | 固定为 `"assistant"`（方便直接拼回 messages 历史） |
| `tool_calls` | list | ☆ | 模型要求调用哪些工具、传什么参数--**Agent 开发的命脉，阶段 1 正式登场** |
| `reasoning_content` | str | ☆ | 思维链内容，仅推理模型（deepseek-reasoner 等）返回 |
| `refusal` | str | ○ | 模型拒绝回答时的原因说明（触发安全策略时） |
| `annotations` | list | ○ | 内容注释（如引用来源、链接） |
| `function_call` | object | ○ | 旧版函数调用字段，已被 `tool_calls` 取代 |
| `audio` | object | ○ | 语音输出模型的音频数据 |

### usage -- token 消耗统计

| 字段 | 类型 | 重要度 | 说明 |
|---|---|---|---|
| `prompt_tokens` | int | ★ | **输入**消耗的 token 数（你发的 messages） |
| `completion_tokens` | int | ★ | **输出**消耗的 token 数（模型生成的回复） |
| `total_tokens` | int | ★ | 两者之和，计费和上下文预算都看它 |

#### prompt_tokens_details -- 输入明细

| 字段 | 说明 |
|---|---|
| `cached_tokens` | ○ 命中前缀缓存的 token 数（这部分通常计费打折，Agent 多轮对话省钱关键） |
| `text_tokens` | ○ 纯文本 token 数 |
| `image_tokens` | ○ 图片输入消耗的 token 数 |
| `audio_tokens` | ○ 音频输入消耗的 token 数 |
| `cache_write_tokens` | ○ 本次写入缓存的 token 数 |

#### completion_tokens_details -- 输出明细

| 字段 | 说明 |
|---|---|
| `reasoning_tokens` | ○ 推理模型"思考"消耗的 token（推理模型贵就贵在这） |
| `text_tokens` | ○ 正文 token 数 |
| `accepted/rejected_prediction_tokens` | ○ 投机采样加速相关的预测 token（底层优化，了解即可） |
| `audio_tokens` | ○ 音频输出 token 数 |

### 取值速查

```python
print(response.id)                              # 响应 ID
print(response.choices[0].finish_reason)        # 结束原因
print(response.choices[0].message.content)      # 回复正文（最常用）
print(response.choices[0].message.role)         # "assistant"
print(response.usage.prompt_tokens)             # 输入 token
print(response.usage.completion_tokens)         # 输出 token
print(response.usage.total_tokens)              # 总 token
```

### 本节记住三件事

1. 回复正文在 `response.choices[0].message.content`
2. 回答异常中断，先看 `finish_reason` 是不是 `length`
3. `tool_calls` 字段现在躺着不用，阶段 1 起它就是主角

---

## 环境变量统一管理

> 目的：API Key 等敏感信息不硬编码、不重复配置、不进 Git 仓库
> 方案：`python-dotenv` 第三方库

### 使用步骤

```bash
pip install python-dotenv
```

1. 在项目根目录创建 `.env` 文件，写入配置（多条换行即可）：

```text
API_KEY="your_api_key"
BASE_URL="your_base_url"
MODEL="your_model_id"
```

2. **将 `.env` 加入 `.gitignore`**（安全关键：不处理的话，Key 会随代码提交泄露）

3. 在 `.py` 文件中加载使用：

```python
import os
from dotenv import load_dotenv

load_dotenv()  # 自动向上查找 .env，也可 load_dotenv("路径/.env") 显式指定

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
```

### 要点速记

| 要点 | 说明 |
|---|---|
| `.env` 永不进 Git | 加入 `.gitignore`；可提交一份不含真实值的 `.env.example` 作模板 |
| 与 `export` 的关系 | `export` 只对当前终端有效；`.env` 持久化，换终端也不用重新设 |
| 命名规范 | 同一服务商的变量可用统一前缀，可读性好、便于整体管理 |
| 优先级 | 已存在的环境变量不会被 `.env` 覆盖（`load_dotenv(override=True)` 可改变此行为） |

### 本节记住三件事

1. `.env` 文件负责存密钥，`.gitignore` 负责挡住它--两者缺一不可
2. `load_dotenv()` 之后，照常用 `os.getenv()` 取值
3. 团队协作时提交 `.env.example`，真实 `.env` 各自本地维护

---

## system prompt 的作用

> 位置：messages 数组中 `role="system"` 的消息（惯例放第一条）
> 本质：不是魔法，就是上下文的开头部分；模型在训练时被教会给予它最高权重

### 五大用途

| 用途 | 英文术语 | 说明 | 示例 |
|---|---|---|---|
| 塑造人设与语气 | Role-Playing | 决定模型的身份、专业背景和说话风格 | "你是一位资深 Python 工程师，回答简洁直接" |
| 规定输出格式 | Formatting Constraints | 强制模型以特定结构返回数据 | "只输出 JSON，字段为 title 和 summary" |
| 设定安全边界 | Safety & Guardrails | 告诉模型什么能说、什么不能说 | "拒绝任何涉及暴力的请求" |
| 提供全局背景 | Context Provision | 贯穿整个会话的全局设定（**注意：不是长期记忆**） | "用户是零基础学员，解释时多用类比" |
| 引导工作流程 | Process Control | 指定模型完成任务的方式与顺序 | "先复述任务，再分步执行，最后总结"（写 Agent 提示词的核心手法） |

### 两个容易误解的点

1. **system prompt ≠ 长期记忆**：它只在当前会话内生效，且内容固定不变；模型不会因为它而"记住"跨会话的历史。真正的长期记忆需要自己工程化实现（向量库存储 + 检索，阶段 2 内容）
2. **优先级高但非绝对**：恶意构造的 user 消息仍可能覆盖它（越狱/prompt injection）。安全关键场景必须配合代码层校验，不能只依赖 system prompt

### 示例代码

```python
messages = [
    {"role": "system", "content": "你是一个毒舌但心软的助手，回答末尾总要补一句关心。"},
    {"role": "user", "content": "我今天学习进度落后了，很焦虑"},
]
```

### 本节记住三件事

1. system prompt 管"怎么答"（人设、格式、边界、流程），user 消息管"答什么"
2. 它的高优先级来自训练，不是玄学；但它不是绝对可靠的防线
3. 写 Agent 时，系统提示词就是 Agent 的"岗位说明书"--阶段 2 会花大量时间打磨它
