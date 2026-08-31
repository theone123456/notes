# pytest 核心知识与面试八股

> 使用方式：Day1-2 按顺序学习前两大节（每节先看知识点再敲示例）；Day5 背诵第三大节问答。
> 所有示例均可直接放进 `../api_framework/` 里跑。

## 一、核心 API 详解（按面试权重排序）

### 1. fixture（面试权重约 50%）

**是什么**：提供测试前置条件/共享资源的机制，替代 unittest 的 setup/teardown，且支持传值、复用、细粒度控制。

```python
import pytest

@pytest.fixture(scope='session')       # 作用域，默认 function
def db_conn():
    conn = create_conn()              # setup（前置）
    yield conn                        # 把资源交给用例使用
    conn.close()                      # teardown（后置清理）

def test_query(db_conn):              # 用例通过形参声明依赖
    assert db_conn.query('select 1')
```

**必须掌握的要点**：

| 要点 | 说明 |
|---|---|
| 五级 scope | `function` < `class` < `module` < `package` < `session`，默认 function |
| yield 前后置 | yield 前是 setup，后是 teardown；一个 fixture 只能有一个 yield |
| setup 失败 | yield 前抛异常，该 fixture 判定为 ERROR，teardown **不会执行**；需要兜底时用 try/finally 或 `request.addfinalizer` |
| autouse | `@pytest.fixture(autouse=True)` 对作用域内所有用例隐式生效，无需形参声明 |
| params | `params=[1, 2]` 让依赖它的每条用例跑两遍，fixture 内用 `request.param` 取值 |
| name | 重命名 fixture，用例中用别名引用 |
| 依赖传递 | fixture 可以作为其他 fixture 的形参，形成链式依赖；不能循环依赖 |

**实例化顺序（面试必考，背下来）**：

1. 高级别 scope 先于低级别（session 最先，function 最后）
2. 同级别按**用例形参声明的顺序**（左边的先实例化）
3. `autouse` 的 fixture 先于同级别其他 fixture
4. 多个同级 autouse fixture 按**函数名字母序**
5. 显式声明的 fixture（形参）不声明就不实例化

**常见面试问法**：
- fixture 的作用域有哪几种？执行顺序？
- fixture 怎么做 teardown？setup 阶段就失败了呢？
- autouse 有什么坑？（隐式执行难排查、影响所有用例、粒度粗，一般只用于日志/计时这类横切逻辑）

### 2. conftest.py

**是什么**：pytest 约定的共享配置文件，主要用来放共享 fixture，**无需 import 自动生效**。

```python
# conftest.py 的 fixture 对其所在目录及子目录下所有用例可见
# 多层 conftest.py 同时存在时，全部生效，同名 fixture 就近覆盖（子目录 > 父目录）
```

**要点**：
- 加载时机：收集阶段自动加载，不用任何 import
- 可以有多层：根目录一份（全局），子目录各一份（模块专属）
- 同名 fixture：**就近覆盖**，子目录的覆盖父目录的
- 除 fixture 外还可放 `pytest_addoption`（自定义命令行参数）、`pytest_collection_modifyitems`（收集后处理）等钩子
- conftest.py 与被测代码不要放同一个包里搞循环导入

**面试问法**：conftest.py 的作用？和直接在测试文件里写 fixture 有什么区别？

### 3. parametrize（数据驱动）

```python
import pytest

# 单参数
@pytest.mark.parametrize('user_id', [1, 2, 3], ids=lambda i: f'用户{i}')
def test_get_user(user_id): ...

# 多参数：参数名与值一一对应
@pytest.mark.parametrize('username, password, expected', [
    ('admin', '123456', 200),
    ('admin', 'wrong', 401),
])
def test_login(username, password, expected): ...

# 叠加装饰器：笛卡尔积（2 x 2 = 4 条用例）
@pytest.mark.parametrize('env', ['test', 'preprod'])
@pytest.mark.parametrize('user', ['a', 'b'])
def test_combo(env, user): ...

# 外部数据驱动（yaml）
import yaml
with open('login_data.yaml', encoding='utf-8') as f:
    cases = yaml.safe_load(f)

@pytest.mark.parametrize('case', cases, ids=[c['case'] for c in cases])
def test_login_ddt(case): ...
```

