# LLMClient 设计文档

> 记录关键设计决策及其理由（是什么、为什么这么做）。使用方法见 [README](../README.md)，测试点见 [测试用例文档](testing.md)。
> 对应源码：`llm_client/client.py`（客户端类）、`llm_client/cli.py`（命令行界面）

## 1. 项目定位

把无状态的 Chat API 封装成一个**有状态、可持久化、可观测**的命令行会话客户端：

- **有状态**：类内自动维护对话历史，调用方只管 `chat("问题")`
- **可持久化**：历史存取 JSON 文件，跨进程恢复会话
- **可观测**：token 用量与成本随每次成功调用累计，会话结束出报告

明确的边界（不做什么）：不做流式输出（等待回复期间同步阻塞，是已知体验问题）；不做长历史压缩（成本随对话线性增长）；失败原因不进返回值（调用方以 `None` 感知失败，细节在终端提示里）。

## 2. 总体结构

```text
llm_client/                 # 仓库根
├── llm_client/             # 包
│   ├── client.py           # LLMClient 类——状态与 API 调用的封装（被 import 的库）
│   └── cli.py              # 命令行界面——程序本体（python -m llm_client.cli）
├── tests/test_cli.py       # 回归防线
├── pytest.ini · requirements.txt · .env.example · .gitignore · README.md
└── docs/
```

一文件一职责：**类（库）、界面（本体）、测试（防线）** 三类性质不同的代码分开放。`cli.py` 进包后加 `__main__` 守卫——包成员可能被 import，import 不得启动交互循环。

一次聊天轮的数据流：

```text
input()
  └─> 命令分发（本地路由，零 token）
        ├─ /exit /clear /resume ──> 本地处理
        └─ 聊天内容 ──> client.chat()
                        ├─ 构造请求快照：self.messages + [本轮 user]
                        ├─ API 调用 ──失败──> 分类：重试（指数退避）或放弃，返回 None
                        └─ 成功 ──> 原子提交：追加历史 + 累计 usage ──> 返回回复

退出（/exit · Ctrl+C · Ctrl+D 三种来源）
  └─> 唯一收尾出口：save() → report()
```

## 3. 核心设计决策

### 3.1 记忆：在无状态 API 上维护状态

Chat API 是无状态的——服务器处理完请求就忘。"记忆"是把完整历史装进 `messages` 每轮重发的工程效果。数据有三层生命周期，LLMClient 负责中间两层：

| 层 | 生命周期 | 谁管 |
|---|---|---|
| API 服务器 | 请求级（处理完即忘） | —— |
| `self.messages`（内存） | 进程级 | `chat()` 自动维护：成功后成对追加 user + assistant |
| `history.json`（磁盘） | 持久 | `save()` / `load()`，调用方显式触发 |

### 3.2 快照 + 原子提交：失败不留痕

每轮先构造**请求快照**（`self.messages + [本轮 user]`，不改动原列表），API **成功后**才把 user + assistant 成对提交进历史、并累计 usage；一切失败路径（重试中、放弃、非瞬时错误）状态原样不动。

由此获得三重"失败干净"：失败轮**不进历史、不计 token、不计成功调用**。不变量：`messages` 永远保持 `system + (user, assistant) × N` 的规整结构，不存在悬空的 user（问了但没被回答的消息）。

这也是重试安全的根基：重试 N 次也不产生半套副作用。

### 3.3 save / load：存整个会话，控制权给调用方

- **存整个 messages（含 system）**：人设是会话的一部分，只存对话会导致恢复后风格漂移；load 因此可以做纯替换，JSON 往返无损
- **显式调用、不进构造函数**：开新会话还是恢复历史，只有调用方知道；构造函数悄悄读文件违反最小惊奇原则
- **EAFP 分类兜底**：文件不存在是正常场景（首次运行——轻提示、开新会话）；JSON 损坏是异常场景（警告、保留当前会话）。两种都不崩溃，但语气与处理不同

### 3.4 错误处理：瞬时 vs 非瞬时，指数退避

判断标准一句话：**等一会儿，世界会不会自己变好？**（时间流逝能否改变现状）

| 异常 | 处理 | 理由 |
|---|---|---|
| `APITimeoutError` / `APIConnectionError` | 重试，1s → 2s → 4s 退避 | 网络抖动，等待有效 |
| `RateLimitError`（真限流） | 重试 | 名额随时间刷新 |
| `RateLimitError` 且 `code=SetLimitExceeded` | 立即放弃 | 配额用尽伪装成限流，重试无效 |
| `AuthenticationError` | 立即放弃，提示检查 .env | 错 Key 不会自己变对 |
| 其余 | 兜底捕获、打印原因、放弃 | 不裸崩 |

实现要点：

