# temperature_experiment.py

> 源文件：`phase0/day5/temperature_experiment.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL = "glm-5.2"

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)

# 标准问题：概率分布集中，模型有强先验
# 创意问题：概率分布平缓，候选词多差距小
experiments = {
    "标准问题": [{"role": "user", "content": "用一句话解释什么是人工智能"}],
    "创意问题": [{"role": "user", "content": "用一个意想不到的比喻描述人工智能，越有创意越好"}],
}

temperatures = [0, 1.0, 2.0]

for exp_name, messages in experiments.items():
    print(f"\n{'#' * 30} {exp_name} {'#' * 30}")
    print(f"问题：{messages[0]['content']}")
    for temp in temperatures:
        print(f"\n{'=' * 20} temperature={temp} {'=' * 20}")
        for i in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    temperature=temp,
                )

                print(f"--- 第 {i + 1} 次调用 ---")
                print(f"content: {response.choices[0].message.content}")
                print(f"completion_tokens: {response.usage.completion_tokens}")
            except Exception as e:
                print(f"调用失败：{e}")
```
