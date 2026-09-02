# client.py

> 源文件：`projects/llm_client/llm_client/client.py`

```python
"""LLM 客户端封装：多轮对话、历史持久化、错误重试、token 统计与成本估算。"""

import json
import os
import time

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)
from typing import Optional


load_dotenv()


class LLMClient:
    """对话状态与 API 调用的封装：维护 messages 历史、持久化、重试、用量统计。

    约定：
    - chat() 失败不抛异常、返回 None，由调用方提示用户；
      仅成功的请求会把消息追加进 messages（失败轮不进历史、不计 token）
    - 重试只针对网络类错误（超时 / 连接 / 限流，指数退避）；
      鉴权 / 配额类错误立即放弃（重试无效）
    """

    # 价格单位：元 / 百万 token
    PRICES = {"glm-5.3": {"input": 8.0, "output": 28.0, "cached": 2.0}}

    def __init__(
        self,
        system_prompt: str = "无论用户问什么问题，回答都不要超过300个字符，并且回答尽可能的直接与精简",
        api_key: str | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key or os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.default_model = "glm-5.3"
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_retries = max_retries
        self.timeout = timeout

        self.total_cached_tokens = 0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.calls_succeeded = 0

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def chat(self, user_prompt: str) -> Optional[str]:
        messages = self.messages + [{"role": "user", "content": user_prompt}]
        time_interval = 1.0

        for attempt in range(self.max_retries + 1):
            reason = None
            try:
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=messages,
                )

                result = response.choices[0].message.content
                self.messages += [
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": result},
                ]

                self.total_cached_tokens += getattr(response.usage.prompt_tokens_details, "cached_tokens", 0)
                self.total_prompt_tokens += response.usage.prompt_tokens
                self.total_completion_tokens += response.usage.completion_tokens
                self.calls_succeeded += 1

                return result
            except AuthenticationError:
                print("API Key 无效，请检查 .env 中的 API_KEY")
                break
            except RateLimitError as e:
                code = (e.body or {}).get("error", {}).get("code", "")
                if code == "SetLimitExceeded":
                    print("配额已用尽，请到火山方舟控制台处理额度（重试无效）")
                    break
                reason = type(e).__name__
            except APITimeoutError as e:
                reason = type(e).__name__
            except APIConnectionError as e:
                reason = type(e).__name__
            except Exception as e:
                print(f"调用失败: {e}")
                break

            if attempt < self.max_retries:
                print(f"第 {attempt + 1} 次重试，原因：{reason}")
                time.sleep(time_interval)
                time_interval *= 2.0
            else:
                print(f"连续失败 {self.max_retries + 1} 次（最后原因：{reason}），放弃重试")

        return None

    def load(self, filepath: str = "history.json") -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                messages = json.load(f)
            self.messages = messages
            print(f"{filepath} 加载成功，继续上次会话")
        except FileNotFoundError:
            print(f"{filepath} 不存在，开始新会话")
        except json.JSONDecodeError:
            print(f"{filepath} 已损坏，无法解析，保留当前会话")
        except Exception as e:
            print(f"未知错误: {e}")

    def save(self, filepath: str = "history.json") -> None:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"存储会话失败: {e}")

    def get_usage_summary(self) -> dict:
        usage_summary = {
            "cached": self.total_cached_tokens,
            "prompt": self.total_prompt_tokens,
            "completion": self.total_completion_tokens,
            "total": self.total_prompt_tokens + self.total_completion_tokens,
            "calls": self.calls_succeeded
        }
        return usage_summary

    def estimate_cost(self) -> float:
        price = LLMClient.PRICES[self.default_model]
        return (
                (self.total_prompt_tokens - self.total_cached_tokens) / 1e6 * price["input"] +
                self.total_cached_tokens / 1e6 * price["cached"] +
                self.total_completion_tokens / 1e6 * price["output"]
        )

    def report(self) -> None:
        s = self.get_usage_summary()
        cost = self.estimate_cost()
        print("=" * 40)
        print("会话用量报告")
        print("=" * 40)
        print(f"输入 token：{s['prompt']}（其中缓存命中 {s['cached']}）")
        print(f"输出 token：{s['completion']}")
        print(f"总 token：{s['total']} · 成功调用 {s['calls']} 次")
        print(f"估算费用：{cost:.6f} 元（约 {cost * 100:.2f} 分）")
        print("=" * 40)
```
