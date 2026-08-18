# token_experiment.py

> 源文件：`phase0/day4/token_experiment.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "glm-5.3"

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

text_code = """
def predict(model, data):
    result = model.run(data)
    if result.score > 0.8:
        return result.label
    return "unknown"
"""

messages = {
    "English": [{"role": "user", "content": "Artificial intelligence lets computers learn from data and make predictions. It powers search engines, recommendation systems, and chatbots like me."}],
    "Chinese": [{"role": "user", "content": "人工智能让计算机从数据中学习并做出预测，它驱动着搜索引擎、推荐系统和聊天机器人。"}],
    "Code": [{"role": "user", "content": text_code}]
}

try:
    for key, value in messages.items():
        response = client.chat.completions.create(
            model=MODEL,
            messages=value,
        )

        content = value[0]["content"]
        char_count = len(content)
        prompt_tokens = response.usage.prompt_tokens
        ratio = char_count / prompt_tokens
        print(f"[{key}] 字符={char_count} | 输入token={prompt_tokens} | 字符/token={ratio:.1f}")
except Exception as e:
        print(f"调用失败：{e}")
```
