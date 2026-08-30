# fake_prompt_test.py

> 源文件：`phase0/day3/fake_prompt_test.py`

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

messages = [
    {"role": "user",      "content": "我叫小明，我的外号是闪电侠"},
    {"role": "assistant", "content": "闪电侠你好！"},
    {"role": "user",      "content": "我的外号是什么？"},
]

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
except Exception as e:
        print(f"调用失败：{e}")

reply = response.choices[0].message.content

print(f"assistant: {reply}")
print(f"[观察] messages 条数: {len(messages)} | 输入 token: {response.usage.prompt_tokens} | 总 token: {response.usage.total_tokens}")
```
