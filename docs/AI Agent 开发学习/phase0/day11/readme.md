# Day 11 学习笔记：命令行聊天界面

> 核心命题：从"跑完即退"的脚本到"持续运行"的循环程序--REPL 骨架 + 命令分发，阶段 2 Agent 主循环的雏形
> 产出脚本：`chat_cli.py` + `test_cli.py`（Step 3-5 编码/验收，库导入 day10 的 `LLMClient`）

## 概念节：REPL 循环与命令分发（Step 1）

> 来源：Step 1 概念任务 · 地基：Day 9 Step 5 Q4（`chat` 返回 None 调用方怎么感知）、Day 10 的 `report()`（退出收尾的归宿）· 目的：建立 CLI 主循环的骨架认知

### REPL：读、判、处理、循环

REPL = **R**ead-**E**val-**P**rint **L**oop。一个永不主动结束的循环，每圈三件事：

```text
┌─────────────────────────────────┐
│            while True           │
│  ① Read   读一行输入             │
│  ② Eval   处理这行输入           │
│  ③ Print  打印处理结果            │
│  ④ Loop   回到 ①，等下一行        │
└─────────────────────────────────┘
```

三个用过的 REPL 实例：Python 交互解释器（`>>>`）、SQLite CLI（`.quit` / `.help`）、redis-cli（`quit`）。共同点：**进程一直活着，等你输入，处理完继续等**；退出不是"跑完了"，而是用户主动发命令。

映射关系：经典 REPL 的 "Eval" 在本 CLI 里**内部就是命令分发**--判（`/` 前缀？）-> 分发（命令分支 / 聊天分支）。"四段结构"和"命令分发"是同一层知识的两种说法。

### 关键转变：脚本 -> 循环程序（状态生命周期）

| | 脚本（Day 2-10） | 循环程序（今天） |
|---|---|---|
| 生命周期 | 跑完即退 | 用户敲 `/exit` 才退 |
| `client.messages` | 进程结束即消失 | **进程活着它就活着** |
| usage 统计 | 每次运行从 0 开始 | 一次会话连续累计 |
| "接着聊" | 必须靠 save/load（Day 8） | 同一进程内天然连续 |

CLI 延长了状态寿命（脚本几秒 -> 一次会话），但**不是永久**。进程退出有三种方式：用户主动（`/exit` / Ctrl+C / Ctrl+D）、**未捕获异常崩溃**、终端关闭。所以 Day 8 的 save/load 依然需要--只是触发点从"脚本结尾"移到"退出命令的收尾动作"。

边界思考：若进程**崩溃**退出，收尾来不及跑，历史照样丢--这是 Step 3 要把三种退出收敛成**单一收尾出口**的原因。

### 命令分发：输入的第一道路由

用户每敲一行，第一件事**不是**发给 LLM，而是路由判断：

```python
while True:
    text = input()
    if text.startswith("/"):      # ① 先本地判断：是命令吗？
        handle_command(text)      #    是 -> 本地处理，0 token，0 费用
    else:
        reply = client.chat(text) # ② 不是 -> 聊天，烧 token
```

**顺序反了的完整事故链**（以 `/exit` 为例）：

```text
用户敲 /exit
-> 先调 LLM："/exit" 被当作聊天内容发给 API（计费）
-> 模型回复"好的，再见！"（再计费）
-> 这轮"用户：/exit / 助手：再见"被写进 messages（污染历史）
-> 然后程序才退出
```

三个代价：① 每条命令白付一次调用费；② 命令词本身被当作聊天发给 LLM 并存进历史；③ 模型对命令的回复不可预期，交互体验诡异。**先判后调 = 路由的第一原则**。

### 伏笔：今天的循环就是未来 Agent 的骨架

对照总计划阶段 2 的"手写 Agent 主循环（while + tool_calls 分发）"：

| | 今天的 CLI | 阶段 2 的 Agent |
|---|---|---|
| 循环 | `while True` | `while True` |
| 输入来源 | `input()`--人 | LLM 的响应--模型决策 |
| 判断 | 输入是不是命令 | 响应里有没有 `tool_calls` |
| 分发分支 | 命令 vs 聊天 | 工具 A vs 工具 B |
| 终止 | `/exit` | 模型自主判断完成 / 最大步数 |

**同构**：读（来源不同）-> 判 -> 分发 -> 循环。今天写熟这个骨架，阶段 2 只是把"人的输入"换成"模型的决策"。

