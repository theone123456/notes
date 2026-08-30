# chat_cli.py

> 源文件：`phase0/day11/chat_cli.py`

```python
from llm_client_with_usage import LLMClient

client = LLMClient()

print("=" * 40)
print("命令行聊天已启动")
print("命令：/exit 退出 · /clear 清空会话历史")
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
                print("清空会话")
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

# 唯一收尾出口：三种退出来源（/exit、Ctrl+C、Ctrl+D）都经 break 到达这里，天然只执行一次
# save 的异常保证由类提供（Day 10 在类内部 catch 并打印"存储会话失败"）
client.save()
client.report()
```
