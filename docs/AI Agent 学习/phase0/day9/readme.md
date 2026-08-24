# Day 9 学习笔记：异常处理与重试

> 核心命题：错误处理的全部设计源于一个判断--这个错误是**瞬时的还是非瞬时的**；判断标准只有一句话：**等一会儿，世界会不会自己变好？**
> 产出脚本：`error_experiments.py`（Step 2 实验）/ `llm_client_with_retry.py`（Step 3-4 编码，复制自 day8）

## 概念节：常见错误类型与 SDK 异常体系（Step 1）

> 来源：Step 1 概念任务 · 地基：Day 8 遗留预告（裸 `except Exception` + print，调用方拿到 None 无法区分错误类型）· 目的：建立异常分类地图 + 重试决策的判断标准

### 一次 API 调用的"旅程"：错误发生在哪一环，决定它是什么类型

```text
你的代码 ──HTTP请求──> 网络 ──> 服务器 ──HTTP响应──> 解析返回
```

| 旅程中的环节 | 出错表现 | 对应异常 |
|---|---|---|
| 参数本身错（model 名拼错） | 服务器回 400 拒收 | BadRequestError |
| 请求发出去了，网络断 / 太慢 | **根本没有 HTTP 响应** | APIConnectionError / APITimeoutError |
| 服务器收到但不让用 | 401 Key 错 / 429 太频繁 / 余额不足 | AuthenticationError / RateLimitError |
| 服务器自己病了 | 5xx | InternalServerError |
| 服务器回了但格式意外 | 解析失败（极少见） | APIResponseValidationError |

### openai SDK 异常家族树（本机 SDK 3.1.0 实测验证）

```text
APIError（所有 API 错误的根）
├── APIStatusError        ← 有 HTTP 响应，服务器明确回了错误状态码（带 .status_code）
│   ├── BadRequestError        400  参数错误（如 model 名写错）
│   ├── AuthenticationError    401  Key 无效 / 过期
│   ├── PermissionDeniedError  403  Key 对但没权限
│   ├── NotFoundError          404  路径 / 模型名不存在
│   ├── RateLimitError         429  请求过于频繁 / 配额用尽
│   └── InternalServerError    5xx  服务端故障
├── APIConnectionError     ← 没有 HTTP 响应，请求没送达 / 没返回（网络层）
│   └── APITimeoutError        请求超时（是上面的子类！）
└── APIResponseValidationError ← 响应解析失败（了解即可）
```

验证方式（不背文档，现场查任何库的继承关系）：

```python
import openai
print([c.__name__ for c in openai.RateLimitError.__mro__])  # mro = 方法解析顺序
```

**关键认知**：第一个分叉最有信息量--`APIStatusError` vs `APIConnectionError` 的区别是"**服务器有没有开口说话**"。它解释了两件事：

- 连接错误 / 超时**没有状态码**（发生在 HTTP 层之下）
- `APITimeoutError` 是 `APIConnectionError` 的子类--下文 except 顺序问题的根源

### 核心分类：瞬时 vs 非瞬时（Step 3/4 一切设计的地基）

| 异常 | 状态码 | 典型成因 | 重试？ | 理由 |
|---|---|---|---|---|
| APITimeoutError / APIConnectionError | 无 | 网络抖动、响应慢 | ✅ | 下一秒网络可能就通了 |
| RateLimitError | 429 | 这一分钟请求太多 | ✅ | 等一会儿名额刷新 |
| InternalServerError | 5xx | 服务端暂时故障 | ✅ | 通常一会儿自愈 |
| AuthenticationError | 401 | Key 本身错了 | ❌ | 等多久，错的 Key 也不会自己变对 |
| BadRequestError / NotFoundError | 400/404 | 参数 / 模型名错 | ❌ | 只有改代码才有用 |

判断标准一句话：**"等一会儿，世界会不会自己变好？"**--429 的成因是**时间性**的（此刻请求太多，等待改变现状），401 的成因是**配置性**的（Key 错了，等待不改变任何事）。所以 429 是 4xx（"你的问题"）里唯一通常该重试的。

### 余额不足：厂商差异陷阱

openai SDK 只映射标准状态码，但"余额不足"没有统一标准：

| 厂商 | HTTP 状态码 | SDK 抛出的异常 | 真实性质 |
|---|---|---|---|
| DeepSeek | 402 Payment Required | 通用 `APIStatusError`（SDK 无 402 映射），message 含 "Insufficient Balance" | 非瞬时 |
| 智谱（本项目在用） | 429，body 错误码 1113 | **`RateLimitError`**（伪装成"该重试"的样子！） | 非瞬时 |

> 一句话：异常类名是**第一道筛选**，message 内容是**第二道确认**。429 是唯一必须读 message 二次确认的分支：真限流才重试，1113 余额不足直接放弃并提示充值。

### except 分支顺序法则：越具体越靠前

机制（两条规则叠加）：

