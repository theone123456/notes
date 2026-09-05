# llm_client

基于 OpenAI 兼容接口的命令行 LLM 聊天客户端：多轮对话、历史持久化、错误重试、token 用量统计与成本估算。

## 功能

- **多轮对话**：自动维护对话历史，模型记得本轮会话中说过的话
- **历史持久化**：退出自动保存到运行目录的 `history.json`，下次 `/resume` 恢复
- **错误重试**：网络类错误（超时 / 连接 / 限流）指数退避重试；鉴权 / 配额类错误快速失败，提示明确
- **用量统计**：会话结束打印输入 / 输出 / 缓存命中 token 数与估算费用
- **命令行界面**：三个本地命令，不消耗 token

## 快速开始

环境要求：Python 3.10+

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. 配置环境变量：从模板复制，填入你的 Key
cp .env.example .env

# 3. 启动（在项目根目录运行）
python -m llm_client.cli
```

`.env` 需要两个变量：

| 变量 | 说明 |
|---|---|
| `API_KEY` | 模型服务商的 API Key（未配置时启动会直接提示） |
| `BASE_URL` | OpenAI 兼容接口地址（火山方舟、DeepSeek 等）。使用非 OpenAI 服务商时必填；不配置则请求发往官方 OpenAI 接口 |

## 命令

以下命令本地处理、不发送给模型（严格匹配）：

| 命令 | 作用 |
|---|---|
| `/exit` | 保存历史、打印用量报告，退出 |
| `/clear` | 清空当前对话、保留人设（system 消息）；用量统计不清零 |
| `/resume` | 从 `history.json` 整体恢复上次会话（当前未保存的对话会被丢弃，有提示） |

其余输入作为聊天内容发送；Ctrl+C / Ctrl+D 与 `/exit` 走同一收尾流程（保存 + 报告）。

## 参数

`LLMClient` 构造参数（定义见 `llm_client/client.py`）：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `system_prompt` | `str` | 精简回答风格约束 | system 消息，定义模型人设与回答风格 |
| `api_key` | `str \| None` | `None` | 不传则读环境变量 `API_KEY` |
| `max_retries` | `int` | `3` | 网络类错误的最大重试次数 |
| `timeout` | `float` | `30.0` | 单次请求超时（秒） |

成本估算价格表 `PRICES`（单位：元 / 百万 token）内置 `glm-5.3`：输入 8.0、输出 28.0、缓存命中 2.0。

## 测试

```bash
pytest            # 零 API 套件（默认排除真实调用，不消耗 token）
pytest -m api     # 真实 API 套件（消耗 token，全套约 13 次调用）
```

运行测试前需配置 `.env`：零 API 套件只要求 `API_KEY` 有值（无效 Key 亦可，不会发起真实请求）；`-m api` 套件需要有效 Key。

## 项目结构

```text
llm_client/        # 包：client.py 客户端类 · cli.py 命令行入口
tests/             # pytest 测试
docs/              # 设计文档与测试用例说明
```