### 检查点自测记录（2026-08-27，三题通过）

> 原始作答：`self_test` · 3/3 通过，Q2 第 2 点成因框架修正

1. **主循环四段结构** -- 通过
   - Read -> Eval -> Print -> Loop，完整准确
2. **为什么命令解析必须在调用 LLM 之前** -- 第 1 点通过，第 2 点修正
   - 第 1 点（避免 token 计费）✓
   - 第 2 点：污染上下文的**后果**说对了，**成因**框架偏了--命令不是脏数据，它本身是合法输入；真实成因是**命令词本身被当作聊天发给 LLM 并存进 messages**。"拦截脏数据"是输入校验，是另一个话题；本 CLI 唯一的本地拦截是空输入 `continue`，同样遵循"本地可判断的先本地处理"总原则
   - 修正后的精确表述：先判后调防的不是"脏数据进历史"，而是"合法命令进历史"
3. **状态生命周期差别 + save/load 为何依然需要** -- 通过
   - 脚本进程自动退出 / 循环程序在非主动退出且无异常时持续运行；历史生命周期跟进程，跨进程必须主动 save/load
   - 精度补充：进程退出有三种方式（主动 / 崩溃 / 终端关闭），CLI 只是延长寿命不是永久；崩溃时收尾来不及跑 -> 单一收尾出口的设计动因

### 本节记住五件事

1. **REPL 四段**：读 -> 判（处理）-> 打印 -> 循环；"Eval"在 CLI 里内部就是命令分发
2. **先判后调**：命令词本身会被当作聊天发给 LLM 并存进历史--防的不是脏数据，是合法命令进历史
3. **CLI 延长状态寿命但不永久**：messages 和 usage 都活在进程里；退出有三种方式，主动退出只是其一
4. **崩溃来不及收尾**：三种退出必须收敛成单一收尾出口，漏一处就是一处丢历史（Step 3 的设计约束）
5. **同构伏笔**：`while + 分发` 就是阶段 2 Agent 主循环的骨架，今天练熟，将来只换输入来源

---

## 项目设计节：CLI 设计四问（Step 2）

> 来源：Step 2 思考任务 · 原始作答：`self_design`（review 后两处精化 + 补依据回链）· 产物即 Step 3-4 的实现规格

### Q1 命令识别：`/` 前缀约定，严格匹配

- 选择前缀而非裸字符串：裸匹配下用户永远没法聊 `exit` 这个词本身，只能换说法或改大小写，交互成本高；前缀让系统命令与聊天内容**语义无歧义**
- 严格匹配：`text == "/exit"`，`/EXIT`、`/exit `（带空格）都不算命令。附带礼物：**更严格的匹配 = 更简单的代码**（不用 strip、不用大小写转换）

### Q2 exit 语义：单一收尾出口，save 先、report 后

- **save 自动做**：不做则 Ctrl+C / Ctrl+D / 忘敲命令时历史丢
- **report 放**：会话结束 = 用户主动退出命令、进程结束之前--Day 10 完成标志"会话结束打印总 token 和费用"的自然归宿
- **顺序：save 先、report 后**（review 精化）。"谁在前都行"的自相矛盾拆解：
  - 两者无依赖的前提是**各自 try/except 互不挡道**（失败打日志不冒泡）--这是"顺序无关"的真正机制，靠包裹保证而非靠顺序保证
  - 但存在一个**信息依赖**：report 是给用户看的最后一屏，save 的成败用户必须知道（否则以为存了、下次 `/resume` 才发现没了）。save 先做、成败在紧邻 report 的输出可见 = 信息优先级设计
- 收尾被三种退出方式共用：`/exit` / Ctrl+C（KeyboardInterrupt）/ Ctrl+D（EOFError）

### Q3 clear 语义：重置为 `[system]`，统计不动

- **messages：保留 system、只清对话**。三层依据：
  1. Day 8 design.txt Q1：system prompt 定义人设与风格，全清后模型答复风格与历史会话割裂
  2. API 层面：messages 变空列表的请求合法但无 system，人设丢失
  3. **与 Day 8 load 的语义对称**：load 是"整体替换、人设随历史回来"，clear 若全清就破坏这对镜像关系。保留 system 是唯一一致的选择