1. Python 从上到下逐个检查 except 分支，**第一个匹配的执行，后面的全部跳过**
2. 匹配标准是 isinstance--继承意味着"是一个"：`APITimeoutError` 的实例**同时是** `APIConnectionError` 的实例

实测验证（2026-08-24，本机 SDK 3.1.0）：

```python
from openai import APIConnectionError, APITimeoutError

# 写法一：父类分支在前
try:
    raise APITimeoutError(None)
except APIConnectionError:
    print("写法一: 被 APIConnectionError 捕获")   # ← 实际走这里，超时被父类截胡
except APITimeoutError:
    print("写法一: 被 APITimeoutError 捕获")       # ← 永远轮不到（死代码）

# 写法二：子类分支在前
try:
    raise APITimeoutError(None)
except APITimeoutError:
    print("写法二: 被 APITimeoutError 捕获")       # ← 正确：精确命中
except APIConnectionError:
    print("写法二: 被 APIConnectionError 捕获")
```

```text
写法一（父类在前）: 被 APIConnectionError 分支捕获
写法二（子类在前）: 被 APITimeoutError 分支捕获
```

类比：医院分诊--内科总台（父类）排在超时专科（子类）前面，所有超时病人都在总台被拦下，专科一个病人都接不到。且**不报错、程序照常运行**--这种"静悄悄的 bug"比崩溃更难查，也是 Step 3/4 的直接风险点：分支顺序写反，所有超时都掉进连接失败的提示里，日志里永远看不到超时的真实占比。

> 一句话：越具体的异常越靠前写，越通用的越靠后，兜底的 `Exception` 永远排最后（与 Day 8 `load` 里 FileNotFoundError / JSONDecodeError 排在 Exception 之前是同一个道理）。

### 检查点自测记录（2026-08-24，两题通过）

**检查点 1：说出 4 种常见错误的状态码、异常类名、典型成因 -- 4/4**

- 我的回答：401 AuthenticationError（Key 错/过期）/ 404 NotFoundError（base_url 或 model 不存在）/ 429 RateLimitError（请求过频，智谱可能是配额用尽）/ 5xx InternalServerError（服务器故障）
- review 补充：
  1. 漏了第五类：**无状态码**的 APIConnectionError / APITimeoutError--家庭网络下实践里最常见、最典型的瞬时错误
  2. 404/400 的映射因厂商而异（"模型不存在"有的报 400 有的报 404）--再次印证"类名第一道、message 第二道"

**检查点 2：无效 Key 该不该重试，为什么 -- 通过**

- 我的回答：不该。修复 Key 需要外部动作（改配置、充值），代码重试只是反复读同一个错 Key
- review 加强：这正是"瞬时 vs 非瞬时"的本质判据--不是看状态码数字，而是看**时间流逝能否改变现状**。同一逻辑延伸：智谱余额不足伪装成 429，但充值和改 Key 一样是外部动作，重试无效

## 本节记住五件事

1. **第一分叉看"服务器有没有开口"**：APIStatusError（有响应、有状态码）vs APIConnectionError（无响应、无状态码）
2. **重试判据一句话**："等一会儿世界会不会自己变好"--时间性（429/超时/5xx）重试，配置性（401/400/404）放弃
3. **余额不足陷阱**：智谱 429+1113 伪装成 RateLimitError；类名第一道筛选，message 第二道确认
4. **except 顺序**：越具体越靠前，APITimeoutError 必须写在 APIConnectionError 之前，否则成死代码且静默无报错
5. **429 是 4xx 里的例外**：客户端错误中唯一通常该重试的，但必须读 message 排除余额不足

---

## 实验记录：故意触发错误，采集真实报错（Step 2）

> 产出脚本：`error_experiments.py` · 模型：glm-5.3 · provider：火山引擎方舟（据报错信息推断，见发现 3）
> 目的：验证 Step 1 的异常分类理论，采集真实报错样例，作为 Step 3/4 编码的依据

### 实验设计

三个实验各改一个变量（工厂函数 `create_client` 负责参数覆盖），消息体保持确定合法（避免引入第四个变量污染归因）：

| 实验 | 触发方式 | 改动的变量 |
|---|---|---|
| 1 无效 Key | 真 base_url + 假 Key | api_key |
| 2 超时 | timeout=0.001 | timeout |
| 3 无效模型名 | 真 Key + "test_model" | model |

统一用 `except Exception` 捕获后打印：异常类名 / 状态码（`getattr(e, "status_code", None)`）/ message。

### 原始输出（2026-08-24）

