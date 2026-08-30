# max_tokens_experiment.py

> 源文件：`phase0/day5/max_tokens_experiment.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "glm-5.2"

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

max_tokens_list = [10, 2000, 5000]

messages = [{"role": "user", "content": "详细解释 Python 的列表和元组的区别"}]

for max_tokens in max_tokens_list:
    print(f"\n{'#' * 20} max_tokens: {max_tokens} {'#' * 20}")
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
        )

        print(f"content: {response.choices[0].message.content}")
        print(f"completion_tokens: {response.usage.completion_tokens}")
        print(f"finish_reason: {response.choices[0].finish_reason}")
    except Exception as e:
        print(f"调用失败: {e}")
```