**要点**：
- `ids` 让报告里的用例名可读（中文 case 名）
- 叠加多个 parametrize 生成笛卡尔积
- `indirect=True` 可把参数传给 fixture 而不是用例（进阶，了解即可）
- 数据与脚本分离：yaml/excel 存数据，脚本只写逻辑

### 4. mark（标记）

```python
import pytest

@pytest.mark.smoke          # 自定义标记
@pytest.mark.regression
def test_xxx(): ...
```

必须在 `pytest.ini` 注册，否则有 Unknown Mark 警告：

```ini
[pytest]
markers =
    smoke: 冒烟用例
    regression: 回归用例
```

**执行方式**：`pytest -m smoke`（只跑 smoke）、`pytest -m "not slow"`（排除）。

**内置标记**：`skip` / `skipif` / `xfail` / `parametrize` / `usefixtures`。

`@pytest.mark.usefixtures('fixture名')`：让用例/类使用某 fixture 但不接收返回值。

### 5. skip / skipif / xfail

| 标记 | 含义 | 典型场景 |
|---|---|---|
| `@pytest.mark.skip(reason='...')` | 无条件跳过 | 功能未实现、用例废弃但保留 |
| `@pytest.mark.skipif(条件, reason=...)` | 条件跳过 | 仅特定环境/版本执行 |
| `pytest.skip('...')`（函数内调用） | 运行时跳过 | 前置条件不满足时动态判断 |
| `@pytest.mark.xfail(reason=...)` | 预期失败 | 已知缺陷、依赖服务未修复 |
| `xfail(strict=True)` | 严格模式：用例若**通过**则报 XPASS 失败 | 防止"预期失败"被修复后没人发现 |

**skip 与 xfail 的本质区别**：skip 是"不执行/不评估"，xfail 是"执行了但预期它失败"。

### 6. 断言

```python
import pytest

# 裸 assert，失败时自动展示双方值对比
def test_add():
    assert add(1, 2) == 3, '加法计算错误'   # 第二个参数是失败时的说明

# 异常断言：pytest.raises
def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError) as exc_info:
        divide(1, 0)
    assert 'division by zero' in str(exc_info.value)

# match 参数：对异常信息做正则匹配
def test_login_error():
    with pytest.raises(ValueError, match='用户名不能为空'):
        login('', '123')

# 近似值断言
assert 0.1 + 0.2 == pytest.approx(0.3)

# 软断言（pytest-assume 插件）：多个断言都执行，失败一次全报
pytest.assume(resp.status_code == 200)
pytest.assume('@' in resp.json()['email'])
```

**面试问法**：pytest 怎么断言抛出的异常？match 参数干嘛的？软断言怎么实现？

### 7. 用例收集规则与配置文件

**收集规则（约定优于配置）**：
- 文件：`test_*.py` 或 `*_test.py`
- 类：`Test` 开头，且**不能有 `__init__` 方法**
- 函数/方法：`test_` 开头

**配置文件优先级**（高到低）：`pytest.ini` > `pyproject.toml([tool.pytest.ini_options])` > `tox.ini` > `setup.cfg`。

```ini
[pytest]
testpaths = testcases          # 只在该目录收集
python_files = test_*.py
addopts =                      # 默认追加的命令行参数
    -v
    --alluredir=reports/results
    --reruns 1
markers =
    smoke: 冒烟用例
```

### 8. 常用命令行参数

| 参数 | 作用 |
|---|---|
| `pytest` | 跑全部 |
| `pytest test_login.py` | 指定文件 |
| `pytest test_login.py::test_login` | 指定用例（nodeid） |
| `pytest -k "login and not slow"` | 关键字表达式筛选 |
| `pytest -m smoke` | 按 mark 筛选 |
| `pytest -v` | 详细模式（显示每条用例） |
| `pytest -s` | 显示 print/日志输出（禁用捕获） |
| `pytest --lf` | 只跑上次失败的 |
| `pytest --ff` | 失败的优先跑 |
| `pytest -x` | 首个失败即停止 |
| `pytest --maxfail=3` | 失败 3 个停止 |
| `pytest -n auto` | 并行（需 xdist） |
| `pytest --collect-only` | 只收集不执行 |
| `pytest --fixtures` | 列出所有可用 fixture |

