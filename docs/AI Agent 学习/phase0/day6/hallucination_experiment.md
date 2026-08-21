# hallucination_experiment.py

> 源文件：`phase0/day6/hallucination_experiment.py`

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

experiments = {
    "虚构实体": {
        "实验组": [{"role": "user", "content": "请介绍一下 2023 年诺贝尔文学奖得主村上春树的代表作"}],
        "对照组": [
            {"role": "system", "content": "如果你对用户提问不确定，请直接回答不知道"},
            {"role": "user", "content": "请介绍一下 2023 年诺贝尔文学奖得主村上春树的代表作"}
        ]
    },
    "冷门知识": {
        "实验组": [{"role": "user", "content": "引望公司研发管理部平台软件与MDC产品部的部长是谁"}],
        "对照组": [
            {"role": "system", "content": "如果你对用户提问不确定，请直接回答不知道"},
            {"role": "user", "content": "引望公司研发管理部平台软件与MDC产品部的部长是谁"}
        ]
    },
    "过时信息": {
        "实验组": [{"role": "user", "content": "DeepSeek最新发布的大模型是什么"}],
        "对照组": [
            {"role": "system", "content": "如果你对用户提问不确定，请直接回答不知道"},
            {"role": "user", "content": "DeepSeek最新发布的大模型是什么"}
        ]
    }
}

for exp_name, groups in experiments.items():
    print(f"\n{'#' * 30} {exp_name} {'#' * 30}")
    print(f"问题：{groups['实验组'][0]['content']}")
    for group_name, messages in groups.items():
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,
            )

            print(f"\n{'=' * 20} {group_name} {'=' * 20}")
            print(f"content: {response.choices[0].message.content}")
        except Exception as e:
            print(f"调用失败: {e}")
```