- **Step 4 延伸：保留的是"哪个 system"（A/B 之选）**：实现取 `messages[:1]`（当前首条），"原始"重定义为**本会话原始**而非进程原始。依据是第 3 层镜像原则的延伸：load 的轴是"人设随历史回来"，clear 的镜像就是"人设随会话保留"——两者都锚定**当前会话状态**；锚定进程启动时刻（启动时另存一份引用）反而引入第三态、破坏对称。推论：`/resume` 载入历史后 `/clear`，保留的是**载入历史的人设**（2026-09-01 冒烟实证：载入海盗人设历史 -> /clear -> 落盘 `[海盗 system]`）
- **usage 统计不清**（Day 10 思考题结论的落地）：token 计数与费用随**进程**生命周期，clear 只删除会话记录，那些会话的消耗仍真实存在于本进程生命周期。若清零，"一个进程经历多个会话"后 report 就回答不了"本进程花了多少"的问题

### Q4 失败与中断：提示继续等，退出权在用户

- **chat 返回 None**：打印清晰提示后继续等下一条输入。失败记录不进历史（Day 8 原子提交），不污染上下文；退出决定权交用户
- **Ctrl+C / Ctrl+D**：捕获，走与 `/exit` 相同的 save -> report 收尾。不捕获则用户看到进程戛然而止 + 裸 traceback，退出风格不一致
- **不加"连续失败 N 次自动退出"**：信息充分时的退出决策权在用户，系统职责是给出准确错误信息和解决思路。与 Q4.1 是同一原则的两次应用：**不猜用户意图，给足信息让用户决策**
- **Step 4 定稿（2026-09-01，失败演练后确认）**：失败上限的必要性取决于**循环的驱动者**。人驱动的 REPL 不需要——每个失败轮都由用户一次按键触发，"连续失败 N 次"发生时用户已做了 N 次继续的显式决策，自动退出 = 用系统的一次猜测推翻 N 次选择；且失败轮零资源消耗（不进历史、不计 token、鉴权/配额类错误立即失败无重试延迟），没有需要止损的对象。模型驱动的 Agent 主循环（阶段 2）则**必须**加——tool_calls 循环没有人踩刹车，外部工具持续失败时 token 真实燃烧，max_steps / 连续失败熔断是安全栏而非可选优化。这是"CLI 与 Agent 同构"伏笔的另一面：换掉输入来源的同时，刹车职责也从人移交给代码

### Q5 resume 语义：整体替换 + 丢弃告知（Step 4 补，可选进阶）

- **命令定位**：任务清单外的自加命令，让 Day 8 的 `load()` 在 CLI 里形成闭环（"继续上次会话"）
- **整体替换**：沿用 `load()` 原语义——messages 被文件内容整体替换，人设随历史回来
- **破坏性决策**：替换会丢当前未保存的对话。**不设确认**：敲 `/resume` 本身就是用户决策（与 Q4"退出权在用户"同一原则）；但**替换确实发生且有对话可丢时打印丢弃条数**（给足信息）。不误报机制：load 失败时类内部保留原列表，CLI 层用 `client.messages is not old_messages` 的**对象身份**判断是否真的替换
- **与 clear 的交互（A 语义）**：resume 后 clear 保留载入人设——Q3 Step 4 延伸的自然推论，两个命令共用"人设随会话状态走"这根轴
- **与 exit-save 的闭环**：resume 后继续聊，exit 时 save 覆盖 `history.json`。完整生命周期：save -> 退出 -> 重启 -> resume -> 续聊 -> save

### 实现规格汇总（Step 3-4 直接照此实现）

```text
命令识别   text == "/exit" / "/clear" / "/resume"（严格匹配，无 strip/大小写转换）
循环       while True -> input() -> 空输入 continue -> 命令分支 -> chat() 聊天
失败路径   reply is None -> 打印提示 -> 继续循环（不进历史、不计数）
收尾出口   单一函数：save（try/except 包裹）-> report -> 退出
           三种触发：/exit、KeyboardInterrupt、EOFError
clear      messages 重置为 [当前首条 system 消息]（"原始"= 本会话原始而非进程原始，
           /resume 后即载入历史的人设——Q3 Step 4 延伸）；4 个 usage 计数器不动
resume     调 load() 整体替换 messages；确有对话被丢弃时打印"已丢弃 N 条"（load 失败
           不误报，以 messages 对象身份判断）；无确认，决策权在敲命令的用户（Q4 原则）
```

### 本节记住四件事