### 9. monkeypatch（了解即可，防追问）

pytest 内置 fixture，用于运行时打补丁，**测试结束自动还原**：

```python
def test_env(monkeypatch):
    monkeypatch.setenv('ENV', 'test')           # 修改环境变量
    monkeypatch.setattr('module.func', fake)    # 替换函数/属性
    monkeypatch.delattr(obj, 'attr')            # 删除属性
    monkeypatch.setitem(d, 'key', 'value')      # 改字典项
```

### 10. 退出码（冷门但区分度高的考点）

| 退出码 | 含义 |
|---|---|
| 0 | 全部通过 |
| 1 | 有用例失败 |
| 2 | 用户中断 |
| 3 | 内部错误 |
| 4 | 命令行参数错误 |
| 5 | 没有收集到用例 |

CI 流水线里据此判断构建结果。

## 二、必会插件

```bash
pip install allure-pytest pytest-xdist pytest-rerunfailures pytest-assume
```

| 插件 | 用途 | 核心用法 | 面试考点 |
|---|---|---|---|
| allure-pytest | 报告 | `pytest --alluredir=reports/results`，`allure serve reports/results` | 报告里看什么：趋势图、用例分布、失败堆栈、step/attach、分类 |
| pytest-xdist | 并行 | `pytest -n auto` / `-n 4` | 每个 worker 独立进程，session fixture 每个 worker 执行一次（数据准备会被执行多份）；用例间有顺序依赖时不能并行 |
| pytest-rerunfailures | 失败重试 | `pytest --reruns 2 --reruns-delay 1` | 只重试 FAILED；与网络层重试的区别（见八股第 22 题） |
| pytest-assume | 软断言 | `pytest.assume(cond)` | 一个用例多个断言全部执行，失败一次性全暴露 |
| pytest-ordering | 控制顺序 | `@pytest.mark.run(order=1)` | 回答"怎么控制执行顺序" |
| pytest-dependency | 用例依赖 | `@pytest.mark.dependency()` | 依赖的前置失败则跳过后续 |

## 三、面试八股 32 问（含参考答案）

### 基础篇

**1. pytest 和 unittest 的区别？**
pytest 兼容 unittest；核心差异四点：①fixture 比 setup/teardown 更灵活（支持传值、作用域、依赖链）；②原生支持参数化（unittest 要依赖 ddt 库）；③裸 assert（unittest 要记 assertEqual 系列方法）；④插件生态庞大（allure/xdist/rerunfailures），且失败信息展示更友好（自动对比双方值）。

**2. pytest 的用例收集规则？**
文件 `test_*.py` 或 `*_test.py`；类 `Test` 开头且无 `__init__`；函数/方法 `test_` 开头。可通过 `pytest.ini` 的 `python_files/python_classes/python_functions` 修改。

**3. 常用命令行参数有哪些？**
`-k` 关键字筛选、`-m` 按 mark 筛选、`-v` 详细、`-s` 显示输出、`-x` 失败即停、`--lf` 只跑上次失败、`--ff` 失败优先、`-n` 并行、`--collect-only` 只收集。

**4. pytest 配置文件有哪些？优先级？**
pytest.ini > pyproject.toml > tox.ini > setup.cfg。常用配置项：testpaths、addopts、markers、python_files、log_cli。

**5. 一个目录下 test_ 开头的函数为什么没被收集？**
排查顺序：①是否在 testpaths 指定目录内；②文件名是否符合 `python_files` 规则；③类是否有 `__init__` 方法（有则整个类被跳过）；④函数名是否 test_ 开头；⑤是否被 skip 或未注册的 mark 影响。用 `pytest --collect-only` 看收集结果。

### fixture 篇

