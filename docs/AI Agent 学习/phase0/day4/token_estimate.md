# token_estimate.py

> 源文件：`phase0/day4/token_estimate.py`

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

messages = [
    [{"role": "user", "content": "今天天气真好"}], # 5
    [{"role": "user", "content": "大语言模型通过预测下一个词来生成文本，核心是基于概率的序列建模。"}], # 25
    [{"role": "user", "content": "Agent 是一个能感知环境、自主决策并调用工具完成目标的智能体系统，它的核心是 LLM 充当大脑，配合记忆、规划和工具使用形成闭环。"}] # 46
]

try:
    for message in messages:
        response = client.chat.completions.create(
            model=MODEL,
            messages=message,
        )

        content = message[0]["content"]
        char_count = len(content)
        prompt_tokens = response.usage.prompt_tokens
        ratio = char_count / prompt_tokens
        print(f"字符={char_count} | 输入token={prompt_tokens} | 字符/token={ratio:.1f}")
except Exception as e:
        print(f"调用失败：{e}")
```
