# error_experiments.py

> 源文件：`phase0/day9/error_experiments.py`

```python
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def create_client(api_key: str | None, timeout: float | None) -> OpenAI:
    if api_key is None:
        api_key = os.getenv("API_KEY")
    if timeout is None:
        timeout = 30.0
    base_url = os.getenv("BASE_URL")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


def chat(client: OpenAI, model: str = "glm-5.3") -> None:
    client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "this is a test system prompt"},
            {"role": "user", "content": "this is a test user prompt"},
        ],
    )


def observe(title: str, e: Exception) -> None:
    """统一打印一条错误观察记录，方便整理进观察表"""
    print(f"===== {title} =====")
    print(f"异常类名: {type(e).__name__}")
    # 连接类错误没有 status_code 属性，None 恰好体现“无状态码”
    print(f"状态码: {getattr(e, 'status_code', None)}")
    print(f"message: {e}")
    print()


def test_invalid_key() -> None:
    try:
        client = create_client(api_key="invalid_api_key", timeout=None)
        chat(client)
    except Exception as e:
        observe("实验 1：无效 Key", e)


def test_timeout() -> None:
    try:
        client = create_client(api_key=None, timeout=0.001)
        chat(client)
    except Exception as e:
        observe("实验 2：超时", e)


def test_invalid_model() -> None:
    try:
        client = create_client(api_key=None, timeout=None)
        chat(client=client, model="test_model")
    except Exception as e:
        observe("实验 3：无效模型名", e)


if __name__ == "__main__":
    test_invalid_key()
    test_timeout()
    test_invalid_model()
```