1. **顺序无关靠包裹不靠排序**：两个动作互不挡道的机制是各自 try/except，顺序只决定信息优先级（save 成败要最后一屏可见）
2. **设计要看镜像关系**：clear 与 load 是一对镜像（清空 vs 恢复），语义必须对称--全清破坏对称，人设处理必须一致
3. **同一原则的应用要能识别**：Q4.1 与 Q4.3 都是"不猜用户意图，给足信息让用户决策"
4. **留观察口不实现**：失败计数器是"连续 N 次退出"的前置条件，今天不做但设计时留位

---

## 编码节：主循环骨架与命令分发（Step 3）

> 来源：Step 3 编码任务 · 产出：`chat_cli.py`（复制 day10 类文件，库导入 `from llm_client_with_usage import LLMClient`）· 初版功能全对，review 后重构掉 finally+flag 机关

### 初版做对的四点

1. **try 包住整个循环体**：Ctrl+C 可能打在 `chat()` 等 API 响应的几十秒里，而不只是 `input()` 处--try 范围必须覆盖等待期，这是本步最大的坑，一次做对
2. flag + finally 达成了单一收尾出口的目标（虽然机关可以更少，见下）
3. `match` 的字面量模式用法正确，没踩 bare-name capture 的坑（`case _` 兜底、`case "/exit"` 是字面量不是变量名）
4. 失败路径 / 空输入 / 命令占位全部符合设计规格；收尾超前实现了 save+report

### 重点：finally 里的 break 会吞掉在途异常

**Python 的规则**：finally 子句里执行 `break` / `continue` / `return`，**正在传播的异常会被直接丢弃**。

这不是笔误，是语言规范（Python 语言参考 finally 一节原文：If the finally clause raises another exception, the saved exception is set as its context... 而 break/return/continue 会**取消** exception propagation）。准确说：finally 里出现任何"离开 finally 的控制流语句"（break/continue/return）或抛出新异常，都会**取代**正在传播的原异常。

**机制拆解**（对照初版代码走一遍）：

```python
# 初版形状
try:
    ...input/chat/match...          # ① 这里抛出 KeyboardInterrupt
except KeyboardInterrupt:
    print("键盘中断")                # ② except 接住，开始打印
    exit_flag = True
finally:
    if exit_flag:                   # ③ 执行到这里时又来一个 Ctrl+C？
        break                       #    若 ②③ 之间有在途异常，break 把它丢弃
```

关键在时间线。异常不是"点"，是**从抛出到被 except 接住的传播过程**：

```text
用户第 1 次 Ctrl+C ──→ 抛出 KeyboardInterrupt ──┐
                                              ├─ 在途：正要进 except 分支
恰好此刻用户第 2 次 Ctrl+C ──→ 新异常在途 ──────┘
except 打印提示（第 1 个异常已被接住处理）
finally 执行 break ──→ 第 2 个在途异常被无声丢弃 ──→ 干净退出
```

初版代码里，"带伤进 finally"只剩两类真实场景：

- **Ctrl+C 打在 except 处理器执行期间**（正在 `print` 提示语时又来一记 Ctrl+C）-> 第二个 KeyboardInterrupt 在途 -> 进 finally -> `break` 把它丢弃 -> 碰巧得到想要的结果（干净退出）。**是运气不是设计**：如果 finally 里不是 break 而是一段耗时收尾（比如大文件写盘），第二个 Ctrl+C 会立刻从 finally 冒出，traceback 裸奔
- **Ctrl+C 打在 finally 自己的 save()/report() 期间** -> 新异常从 finally 直接冒出，`break` 还没执行到 -> 穿出循环 -> 裸 traceback（快速双击 Ctrl+C 可复现）

**本质**：finally 的语义是"无论怎样都要执行的补台代码"，它适合做**清理**（关文件、释放锁），不适合做**控制流决策**（用 flag 告诉它"这次要不要 break"）。把 break 塞进 finally，等于让补台代码兼职决定程序走向，而它兼职时随手丢弃在途异常。

**教训**：`finally` 里出现 `break`/`continue`/`return` = 危险信号。见到就问一句：有没有在途异常会被这个控制流语句吞掉？

### 重构：break 直接写，收尾放循环外

flag + finally 的方案是"告诉 finally 该退出了"。但 **break 在 try 块内、match 分支内、except 块内都合法**--三种退出来源各自直接 break，收尾写在**循环外**：天然恰好执行一次，不需要 flag、不需要 finally，吞异常的陷阱消解于无形：

