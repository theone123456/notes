# cli.py

> 源文件：`projects/llm_client/llm_client/cli.py`

```python
"""命令行聊天界面：llm_client 包的程序入口。

REPL 主循环：读输入 -> 本地分发命令（/exit /clear /resume，本地处理不烧 token）
-> 非命令内容走 client.chat()。三种退出来源（/exit / Ctrl+C / Ctrl+D）
都经 break 汇入循环外的唯一收尾出口（save -> report）。

运行方式：在项目根目录执行 python -m llm_client.cli
"""

import os

from llm_client.client import LLMClient


def main() -> None:
    # 启动前校验（系统边界）：缺 Key 早失败并给出可操作的提示，
    # 好过构造时抛 SDK 英文异常、用户面对裸 traceback
    if not os.getenv("API_KEY"):
        print("缺少 API_KEY：请先复制 .env.example 为 .env 并填入（配置说明见 README）")
        raise SystemExit(1)

    client = LLMClient()

    print("=" * 40)
    print("命令行聊天已启动")
    print("命令：/exit 退出 · /clear 清空会话 · /resume 恢复上次会话")
    print("=" * 40)

    while True:
        try:
            # try 包住整个循环体：Ctrl+C 可能在 chat() 等待 API 响应期间到达
            user_input = input("> ")

            # 边界校验（用户输入是系统边界）：空输入或纯空白不值得一次 API 调用
            if not user_input.strip():
                continue

            match user_input:
                case "/exit":
                    print("退出进程")
                    break
                case "/clear":
                    # 清空对话、保留当前首条 system：人设随会话状态走，
                    # 与 load() 的整体替换互为镜像
                    cleared = len(client.messages) - 1
                    client.messages = client.messages[:1]
                    print(f"已清空 {cleared} 条对话，保留人设（当前 {len(client.messages)} 条消息）")
                case "/resume":
                    # load 是整体替换：成功则当前未保存对话被丢弃，失败则原样保留
                    old_messages = client.messages
                    client.load()
                    if client.messages is not old_messages and len(old_messages) > 1:
                        print(f"已丢弃当前未保存的 {len(old_messages) - 1} 条对话")
                case _:
                    reply = client.chat(user_input)
                    if reply is not None:
                        print(reply)
                    else:
                        print("调用失败，本轮对话未记录，可重试或退出")
        except KeyboardInterrupt:
            print("\n收到 Ctrl+C，退出进程")
            break
        except EOFError:
            print("\n收到 Ctrl+D（输入结束），退出进程")
            break
        except Exception as e:
            print(f"未知错误: {e}")
            break

    # 唯一收尾出口：三种退出来源（/exit、Ctrl+C、Ctrl+D）都经 break 到达这里，
    # 天然只执行一次；save() 内部已捕获全部异常并打印提示，这里无需再包
    client.save()
    client.report()


# 包成员可能被 import（测试 / 其他程序），守卫防止 import 即启动交互循环
if __name__ == "__main__":
    main()
```