- **三条退出通道**：成功 `return` / 非瞬时 `break` / 可重试落到循环底部统一打印。重构循环时逐条核对——漏掉成功 `return` 会导致成功也在循环里重复调用（重复计费 + 历史污染）
- **429 必须二次判断**：异常类名只是第一道筛选，用 `(e.body or {}).get("error", {}).get("code")` 取结构化 code 确认真实成因（本服务方将配额用尽也映射为 429）；message 文案会误导人，只用于展示、不参与逻辑
- **except 顺序**：子类 `APITimeoutError` 必须写在父类 `APIConnectionError` 之前——写反不报错、程序照常跑，子类分支静默变成死代码

### 3.5 用量统计与成本估算

- **状态最小化**：只存 prompt / completion / cached 三个独立计数器 + `calls_succeeded`；total 是派生值，用的时候现算
- **累加位置在成功路径内**（return 前）：失败的请求没有 usage 可读，统计天然干净
- **计费公式**（glm-5.3，单位元/百万 token）：

  ```text
  费用 = (prompt − cached) × 8 / 1e6 + cached × 2 / 1e6 + completion × 28 / 1e6
  ```

  `cached_tokens ⊂ prompt_tokens`（details 字段是拆细、不是另算），不先扣除就把缓存部分收两次钱
- **`estimate_cost()` 返回裸 float**，格式化归 `report()`——接口给代码看，print 给人看
- **按数据归属选错误策略**：价格表是内部不变量，查不到直接 KeyError（fail loudly，错误的数字比崩溃更糟）；usage 里的外部字段（`prompt_tokens_details.cached_tokens`）用 `getattr` 防御回落（缺失按 0 只损精度、不损正确性）。同一段代码两种相反策略，依据是数据归属，不是风格

### 3.6 统计生命周期：跟进程，不跟会话

messages 要持久化（它决定下次请求发什么），usage 不持久化（它回答本进程花了多少）。`/clear` 只清对话、不清统计：清零会让报告从"本进程花了多少"降级为"当前会话花了多少"，已发生的消耗从账上消失——只少报、不多报。

### 3.7 CLI：先判后调 + 单一收尾出口

- **先判后调**：每行输入先本地路由（严格匹配 `text == "/exit"`，不做 strip / 大小写转换——更严格的匹配意味着更简单的代码），命令零 token、不进历史。顺序反了 = 命令词被当作聊天发给模型：白付一次调用费、命令进历史、模型回复不可预期
- **单一收尾出口**：三种退出（`/exit`、Ctrl+C、Ctrl+D）都 `break` 汇入循环外，收尾（save → report）天然只执行一次。不用 flag + finally——`finally` 里的 `break` 会吞掉在途异常。`try` 包住整个循环体，因为 Ctrl+C 可能打在等待 API 响应的几十秒里
- **/clear 与 /resume 是一对镜像**：resume 整体替换（人设随历史回来）；clear 保留当前首条 system（人设随会话保留）——两者都锚定**当前会话状态**。推论：resume 载入历史后 clear，保留的是载入历史的人设，不是进程默认人设
- **不猜用户意图**：`chat()` 返回 None 时打印清晰提示后继续等输入（退出权在用户）；resume 不设确认（敲命令即决策），但确有未保存对话被丢弃时打印丢弃条数——给足信息，决策留给人
- **启动前校验**：缺 `API_KEY` 直接给可操作的中文提示并退出（exit 1），好过构造时抛 SDK 英文 traceback

## 4. 接口约定

| 成员 | 签名 | 约定 |
|---|---|---|
| `chat` | `chat(user_prompt) -> str \| None` | 失败不抛异常、返回 None；仅成功请求改变对象状态 |
| `save` | `save(filepath="history.json") -> None` | 内部捕获全部异常，不向调用方抛 |
| `load` | `load(filepath="history.json") -> None` | 成功则整体替换 messages；任何失败保留当前会话 |
| `get_usage_summary` | `-> dict` | `cached / prompt / completion / total / calls` 五键 |
| `estimate_cost` | `-> float` | 价格缺失抛 KeyError（fail loudly） |
| `report` | `-> None` | 打印用量报告（格式化层，无返回值） |
| `messages` | `list[dict]` | 不变量：`system + (user, assistant) × N` |

## 5. 已知限制与演进方向

| 限制 | 说明 | 演进方向 |
|---|---|---|
| 同步阻塞 | 等待回复期间终端完全无法输入 | 流式输出（stream） |
| 长历史成本 | 历史每轮重发，prompt 线性膨胀、复利计费 | 截断 / 摘要压缩 / 检索式记忆 |
| 失败原因不可程序化 | None 只能感知失败，原因只在终端提示里 | 自定义异常或错误码 |
| usage 边界 | provider 不回 usage 时，当前顺序会先写历史再抛错 | 边界字段先消费、再提交 |

## 6. 贯穿的原则

1. **接口给代码看，print 给人看**：数值方法返回裸值，格式化归打印层
2. **副作用集中在成功路径**：快照 + 原子提交，失败不留痕、重试无副作用
3. **按数据归属选错误策略**：内部不变量 fail loudly，外部数据防御回落
4. **控制权给调用方**：显式 save / load、无确认弹窗、退出权在用户
5. **输出协议即测试协议**：`> ` 提示符与 banner 的稳定结构，既是用户体验也是自动化测试的解析依据
