# multi_turn_tokens.py

> 源文件：`phase0/day4/multi_turn_tokens.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "deepseek-v4-flash"

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

rounds = [
    "我叫小明，今年25岁。",
    "我在学Python编程。",
    "我打算三个月后找工作。",
    "我目前住在上海。",
    "我每天能学习3小时。"
]

messages = [{"role": "system", "content": "你是一个简洁的助手"}]

last_messages = 1
last_prompt_tokens = 0
last_completion_tokens = 0
last_total_tokens = 0

for index in range(len(rounds)):
    print(f"========== 第 {index + 1} 轮对话开始 ==========")

    messages.append({"role": "user", "content": rounds[index]})
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        print(f"[观察] messages 条数: {len(messages)} | 输入 token: {response.usage.prompt_tokens} | 输出 token: {response.usage.completion_tokens}｜ 总 token: {response.usage.total_tokens}")
        print(f"[观察] messages 增加条数: {len(messages) - last_messages} | 输入 token 增加数: {response.usage.prompt_tokens - last_prompt_tokens} | 输出 token 增加数: {response.usage.completion_tokens - last_completion_tokens} | 总 token 增加数: {response.usage.total_tokens - last_total_tokens}")

        last_messages = len(messages)
        last_prompt_tokens = response.usage.prompt_tokens
        last_completion_tokens = response.usage.completion_tokens
        last_total_tokens = response.usage.total_tokens

        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
    except Exception as e:
        print(f"调用失败：{e}")

    print(f"========== 第 {index + 1} 轮对话结束 ==========")
```