**6. fixture 的五种 scope 及生命周期？**
function（每条用例）、class（每个类）、module（每个文件）、package（每个包）、session（整个会话一次）。级别越高越早实例化、越晚销毁。选择原则：创建成本高、可复用的资源（连接、登录态）用高 scope；需要用例间隔离的数据用 function。

**7. fixture 的实例化顺序？**
①高 scope 先于低 scope；②同级按用例形参声明顺序；③autouse 先于同级其他；④多个同级 autouse 按函数名字母序；⑤未声明的 fixture 不实例化。

**8. yield 前后置与 setup/teardown 的区别？**
yield 把前置和后置写在同一个函数里，逻辑内聚、作用域可控、能向前者传值；setup/teardown 是固定名字的成对方法，无法传值、只覆盖单一作用域。fixture 中 yield 前抛异常则后置不执行（setup/teardown 中 setup 失败 teardown 同样不执行）。

**9. setup 阶段失败，teardown 还执行吗？怎么保证清理？**
不执行（fixture 认定为 ERROR）。兜底方案：①yield 前的代码用 try/finally 包裹关键清理；②用 `request.addfinalizer(fn)` 注册清理函数，注册之后的失败不影响已注册的清理执行；③资源本身支持 with 上下文管理器时直接 `with ... as x: yield x`，异常也能清理。

**10. conftest.py 的作用？同名 fixture 谁生效？**
存放共享 fixture 与钩子函数，自动发现无需 import，作用于所在目录及子目录。多层 conftest 同时生效，同名 fixture **就近覆盖**（子目录覆盖父目录）。

**11. autouse fixture 的特性和使用建议？**
无需形参声明即对作用域内全部用例生效，先于同级显式 fixture 执行。适合日志、计时、数据隔离这类横切关注点；不适合有返回值的业务 fixture（隐式依赖难排查、粒度粗）。

**12. fixture 怎么参数化？**
`@pytest.fixture(params=[1, 2])`，fixture 内部用 `request.param` 取当前值，依赖它的每条用例会跑 N 遍。适合"同一套前置，不同输入"的场景。

**13. fixture 之间可以依赖吗？循环依赖会怎样？**
可以，把被依赖的 fixture 作为形参传入即可（如 api_framework 里 `user_api(api_client)`）。循环依赖 A->B->A 会在收集/执行时报错，需要把公共部分抽成第三个 fixture 打破环。

**14. 一个 fixture 怎么给不同用例传不同数据？**
用 params 参数化 fixture；或拆成多个 fixture；或用例自己 parametrize + `indirect=True` 把参数转发给 fixture。

**15. fixture 返回多个值？**
返回 tuple，用例解包接收：`a, b = my_fixture`。更推荐返回 dict/dataclass，可读性更好。

**16. 如何只让某个测试类使用某 fixture？**
定义在该类内部（类级私有）；或放在该模块同级的 conftest.py；或用 `@pytest.mark.usefixtures('name')` 标在类上。

### 数据驱动篇

**17. parametrize 的用法？多参数、叠加是什么效果？**
单参数一个变量名一个列表；多参数用逗号分隔变量名 + 嵌套列表；叠加多个装饰器生成笛卡尔积。ids 参数自定义报告里的用例名。

**18. ids 参数有什么用？**
自定义用例在报告/命令行中的展示名，可传字符串列表或函数。数据驱动时用业务含义的中文 case 名，报告可读性大幅提升（如 `test_login[密码错误]`）。

**19. yaml 数据驱动怎么落地？**
yaml 存列表数据（每条一个 dict，含 case 名、入参、预期），脚本加载后传入 parametrize，ids 取 case 名。好处：非技术人员也能维护数据、数据与脚本分离。excel 同理（openpyxl 读取）。

**20. skip、skipif、xfail 的区别？strict=True 是什么？**
skip 无条件跳过、skipif 条件跳过、xfail 执行但预期失败。strict=True 时若用例意外通过会报 XPASS（严格失败），用于防止"预期失败"被修复后无人察觉。

### 工程篇

