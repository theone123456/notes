# llm_client_without_save_and_load.py

> 源文件：`phase0/day8/llm_client_without_save_and_load.py`

```python
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
            print(f"call failed: {e}")

        return None


if __name__ == "__main__":
    client = LLMClient()
    reply1 = client.chat("你好，请用一句话介绍你自己")
    print(reply1)
    print(f"current messages length: {len(client.messages)}")
    reply2 = client.chat("请问我刚刚说了什么")
    print(reply2)
    print(f"current messages length: {len(client.messages)}")
```
