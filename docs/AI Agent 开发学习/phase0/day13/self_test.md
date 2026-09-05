# self_test.py

> 源文件：`phase0/day13/self_test.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL"),
)

messages = [
    {"role": "system", "content": "无论用户问什么问题，回答都不要超过300个字符，并且回答尽可能的直接与精简"},
    {"role": "user", "content": "请问今天上海的天气怎么样，是否会下雨，如果下雨是在哪些时段"},
]

try:
    response = client.chat.completions.create(
        model="glm-5.3",
        messages=messages,
    )

    print(response.choices[0].message.content)
    print(response.usage.prompt_tokens)
    print(response.usage.completion_tokens)
except Exception as e:
    print(e)
```
