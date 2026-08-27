# final_check.py

> 源文件：`phase0/day10/final_check.py`

```python
"""Step 5 完成标志演练：一个含失败调用的完整会话

流程：错 Key 失败 -> 正确 Key 多轮对话 -> 会话结束 report()
复现真实使用节奏：先犯一次错，再正常使用，最后看账单。

两个盯点：
1. 失败调用后的提示是否清晰（不崩溃、指向 .env）
2. report 的数字是否把失败轮排除在外（calls 只含成功调用）
"""
from llm_client_with_usage import LLMClient


def main() -> None:
    print("========== 第 1 幕：填错 Key（失败调用不进统计） ==========")
    bad = LLMClient(api_key="wrong_key")
    reply = bad.chat("你好")
    print(f"返回值：{reply}（预期 None，程序未崩溃）")
    print(f"失败客户端统计：{bad.get_usage_summary()}（预期全 0）")
    assert reply is None
    assert all(v == 0 for v in bad.get_usage_summary().values())

    print()
    print("========== 第 2 幕：换正确 Key，正常多轮会话 ==========")
    client = LLMClient()
    for q in ["你好，请用一句话介绍你自己", "我刚才问了你什么？", "请把答案控制在20字以内再说一遍"]:
        reply = client.chat(q)
        assert reply is not None
        print(f"Q: {q}")
        print(f"A: {reply}\n")

    print("========== 第 3 幕：会话结束，打印总 token 数和估算费用 ==========")
    # report 应只统计 3 次成功调用；第 1 幕的失败不在此账内
    client.report()
    assert client.get_usage_summary()["calls"] == 3

    print()
    print("✅ 完成标志达成：失败不崩溃 + 提示清晰 + 会话结束打印总 token 与估算费用")


if __name__ == "__main__":
    main()
```
