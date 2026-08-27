# llm_client_with_usage.py

> 源文件：`phase0/day10/llm_client_with_usage.py`

```python
import json
import math
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
        # 精确版公式：cached ⊂ prompt（拆细不是另算）--缓存部分按缓存价，其余按标准输入价
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


if __name__ == "__main__":
    print("=" * 60)
    print("场景 A：失败调用不污染统计（错 Key，非瞬时错误）")
    print("=" * 60)
    bad_client = LLMClient(api_key="test_api_key")
    reply = bad_client.chat("你好")
    summary = bad_client.get_usage_summary()
    print(f"返回值：{reply}（预期 None）")
    print(f"统计：{summary}（预期全 0）")
    assert reply is None
    assert summary == {"cached": 0, "prompt": 0, "completion": 0, "total": 0, "calls": 0}
    assert len(bad_client.messages) == 1  # 失败不写历史（Day 8 原子提交回归）
    print("✅ 通过\n")

    print("=" * 60)
    print("场景 B：重试后放弃也不污染统计（timeout=0.001, max_retries=2）")
    print("=" * 60)
    flaky = LLMClient(timeout=0.001, max_retries=2)
    reply = flaky.chat("你好")
    summary = flaky.get_usage_summary()
    print(f"统计：{summary}（预期全 0 -- 被拒/超时的请求无账可记）")
    assert reply is None
    assert summary["calls"] == 0
    print("✅ 通过\n")

    print("=" * 60)
    print("场景 C：3 轮对账（快照差分法：单轮 = after - before）")
    print("=" * 60)
    client = LLMClient()
    deltas = []
    questions = ["我叫小明，今年25岁。", "我在学Python编程。", "请问我刚才说了什么？"]
    for q in questions:
        before = client.get_usage_summary()
        reply = client.chat(q)
        after = client.get_usage_summary()
        delta = {k: after[k] - before[k] for k in after}
        deltas.append(delta)
        print(f"本轮 usage：{delta}")
    summary = client.get_usage_summary()
    manual = {k: sum(d[k] for d in deltas) for k in summary}
    print(f"逐轮求和：{manual}")
    print(f"累计统计：{summary}")
    assert manual == summary, "对账失败：逐轮之和不等于累计值"
    print(f"本次 3 轮估算费用：{client.estimate_cost():.6f} 元")
    print("✅ 对账一致\n")

    print("=" * 60)
    print("场景 D：Day 8 回归 + load 后统计观察")
    print("=" * 60)
    print(f"记忆验证（应提到小明）：{(reply or '')[:60]}")
    client.save(filepath="history.json")
    restored = LLMClient()
    restored.load(filepath="history.json")
    print(f"往返一致：{restored.messages == client.messages}（预期 True）")
    print(f"新实例统计：{restored.get_usage_summary()}（预期全 0 -- 统计是进程级，不随历史持久化）")
    print()
    client.report()  # 完成标志演示：会话结束打印总 token 数和估算费用

    print()
    print("=" * 60)
    print("场景 E：estimate_cost 金标准值（零 API 调用）")
    print("=" * 60)
    # 用例 1：Step 2 场景 C 的实测值（218 prompt / 238 completion / 0 cached）
    c1 = LLMClient(api_key="dummy")
    c1.total_prompt_tokens, c1.total_completion_tokens, c1.total_cached_tokens = 218, 238, 0
    assert math.isclose(c1.estimate_cost(), 0.008408), c1.estimate_cost()
    # 用例 2：Step 1 检查点 3 的手算值（1000 prompt / 600 cached / 2000 completion）
    c2 = LLMClient(api_key="dummy")
    c2.total_prompt_tokens, c2.total_cached_tokens, c2.total_completion_tokens = 1000, 600, 2000
    assert math.isclose(c2.estimate_cost(), 0.0604), c2.estimate_cost()
    print("✅ 两个金标准值精确命中\n")
    c2.report()  # 顺带演示 report 输出格式
```