```python
while True:
    try:
        user_input = input("> ")     # try 包整个循环体（保住 Ctrl+C-during-API）
        if not user_input.strip():   # 空输入/纯空白：边界校验，不值得烧 API
            continue
        match user_input:
            case "/exit":
                break                # 在 match 分支里 break，合法
            case "/clear":
                ...
            case _:
                reply = client.chat(user_input)
                ...
    except KeyboardInterrupt:
        break                          # 在 except 块里 break，合法
    except EOFError:
        break
    except Exception as e:
        print(f"未知错误: {e}")
        break

# 循环外：唯一可能的退出后位置，收尾只出现一次
client.save()
client.report()
```

**这是 CLI 的教科书形状：每个退出源只负责 break，收尾只出现在循环之后。** 收尾代码不进 try/finally，反而不参与任何异常传播路径。初版功能等价，但 Step 4 要往循环体加 `/clear` 完整语义，底座越简单越好。

### 其他记录点

- **空白输入的决策**：空输入 `""` 和纯空白 `"   "` 都走 `continue`，不烧 API。定位是**系统边界处的输入校验**（Day 9 Bug 4 原则的正面应用）；与命令严格匹配不冲突--`/exit `（带尾空格）仍是聊天内容，命令匹配语义未变
- **EOF 提示去术语化**：用户不知道 EOFError 是什么，提示写"收到 Ctrl+D（输入结束）"；Ctrl+C/D 的提示前补 `\n`，避免与 `> ` 提示符挤在同一行
- **save 的异常保证由类提供**：设计规格写"收尾 save 用 try/except 包裹"，实际不包的原因--Day 10 的 `save()` 类内部已 catch 全部异常并打印"存储会话失败"。**要知道保证的提供者是谁**（这里由类保证，不是 CLI 层）；`report()` 缺价格 KeyError fail loudly 是 Day 10 的既定决策，不包
- **CLI 模块顶层不套 `__main__` 守卫**：`client = LLMClient()` 和 while 在模块顶层 = import 即启动交互循环。可接受，因为没人 import 一个 CLI（它是程序本体）。Day 10 的守卫是为了"类被当库用"，两者性质不同--**守卫的必要性取决于"有没有人 import 我"**

### 验证（2026-08-27，冒烟测试全绿，零 API 调用）

| 测试 | 输入流 | 验证点 | 结果 |
|---|---|---|---|
| 空管道 | `printf "" |` | stdin 立即 EOF -> Ctrl+D 路径 -> save+report -> 干净退出 | ✅ |
| 空行+空白+/exit | `\n   \n/exit` | 空行、纯空白被跳过，/exit 退出 | ✅（三个提示符、两行跳过）|
| import 安全 | 启动即进 `> ` | day10 的场景测试未触发（`__main__` 守卫） | ✅ |
| save 落盘 | 退出后检查 | `day11/history.json` 写入成功，落在运行目录 | ✅ |

环境备注（2026-09-01 更新）：系统 `python3` 缺 dotenv（ModuleNotFoundError），须用项目 venv。原 Day 1 venv 建于 `Learn/.venv`，目录改名 `Development/` 后整体搬迁导致损坏——**venv 不可搬迁**（activate 脚本与各脚本 shebang 写死创建时的绝对路径），已在 `Development/.venv` 原样重建（python.org 3.13.3，`openai==3.1.0` + `python-dotenv==1.2.2`）。用法：`source .venv/bin/activate` 后 `python chat_cli.py`；IDE 须将解释器指向 `Development/.venv/bin/python`（编辑器"缺库"红线 = 解释器绑定问题，与 venv 本体无关）。

### 本节记住五件事

1. **finally 里的 break/continue/return 会吞掉在途异常**：语言规范行为，不是 bug 但反直觉；finally 只做清理，不做控制流决策
2. **CLI 教科书形状**：每个退出源直接 break，收尾只在循环之后--不需要 flag、不需要 finally
3. **异常是传播过程不是点**：Ctrl+C 打在 except 执行期、finally 执行期都是真实场景；try 要包到能覆盖"等待期"的整个循环体
4. **保证要知道提供者**：save 不抛异常是类的保证（Day 10 内部 catch），不是 CLI 运气好
5. **`__main__` 守卫的判据**：有没有人 import 我--类文件必须有，CLI 程序本体不需要

---

