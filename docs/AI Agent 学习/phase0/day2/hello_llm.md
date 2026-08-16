# hello_llm.py

> 源文件：`phase0/day2/hello_llm.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
)

try:
    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "你是一个毒舌但心软的助手，回答末尾总要补充一句关心。"},
            {"role": "user", "content": "我今天学习进度落后了，很焦虑。"},
        ]
    )

    print(response.choices[0].message.content)
except Exception as e:
    print(e)
```
