# resume_demo.py

> 源文件：`phase0/day8/resume_demo.py`

```python
"""Day 8 Step 5 终局验收：两个独立进程接力对话。

用法：
    python resume_demo.py new      # 进程 A：新建会话，聊两轮，保存后退出（模拟中断）
    python resume_demo.py resume   # 进程 B：全新进程加载历史，验证模型记得
"""
import sys

from llm_client_with_save_and_load import LLMClient

HISTORY_FILE = "resume_history.json"


def new_session() -> None:
    print("【进程 A】新建会话")
    client = LLMClient()

    reply1 = client.chat("我叫小明，我最喜欢的数字是 42，请记住这两点。")
    print(f"第 1 轮回复：{reply1}")

    reply2 = client.chat("另外，我今天在学 Day 8：多轮对话与历史持久化。")
    print(f"第 2 轮回复：{reply2}")

    client.save(filepath=HISTORY_FILE)
    print(f"【进程 A】历史已保存到 {HISTORY_FILE}，进程退出（模拟中断）")


def resume_session() -> None:
    print("【进程 B】全新进程启动")
    client = LLMClient()

    client.load(filepath=HISTORY_FILE)
    print(f"加载后消息数：{len(client.messages)}")

    reply = client.chat("我叫什么名字？我最喜欢的数字是多少？我今天在学什么？")
    print(f"验证回复：{reply}")

    client.save(filepath=HISTORY_FILE)
    print(f"【进程 B】验证完成，本轮问答已追加保存回 {HISTORY_FILE}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("new", "resume"):
        print("用法：python resume_demo.py [new|resume]")
        sys.exit(1)

    if sys.argv[1] == "new":
        new_session()
    else:
        resume_session()
```