## 编码 + 实验节：clear / resume 语义落地与自动化验证（Step 4）

> 来源：Step 4 编码 + 实验任务 · 产出：`chat_cli.py` 最终版（/clear 计数与 A 语义、/resume 丢弃告知）+ `test_cli.py` / `pytest.ini`（pytest，11 用例）· 流程：两轮 review -> 修正 -> 冒烟 T0-T3 -> 测试套件 11/11 全绿，2026-09-01

### 编码记录：clear / resume 分支的最终形状

- **/clear**：先重置后打印——记 `cleared = len(client.messages) - 1` -> 重置为 `messages[:1]` -> 打印"已清空 N 条对话，保留人设（当前 1 条消息）"。"当前消息数"是任务清单明文要求；N 报清掉的非 system 条数，比单报剩余数信息量大
- **/resume**：删掉与 `load()` 结果可能矛盾的预打印（文件不存在时会先说"加载历史会话"再说"不存在"）。丢弃告知用**对象身份**判断：`client.messages is not old_messages` 且旧会话确有对话（len > 1）才打印"已丢弃 N 条"。机制：`load()` 只在成功路径 rebind `self.messages`，失败时保留原列表对象——身份比较天然区分"真替换"与"失败保留"，不误报
- banner 列全三个命令；设计依据见设计节 Q3 Step 4 延伸（A 语义）与 Q5（resume 语义），此处不重复

### 实验记录：pytest 自动化（2026-09-01，11/11 全绿）

实验从"人工体验"升级为"可回归的自动化用例"。分层：**零 API 套件**（`pytest`，8 用例，约 7 秒，不烧 token）+ **真实 API 套件**（`pytest -m api`，3 用例，约 13 次调用，全套约 1 分钟）。`pytest.ini` 用 `addopts = -m "not api"` 默认排除 API 用例，防止日常回归误烧 token。

**隔离机制**：每用例在 pytest 临时目录（tmp_path）以子进程跑 `chat_cli.py`——`history.json` 相对运行目录落盘，cwd 换成临时目录即天然隔离，不碰真实历史；`.env` 的 Key 显式注入子进程环境（不依赖 load_dotenv 的查找行为），错 Key 演练靠 env 覆盖（load_dotenv 默认不覆盖已存在的环境变量）。

**实验数据**（断言全过 = 下列行为全部实证）：

| 实验 | 用例 | 实证内容 |
|---|---|---|
| 记忆验证 | `test_memory_multi_turn` | 5 轮自我介绍后第 6 轮问姓名年龄，回复含"小测""28"；成功调用 6 次 |
| clear 失忆 + 新话题 | `test_clear_amnesia_and_usage_kept` | clear 后问名字，回复**不含**旧名字；新话题正常回答 |
| exit 落盘 | 同上 + `test_exit_saves_and_reports` | 落盘的 history.json 全部消息中旧名字不出现（只剩 clear 后的新会话） |
| 重启 resume | `test_step5_full_walkthrough` | 第二进程"加载成功"+ 川菜记忆恢复 + 成功调用 1 次 |
| 失败演练（错 Key） | `test_wrong_key_no_crash_loop_continues` | 两轮各打印"API Key 无效"+"调用失败，本轮对话未记录"，循环继续不崩；成功调用 0 次；落盘只剩 system |
| A 语义回归 | `test_clear_keeps_loaded_persona` | 载入海盗人设 5 条 -> /clear -> 落盘 `[海盗 system]`（本会话原始，非进程原始） |

**usage 的双向实证**（Day 10 思考题的落地闭环）：
- **跨 clear 累计**：clear 前后各聊，report 报"成功调用 3 次"——统计跟进程不跟会话
- **重启归零**：第二进程 resume 后只聊 1 轮，report 报"成功调用 1 次"——同一份历史、不同进程、计数独立

**失败演练是四天结论的端到端串联**：Day 8 原子提交（失败轮不进历史）+ Day 9 悬案（None -> 提示后继续）+ Day 10 统计（失败不计成功调用）+ Day 11 循环（退出权在用户）。零 token 成本（鉴权失败无推理消耗）。

**教训：测试与实现不一致时，先判谁错**。首跑 walkthrough 失败——预期"已清空 2 条"，实际"已清空 4 条"。排查：CLI 对（clear 前有两轮聊天 = 4 条非 system 消息），**测试预期漏算了一轮**。测试失败的可能有四种（实现错 / 测试错 / 都错 / 环境错），不加判断就"改实现迁就测试"是最坏路径——这次是测试错，修的是断言。

