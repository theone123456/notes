# llm_client_with_retry.py

> 源文件：`phase0/day9/llm_client_with_retry.py`

```python
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
    def __init__(
        self,
        system_prompt: str = "无论用户问什么问题，回答都不要超过300个字符，并且回答尽可能的直接与精简",
        api_key: str | None = None,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        # api_key=None 表示“用默认”（读 .env）；传假 Key 即可构造错 Key 测试场景，无需改源码
        self.api_key = api_key or os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.default_model = "glm-5.3"
        self.messages = [{"role": "system", "content": system_prompt}]
        self.max_retries = max_retries
        self.timeout = timeout

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

    def chat(self, user_prompt: str) -> Optional[str]:
        # 快照：本轮请求的 messages；self.messages 只在成功后原子提交（Day 8 设计）
        messages = self.messages + [{"role": "user", "content": user_prompt}]
        time_interval = 1.0

        for attempt in range(self.max_retries + 1):
            reason = None  # 本轮失败原因（异常类名）；只有可重试错误会赋值
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
                return result  # 成功必须立即返回，否则会落入下方重试逻辑重复调用
            except AuthenticationError:
                print("API Key 无效，请检查 .env 中的 API_KEY")
                break  # 非瞬时错误：立即放弃，不重试
            except RateLimitError as e:
                # 二次判断：配额用尽（SetLimitExceeded）伪装成 429，重试无效
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
                break  # 未知错误不重试

            # ---- 走到这里 = 本轮失败且可重试 ----
            if attempt < self.max_retries:
                print(f"第 {attempt + 1} 次重试，原因：{reason}")
                time.sleep(time_interval)
                time_interval *= 2.0  # 指数退避：1s -> 2s -> 4s
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


if __name__ == "__main__":
    print("=" * 60)
    print("场景 A：瞬时错误触发重试（timeout=0.001, max_retries=2）")
    print("=" * 60)
    flaky = LLMClient(timeout=0.001, max_retries=2)
    reply = flaky.chat("你好")
    # 预期：2 行重试日志（原因 APITimeoutError）+ 放弃提示；耗时约 3 秒（1s + 2s）
    print(f"返回值：{reply}（预期 None）")
    print(f"历史长度：{len(flaky.messages)}（预期 1，失败不写历史）")
    print()

    print("=" * 60)
    print("场景 B：非瞬时错误不重试（错 Key, max_retries=3）")
    print("=" * 60)
    bad_client = LLMClient(api_key="test_api_key", max_retries=3)
    reply = bad_client.chat("你好")
    # 预期：0 行重试日志（重试有判断力），直接 401 提示
    print(f"返回值：{reply}（预期 None）")
    print(f"历史长度：{len(bad_client.messages)}（预期 1）")
    print()

    print("=" * 60)
    print("场景 C：正常成功 + Day 8 回归")
    print("=" * 60)
    client = LLMClient()
    reply = client.chat("你好，请用一句话介绍你自己")
    print(f"返回值非空：{reply is not None}（预期 True）")
    # 预期 3 = system + 1 组问答；若为 9，说明成功也在循环里重复调用
    print(f"历史长度：{len(client.messages)}（预期 3）")
    print(f"第 2 轮：{client.chat('请问我刚刚说了什么')}")
    client.save(filepath="history.json")

    restored = LLMClient()
    restored.load(filepath="history.json")
    print(f"往返一致：{restored.messages == client.messages}")
```
