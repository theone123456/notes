# multi_turn.py

> 源文件：`phase0/day3/multi_turn.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# 经常切换模型对比，不放入 .env，统一在此处修改
MODEL = "deepseek-v4-flash"

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

# 对话历史：只增不改，结构为 [system, user1, assistant1, user2, assistant2, ...]
messages = [
    {"role": "system", "content": "每次用户问什么，每次回答不得超过10个字"},
]

index = 1
while True:
    print(f"========== 第 {index} 轮对话开始 ==========")
    user_content = input("user_content: ").strip()

    if user_content == "exit":
        print("对话结束")
        break
    if not user_content:
        print("（空输入，跳过本轮）")
        continue

    messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
    except Exception as e:
        # 调用失败则回滚刚追加的 user 消息，保证历史交替结构不被破坏
        messages.pop()
        print(f"调用失败：{e}")
        continue

    reply = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})

    print(f"assistant: {reply}")
    print(f"[观察] messages 条数: {len(messages)} | 输入 token: {response.usage.prompt_tokens} | 总 token: {response.usage.total_tokens}")
    print(f"========== 第 {index} 轮对话结束 ==========")

    index += 1
```
