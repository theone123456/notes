# api_framework 项目精讲（面试讲解指南）

> 项目位置：`../api_framework/`，已验证通过：12 passed / 1 xfailed / 1 skipped（preprod 环境）。
> 被测系统：jsonplaceholder.typicode.com（免费业务 CRUD）+ httpbin.org（鉴权），无需自建服务。

## 一、项目一句话定位（面试开场白）

> "我搭了一套基于 requests + pytest 的接口自动化测试框架：apis 层封装业务接口、用例层只写业务与断言，yaml 做数据驱动，支持 test/preprod 多环境切换和自定义命令行参数，集成 allure 报告、失败自动重试和并行执行，两层重试机制（网络层 + 业务层），fixture 体系管理登录态和造数清理。"

## 二、目录结构与分层职责

```
api_framework/
├── pytest.ini                 # 运行配置：testpaths、addopts（allure+重试）、markers 注册
├── conftest.py                # 根 conftest：--env 参数、环境配置、全局客户端、autouse 计时
├── common/                    # 公共层：与业务无关的基础能力
│   ├── config.py              #   读 env.yaml（按环境）+ 加载测试数据
│   ├── http_client.py         #   Session 封装：超时、连接池、网络重试、请求日志
│   └── logger.py              #   控制台 + 按天滚动文件日志
├── apis/                      # 接口封装层（PO 思想）
│   ├── base_api.py            #   基类：持有统一 HTTP 客户端
│   ├── user_api.py            #   用户模块：get_user / list_users
│   └── post_api.py            #   帖子模块：增删改查 + 按用户过滤
├── testcases/                 # 用例层：只写业务逻辑与断言，不出现 requests
│   ├── conftest.py            #   业务 API 对象、登录态 auth_client
│   ├── test_login.py          #   yaml 数据驱动正反用例 + 参数化 ids
│   ├── test_user.py           #   软断言（assume）+ 列表循环断言
│   └── test_post.py           #   fixture 造数清理、运行时 skip、xfail(strict)
└── testdata/
    ├── env.yaml               # test / preprod 双环境配置
    └── login_data.yaml        # 登录测试数据（数据驱动）
```

**分层收益（面试必讲）**：
- 接口 URL/参数变更只改 `apis/` 层，用例零改动
- 用例作者不需要懂 requests 细节，上手成本低
- 数据（testdata）、配置（env.yaml）、逻辑（testcases）三者分离

## 三、一条用例的完整执行链路

以 `test_login[错误的密码]` 为例：

```
pytest --env=test
  └─> 根conftest: pytest_addoption 注册 --env
      └─> fixture: env_config(session)     读 env.yaml 的 test 块
          └─> fixture: auth_client(session) 建 HttpClient，设置登录凭证并校验 200
              └─> 用例: test_login          parametrize 取 yaml 中一条数据
                  └─> HttpClient.get()       统一日志 + 超时 + 网络重试
                      └─> assert             失败则由 rerunfailures 重跑 1 次
                          └─> allure 收集结果 -> reports/results
```

同时每条用例前后，`case_logger`（autouse）打印开始/结束与耗时。

## 四、关键设计点逐个讲

### 4.1 fixture 体系（项目的骨架，面试核心）

| fixture | scope | 职责 | 面试考点 |
|---|---|---|---|
| `env_config` | session | 读环境配置，整轮只读一次 | session 级的实例化时机 |
| `api_client` | session | 业务系统客户端，连接池全用例复用；teardown 关闭会话 | 为什么用 Session 不用 requests.get |
| `auth_client` | session | 登录态客户端（httpbin basic-auth），凭证存在会话里后续自动携带 | 登录态如何全局共享 |
| `user_api` / `post_api` | session | 业务对象，依赖 api_client（fixture 链式依赖） | fixture 相互依赖 |
| `created_post` | function | 每条用例独立造数，yield 后自动删除 | 前后置 + 造数清理 |
| `case_logger` | function, autouse | 全部用例前后打日志、计时 | autouse 的适用场景 |

### 4.2 环境切换

`pytest_addoption` 注册 `--env`（choices 限制取值），`env_config` 据此读 yaml 对应块。危险操作限制：`test_delete_post` 内运行时判断 `--env != test` 则 `pytest.skip()`。运行 `pytest --env=preprod` 可看到该用例 skip。

### 4.3 两层重试（高频追问）

- **网络层**：`HTTPAdapter(max_retries=3)`，只重试连接建立阶段的异常（连接拒绝/DNS），不重复提交业务请求
- **业务层**：pytest.ini 的 `--reruns 1 --reruns-delay 1`，整条用例失败后重跑，应对环境抖动导致的偶发失败

### 4.4 数据驱动

`login_data.yaml` 存正反用例（正确账号/错误密码/错误账号），`load_cases()` 加载后传给 `parametrize`，`ids` 用 case 名，报告中显示 `test_login[错误的密码]` 这种可读名称。新增用例只改 yaml 不改代码。

### 4.5 skip / xfail 的实际应用