**21. 如何控制用例执行顺序？**
pytest 默认按收集顺序（文件内从上到下，多文件按字母序）。控制方式：pytest-ordering 的 `@pytest.mark.run(order=n)`、pytest-dependency 声明依赖关系。最佳实践是用例无序可跑（依赖前置改造成 fixture 造数），顺序控制只做兜底。

**22. 失败重试怎么实现？你项目里有两层重试，区别是什么？**
业务层：pytest-rerunfailures 插件 `--reruns N`，用例 FAILED 后整条重跑，适合网络抖动/环境不稳定导致的偶发失败。网络层：requests 的 HTTPAdapter(max_retries=N)，只针对连接拒绝、超时等**连接建立阶段**的异常自动重试，粒度是单次请求，不会重复提交已发出的业务请求。两者互补。

**23. 并行执行怎么做？有什么坑？**
pytest-xdist，`-n auto` 或 `-n 4`。坑：①每个 worker 独立进程，session fixture 每个 worker 各执行一次（造数逻辑会重复，需设计成幂等或用文件锁）；②用例间有顺序/数据依赖时不能并行；③ allure 报告正常合并，但耗时统计口径变化。

**24. 如何生成测试报告？allure 集成步骤？报告里主要看什么？**
步骤：装 allure-pytest -> pytest 加 `--alluredir=reports/results` -> `allure serve reports/results`（CLI 需 `brew install allure`）。看：失败用例的堆栈与请求日志、趋势图（质量走势）、用例按 feature/severity 的分布、执行时长排名（慢用例优化）。

**25. 软断言是什么？怎么实现？**
普通 assert 失败即终止，后面断言不再执行；软断言全部执行、失败统一报告。pytest-assume 的 `pytest.assume(cond)`；替代品 pytest-check 的 `with check: assert ...`。适合一个用例校验多个不相关字段的场景。

**26. 如何做 mock？monkeypatch 能做什么？**
monkeypatch 是内置 fixture：setenv/setattr/delattr/setitem，测试结束自动还原。复杂 mock 用标准库 unittest.mock（Mock/patch）。场景：依赖第三方服务未就绪、模拟异常分支、隔离外部副作用。

**27. 如何只跑上次失败的用例？**
`pytest --lf`（last-failed，只跑失败）；`pytest --ff`（failed-first，失败的排前面跑）。`.pytest_cache` 缓存了上次结果。

### 框架设计篇

**28. 你的自动化框架怎么分层？每层职责？**
四层：apis 接口封装层（一个业务模块一个类，屏蔽 URL/参数细节）；testcases 用例层（只写业务逻辑与断言，不出现 requests）；testdata 数据层（yaml 驱动，数据与脚本分离）；common 公共层（HTTP 客户端、配置、日志）。另加 conftest.py 管理 fixture 体系，pytest.ini 管理运行配置。收益：接口变更只改 apis 层；新人只写用例层即可上手。

**29. 接口测试断言哪些内容？**
①HTTP 状态码；②业务码/响应体关键字段（code/message/核心业务字段）；③数据一致性（调 DB 断言落库数据）；④响应时间（性能下限）；⑤schema 校验（字段类型/必填，可用 jsonschema）。反例是只断言 200。

**30. 如何保证用例独立性和数据清理？**
每条用例的依赖数据用 function 级 fixture 现场造数（setup 创建、teardown 删除），用例之间不共享可变数据、不依赖执行顺序；只读的公共数据可放高 scope fixture。登录态这类稳定资源用 session 级复用。

**31. 多环境切换怎么设计？**
yaml 按环境名分块存配置（base_url/账号/超时），conftest 里 `pytest_addoption` 注册 `--env` 参数，session 级 fixture 读取并注入客户端。运行时 `pytest --env=preprod` 切换，敏感操作（删除类用例）通过运行时 skip 限制环境。

**32. 自动化的价值如何量化？（必准备）**
准备 2-3 组真实感数据，例如：核心链路回归从手工 2 人天缩短到 10 分钟；冒烟用例覆盖 80% 核心接口，版本卡点平均提前 1 天发现阻塞性缺陷；失败自动重试消除了 90% 的环境抖动误报。面试官问"带来什么收益"时直接甩数字。