```text
===== 实验 1：无效 Key =====
异常类名: AuthenticationError
状态码: 401
message: Error code: 401 - {'error': {'code': 'AuthenticationError', 'message': 'The API key format is incorrect. Request id: 021787582304089e4d5e3acd6b6d5c09c835e2d36b9596cbcf7c8', 'param': '', 'type': 'Unauthorized'}}

===== 实验 2：超时 =====
异常类名: APITimeoutError
状态码: None
message: Request timed out.

===== 实验 3：无效模型名 =====
异常类名: NotFoundError
状态码: 404
message: Error code: 404 - {'error': {'code': 'UnsupportedModel', 'message': 'The requested model does not support the coding plan feature. Please refer to the documentation at `https://www.volcengine.com/docs/82379/1925114` to select a compatible model. Request id: 0217875823055393d763aaa7a5e423f9e5323a8c500bc9fb40feb', 'param': '', 'type': ''}}
```

### 实验结果

| 实验 | 异常类名 | 状态码 | message 关键信息 | 瞬时？ |
|---|---|---|---|---|
| 1 无效 Key | AuthenticationError | 401 | "The API key format is incorrect" + Request id | ❌ |
| 2 超时 | APITimeoutError | None | "Request timed out."（无 body、无 Request id） | ✅ |
| 3 无效模型名 | NotFoundError | 404 | code=`UnsupportedModel`，文案提到 coding plan + volcengine 文档 | ❌ |

理论预测 3/3 全中（含 Step 1 检查点答的"404 NotFoundError"，被自己的环境证实）。

### 三个发现（理论没预言的部分）

**发现 1：status None 是"服务器没开口"的实锤**

实验 1、3 的报错都带完整 JSON body 和 Request id（服务器生成并留下的凭证）；实验 2 只有一句干巴巴的 "Request timed out."，什么都没有--这个错误诞生在本机的 SDK/httpx 里，请求根本没走完一个来回。Step 1 家族树的第一个分叉（APIStatusError vs APIConnectionError），在这里有了肉眼可见的证据。

**发现 2：message 会主动误导人**

发的是完全不存在的模型名 `test_model`，返回文案却是"不支持 coding plan 功能"+火山文档链接--光看文案绝猜不到真实原因是"模型不存在"。可靠的判别信号：**异常类 + 状态码 + 结构化 code 字段（UnsupportedModel）**。

**发现 3：provider 不是智谱官方，是火山引擎方舟**

报错链接指向 volcengine.com/docs/82379（方舟文档）。Step 1 假设的"智谱 429+1113"与本环境无关。教训：**别假设你的 provider，读它的报错**。

### 实验 4：rate limit / 配额用尽（官方文档样例，非本地实测）

本地触发不了 429，按计划采集样例。样例按火山方舟官方错误码文档（https://www.volcengine.com/docs/82379/1299023）的真实模板构造，body 结构与实验 3 实测格式一致：

```text
===== 样例 A：真·限流（可重试）=====
异常类名: RateLimitError
状态码: 429
message: Error code: 429 - {'error': {'code': 'ModelAccountTpmRateLimitExceeded', 'message': 'TPM (Tokens Per Minute) limit of the model is exceeded. Request ID: 02178758...', 'param': '', 'type': 'TooManyRequests'}}

===== 样例 B：配额用尽，伪装成 429（不可重试）=====
异常类名: RateLimitError
状态码: 429
message: Error code: 429 - {'error': {'code': 'SetLimitExceeded', 'message': 'Your account [xxx] has reached the set inference limit for the [glm-5.3] model, and the model service has been paused. To continue using this model, please visit the Model Activation page to adjust or close the "Safe Experience Mode". Request ID: 02178758...', 'param': '', 'type': 'TooManyRequests'}}
```

样例 A/B 的异常类名、状态码、type 全部相同，但 B 重试一万次也没用（关闭安心体验模式/充值是外部动作，时间流逝改变不了它）--"一个类名覆盖多种真实原因"在本 provider 的现场版本，等价于智谱的 429+1113 陷阱。

### 结论

1. **验证了概念节分类表**：三种错误的类名、状态码全部实测吻合，理论预测 3/3
2. **修正了"message 第二道确认"原则**（实验 3 证明 message 会骗人）：
   - 逻辑判断（重试/放弃/分支）-> 用 **异常类 + 状态码 + 结构化 code 字段**（如 `e.body["error"]["code"]`）
   - 给人看（日志、终端提示）-> 用 message，但记得它可能误导
   - 唯一下钻场景：一个类名多种成因（RateLimitError）-> 读结构化 code，不匹配 message 文本
3. **Step 4 重试设计的本地化依据**：RateLimitError 分支需二次判断--`Model*Rpm/TpmRateLimitExceeded` 是真限流可重试；`SetLimitExceeded`（配额用尽）直接放弃并提示用户处理额度

## 实验节记住四件事

1. **status None + 无 body = 本机错误**：超时/连接错误诞生在 SDK 里，服务器从没开口（反过来：带 Request id 的报错一定是服务器生成的）
2. **message 会骗人**：判别用 类名 + 状态码 + code 字段；文案只配给人看
3. **本 provider 的 429 陷阱**：`SetLimitExceeded` 是配额用尽伪装的限流，不可重试；`Model*RateLimitExceeded` 才是真限流
4. **读报错认 provider**：volcengine 文档链接暴露了真实链路--环境假设要用实测校准