**同步阻塞观察（人工，不可自动化）**：等待回复期间终端完全阻塞——无法输入，体验即"卡死"。同步 `chat()` 一路阻塞到响应或超时。这正是阶段 1 流式输出（stream）要解的问题：逐 token 打印、等待期不再黑盒。伏笔记下。

### 本节记住五件事

1. **实验可以升级为回归资产**：人工体验 -> pytest 用例（零 API 默认跑、真实 API 显式 `-m api`），一次实验变永久防线
2. **子进程 + 临时目录 = CLI 测试的隔离单元**：history.json 相对运行目录落盘，cwd 换成 tmp_path 即天然隔离；Key 显式注入 env，不依赖 load_dotenv 查找行为
3. **输出协议是测试的解析依据**：`> ` 提示符每出现一次 = 一条输入的处理块；输出结构的稳定性就是可测性
4. **测试失败先判谁错**：实现 / 测试 / 都错 / 环境——不加判断就改实现迁就测试是最坏路径
5. **阻塞体验本身就是需求信号**："卡死感"是阶段 1 流式输出的直接动机，体验类观察不可自动化，但要记录

---

## 验收节：完成标志自测（Step 5）

> 原始作答：`self_test`（保留原样）· 2026-09-01 review：4 题直过 + Q5.3 成因修正（与 Step 1 Q2 同类型：成因与感知点混淆）· 完整演练已由 `test_step5_full_walkthrough` 自动化验证

### 完成标志对照：一个完整可用的命令行聊天程序 ✅

启动 -> 多轮聊天（记忆验证）-> `/clear` -> 新话题 -> `/exit`（save + report）-> 重启 -> `/resume` 历史恢复——全流程由 `test_step5_full_walkthrough` 断言通过；11 用例全部断言 stderr 为空（无裸 traceback）、退出码 0。

### 自测记录（5/5 答出）

1. **命令识别与先判后调** -- 通过（一处措辞精度）
   - 前缀约定 + 严格匹配 ✓；裸匹配代价（无法明文聊 `exit`）✓
   - 精化：计费成因不是"命令判断"，是**命令词被当作聊天内容发给 LLM**——判断本身零成本，顺序反了才让命令进计费通道
2. **clear 后剩什么** -- 通过（补 A 语义）
   - 剩 system、保留理由（人设/风格割裂，Day 8 依据）✓
   - 补：剩的是**本会话原始** system——`/resume` 后为载入历史的人设（`test_clear_keeps_loaded_persona` 实证）
3. **None 处理** -- 通过（补半步）
   - 继续循环、不进历史、不付钱 ✓
   - 补：完整动作是**先打印清晰提示**再继续等输入（"给足信息让用户决策"的落地）；边界注脚：客户端超时 ≠ 服务端未执行，极端情况可能没看到回复但被计费——重试策略的真实成本
4. **usage 不清零** -- 通过（说法锋利化）
   - 跟进程不跟会话、真实消耗不随记录删除而消失 ✓
   - 锋利版：清零后 report 从"本进程花了多少"降级为"当前会话花了多少"，已发生消耗从账上消失——**只少报不多报，账实分离**（`test_clear_amnesia_and_usage_kept` 断言跨 clear"成功调用 3 次"实证）
5. **三种退出收尾一致** -- 前两点通过，第 3 点修正
   - 循环外统一收尾 ✓；收尾 = save（先）+ report（后）两件事，"退出循环"是到达路径不是组成 ✓
   - **修正：load 不丢历史**。丢历史的成因 = 退出时未写盘 -> 进程结束 -> 内存消失；感知点 = 下次 `/resume` 拿到上一次落盘的旧版本；最疼场景 = resume 续聊后退出，丢的是"本次增量"且未必意识到。对照 Q4 同一根轴：漏 save 时 usage 照样记着"花过"——**report 有账、历史无据**

### Day 11 收官

CLI 把 Day 8-10 的零件（原子提交、失败返回 None、usage 统计）组装成一台完整可用的机器，全部行为沉淀为 11 个可回归的自动化用例。伏笔移交：等待回复期的"卡死" -> 阶段 1 流式输出（stream）；`while + 分发`骨架 -> 阶段 2 Agent 主循环（届时"谁踩刹车"从人移交给代码）。