- `test_delete_post`：运行时 skip（非 test 环境不执行删除）
- `test_created_post_is_persisted`：`@pytest.mark.xfail(strict=True)`，标记"Mock 服务数据不落库"这一已知事实；strict 保证一旦行为变化（真的落库了）会立刻暴露

### 4.6 日志与报告

`HttpClient.request` 统一记录 `--> 请求` / `<-- 状态码+耗时`，配合按天滚动文件日志（logs/）。用例失败时 pytest 自动展示 captured log，配合 allure 报告可定位到具体是哪次请求失败。

## 五、运行方式

```bash
cd api_framework
../.venv/bin/python -m pytest                    # 全量（含 allure 结果生成）
../.venv/bin/python -m pytest -m smoke           # 只跑冒烟用例
../.venv/bin/python -m pytest -k login           # 关键字筛选
../.venv/bin/python -m pytest testcases/test_post.py::test_create_post   # 精确到单条
../.venv/bin/python -m pytest --env=preprod      # 切换环境（删除用例自动 skip）
../.venv/bin/python -m pytest -n 3               # 3 进程并行
../.venv/bin/python -m pytest -s                 # 实时看请求日志
../.venv/bin/python -m pytest --lf               # 只跑上次失败的
allure serve reports/results                     # 打开报告（需先 brew install allure）
```

## 六、面试话术（STAR 模板，背熟）

**S（背景）**：团队回归主要靠手工，版本迭代快，核心链路每次回归要 1-2 人天，且环境不稳定导致偶发漏测。

**T（目标）**：把核心接口的回归自动化，做到版本卡点自动执行、失败自动定位。

**A（做法）**：基于 requests + pytest 搭了分层框架——apis 层封装业务接口，用例层只写业务断言；yaml 做数据驱动，加一条用例只改数据文件；conftest 管理 fixture 体系，session 级复用登录态和连接池，function 级 fixture 现场造数、用例结束自动清理保证独立性；支持 --env 多环境切换；集成 allure 报告和失败自动重试。

**R（结果）**：核心链路回归从 2 人天降到 10 分钟，冒烟覆盖 80% 核心接口，偶发环境问题通过重试消除了大部分误报，失败用例凭日志和报告 5 分钟内可定位。

## 七、常见追问与参考回答

**Q1：为什么用 Session 不直接 requests.get？**
Session 复用 TCP 连接（连接池），避免每条用例重建连接，速度更快；且可以统一维护 headers/登录凭证，后续请求自动携带。

**Q2：conftest.py 为什么分两个？**
根 conftest 放与业务无关的全局能力（配置、客户端、autouse 日志），testcases/conftest 放业务 fixture（API 对象、登录态）。职责隔离，将来加 UI 用例目录时根层直接复用。

**Q3：created_post 为什么是 function 级？**
保证用例独立性：每条用例用自己的数据，用例间互不影响、可以乱序/并行执行；yield 后删除实现自动清理。如果造数成本高才考虑提升 scope。

**Q4：用例之间有依赖（比如下单依赖登录）怎么办？**
优先把依赖改造成 fixture：登录态由 session 级 fixture 提供，下单的前置数据由 fixture 造数。原则是用例之间不直接依赖执行顺序，依赖都下沉到 fixture。

**Q5：--env 参数是怎么实现的？**
conftest 的 `pytest_addoption` 钩子注册命令行选项，session 级 fixture 用 `request.config.getoption('--env')` 取值，再读 env.yaml 对应环境的配置块注入客户端。

**Q6：框架怎么扩展？**
加业务模块：apis 下加一个类 + testcases 加一个文件，互不影响；加 DB 断言：common 加 db 工具类，conftest 注册连接 fixture；接 CI：Jenkins/GitLab CI 里一条命令跑 pytest，allure 结果归档。

**Q7：xfail(strict=True) 的意义？**
预期失败的用例如果突然通过了，strict 模式会报 XPASS 失败，提醒"缺陷可能已修复或预期错了"，防止标记变成永久免检。

## 八、扩展练习（按顺序完成，做完才算掌握）

| # | 任务 | 验收标准 |
|---|---|---|
| 1 | 给 `login_data.yaml` 加一条"账号为空"用例 | 报告中出现新的中文 case 名且通过 |
| 2 | 新增 todos 模块：`apis/todo_api.py` + `testcases/test_todo.py`（jsonplaceholder 的 /todos） | CRUD 用例全部通过 |
| 3 | 故意改坏一个断言跑一次，再看 allure 报告 | 能从报告中定位到失败的那次请求 |
| 4 | 把 `test_user.py` 的 user_id 参数化改为 yaml 数据驱动 | 与改造前用例数一致、全部通过 |
| 5 | 新增一个 session 级 fixture 打印整个会话总耗时 | 日志中该信息只出现一次 |
| 6 | 安装 pytest-ordering，控制 test_post.py 中用例先跑 update 再跑 get | 命令行输出顺序符合预期 |

> 进阶方向（有余力再做）：统一响应封装类（状态码+业务码断言一处搞定）、jsonschema 响应结构校验、Jenkinsfile 一条流水线把框架跑起来。
