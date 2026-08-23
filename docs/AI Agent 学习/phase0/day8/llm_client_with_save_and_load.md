# llm_client_with_save_and_load.py

> 源文件：`phase0/day8/llm_client_with_save_and_load.py`

```python
import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from typing import Optional

load_dotenv()


class LLMClient:
    def __init__(self, system_prompt: str = "无论用户问什么问题，回答都不要超过300个字符，并且回答尽可能的直接与精简") -> None:
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL")
        self.default_model = "glm-5.3"
        self.messages = [{"role": "system", "content": system_prompt}]

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, user_prompt: str) -> Optional[str]:
        messages = self.messages + [{"role": "user", "content": user_prompt}]

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

            return result
        except Exception as e:
            print(f"调用失败: {e}")

        return None

    def load(self, filepath: str = "history.json") -> None:
        # EAFP：不预先检查存在性，直接尝试，按异常类型分类处理
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                messages = json.load(f)
            self.messages = messages
            print(f"{filepath} 加载成功，继续上次会话")
        except FileNotFoundError:
            # 首次运行是正常场景：保留 __init__ 默认值（新会话），轻提示
            print(f"{filepath} 不存在，开始新会话")
        except json.JSONDecodeError:
            # 文件损坏是异常场景：如实警告并保留当前会话，由用户决定
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
    # 场景 0：正常流程 chat -> save
    client = LLMClient()
    reply = client.chat("你好，请用一句话介绍你自己")
    print(reply)
    client.save(filepath="history.json")

    # 测试 1：往返一致——新实例 load 同一文件，messages 应与保存前完全一致
    restored = LLMClient()
    restored.load(filepath="history.json")
    print(f"往返一致：{restored.messages == client.messages}")

    # 测试 2：文件不存在（首次运行）——应轻提示、不崩溃、保留默认
    fresh = LLMClient()
    fresh.load(filepath="no_such_file.json")
    print(f"保留默认：{len(fresh.messages)} 条消息")

    # 测试 3：JSON 损坏——应警告、不崩溃、保留默认
    with open("corrupted.json", "w", encoding="utf-8") as f:
        f.write("{这不是合法的JSON")
    corrupted = LLMClient()
    corrupted.load(filepath="corrupted.json")
    print(f"保留默认：{len(corrupted.messages)} 条消息")
    os.remove("corrupted.json")
```
