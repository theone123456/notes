# Day 12 学习笔记：代码整理与 Git

> 核心命题：从"能跑的代码"到"规范的仓库"--职责拆分、README 面向无上下文读者、检查点做在决定之前
> 产出：`projects/llm_client/` 独立仓库（Step 1 设计 → Step 2 拆分重构 → Step 3 README 与启动校验 → Step 4 git 首提；Day 12 五步全部完成）

---

## 项目设计节：仓库边界与项目结构四问（Step 1）

> 来源：Step 1 思考任务 · 原始作答：`self_design_step1` · review 后三处精化（projects/ 复数命名、仓库根补 requirements.txt、"测试数据"改为"运行时产物"）· 2026-09-02

### Q1 仓库边界：projects/ 下独立建仓，一项目一 repo

- **结论**：新建 `Development/projects/` 专门存放独立项目；每个项目一个目录 = 一个本地 git 仓库 = 将来 GitHub 上一个 repo。`llm_client` 项目在 `projects/llm_client/` 内 `git init`
- **理由**：阶段 2/4/5 各有产出项目，都要上 GitHub--一项目一仓的边界今天定下，学习过程（phase0/dayN）不混进求职项目
- **否决项**：直接在 `Development/` init--`.env`（真实 Key）、`.venv`、学习草稿全在旁边，历史混杂且风险高
- **命名（review 精化）**：用复数 `projects/`，与 `docs/`、`tests/` 的复数惯例一致

### Q2 文件拆分：包结构 + 仓库标准件

```text
Development/projects/llm_client/     # 仓库根（git init 在此）
├── llm_client/                      # 包
│   ├── __init__.py                  # 包身份标记（空文件或 re-export LLMClient）
│   ├── client.py                    # LLMClient 类（被 import 的库）
│   └── cli.py                       # 命令行界面（程序本体）
├── tests/
│   └── test_cli.py                  # 回归资产
├── pytest.ini                       # 默认排除 api 标记，防误烧 token
├── requirements.txt                 # 环境配方（review 补充）
├── .gitignore                       # 入库过滤器：挡隐私/环境/缓存/运行时产物
├── .env.example                     # 配置模板：只有变量名，没有值
├── README.md                        # 产品视角门面
└── docs/                            # Day 14 学习笔记预留位
```

- **拆分原则**：一个文件一个职责--类（被 import 的库）、界面（程序本体）、测试（回归防线）三类性质不同的代码分开放。Day 11 已打过样（`chat_cli.py` 只放界面逻辑）
- **requirements.txt（review 补充）**：README 要写"依赖安装"，仓库里必须有文件支撑；**环境不入库，入库的是重建环境的配方**。版本钉死当前环境：`openai==3.1.0`、`python-dotenv==1.2.2`、`pytest==9.1.1`（标注仅测试用）
- **venv 选择**：继续用 `Development/.venv`（绝对路径激活）或在项目内自建（`.gitignore` 已覆盖），有了配方后两者等价

### Q3 什么不进库：分类法 + 逐文件验证

分类法（优于逐个列举，可迁移到未来项目）：

| 分类 | 本项目对应 | 删除/泄露代价 |
|---|---|---|
| 隐私数据 | `.env`（真实 Key）、`history.json`（个人对话） | 泄露不可逆，Key 须作废重发 |
| 可重建环境 | `.venv/` | `pip install -r requirements.txt` 一条命令重建 |
| 缓存/生成物 | `__pycache__/`、`.pytest_cache/` | 零代价，随时再生 |
| 运行时产物 | 测试在 tmp_path 产生的数据 | 零代价 |
| 日志文件 | （暂无，面向未来） | — |
| 项目不相关 | `.DS_Store`、编辑器配置等 | — |

- **分类调整（review）**："测试数据"改为"运行时产物"（消歧义）；新增"可重建环境"（`.venv` 归位）；"临时文件"并入"缓存/生成物"（同义合并）
- **关键修正**：**测试代码（tests/）必须入库**--它是回归资产、求职加分项；不入库的只是测试运行产物。字面照读"测试数据不上传"会把防线本身排除在仓库外
- **`.venv` 归类精化**：不是"项目不相关文件"，是"可重建环境"--区别在于：项目不相关 = 删了跟项目无关；可重建 = 删了能用配方重建。归对类的意义是知道自己删得起
- **配套动作**：`.env.example` 进库（只有变量名没有值），仓库可用且安全

### Q4 README 的读者：无上下文的访问者

- **结论**：非作者本人、其他访问该项目的人，能快速了解项目的功能与使用方式（30 秒标准）
- **操作推论（review 补充）**：这个读者没有作者的任何上下文--不知道 Day 8-11 设计史、不知道 `.env` 放哪、不知道 glm-5.3 是什么。因此 README **禁止自指引用**（"如 Day 11 所述"、"见 design.txt"），所有前置知识默认为零
- **分工**：README = 产品视角（是什么、怎么用）；`docs/` = 学习叙事（为什么这么设计、踩过什么坑）

### 实现规格汇总（Step 2-4 直接照此执行）

```text
仓库位置   Development/projects/llm_client/（git init 在此）
目录结构   llm_client/ 包（__init__.py + client.py + cli.py）
           + tests/test_cli.py + pytest.ini + requirements.txt
           + .gitignore + .env.example + README.md + docs/
入库范围   代码、测试、配置模板、README 进库；
           隐私数据 / 可重建环境 / 缓存生成物 / 运行时产物一律不进
README     产品视角、无自指、前置知识为零；Quick Start 每条命令验证过
```

### 检查点自测记录（2026-09-02）

> Q1：原始作答（对话提交）+ review 两处修正后定稿 · Q2/Q3：AI 生成，2026-09-02 本人复核通过（Step 5 自测题 2 将回收 Q2）

1. **为什么 `.gitignore` 必须在首次提交之前就位，而不是提交后再补** -- 原始作答核心链条通过：进过提交 → 历史里留着 → 删历史也难清干净 → 非必要上传 / 隐私泄露。两处修正：
   - **修正 1："提交后再补只保证后续不上传"不成立**。`.gitignore` 只对**未跟踪**文件生效；已跟踪文件加进 ignore 后照样被跟踪（`git status` 照常出现、`git add .` 照常捕获）。完整补救是三步，而不止补一行 ignore：`git rm --cached`（停止跟踪，ignore 从此才对它生效）→ `commit`（提交"删除"，只是后续版本不再有它）→ 改写历史（旧提交里那份还在，须 filter-repo 级操作）
   - **修正 2："删历史仍能查到"的三层机制**。① 本地：改写历史后旧提交变 unreachable，但 reflog 仍指向它（默认可达 90 天 / 不可达 30 天），`git fsck` 可找回，要等 `git gc` 才物理清除；② 已 push：别人的 clone / fork 不受上游改写影响，GitHub 对被改写的 commit 还有按 SHA 访问的缓存；③ 时间不可逆：公开仓库的 Key 被扫密机器人**分钟级**捕获，"有没有人看过"不可证明
   - **分类结论**：非必要文件（如 `history.json`）→ `rm --cached` + 改写历史，可控善后；隐私（Key）→ 改写历史只是善后的一半，**唯一可靠补救是作废重发（rotate）**。这也是 Step 4 顺序「`.gitignore` 先行 → add → `status` / `ls-files` 检查 → commit」的根据：检查点做在决定之前，一步都不需要补救

2. **一句话说清拆分后每个文件的职责**（AI 生成，2026-09-02 复核通过）：
   - `client.py`：`LLMClient` 类--唯一与 API 打交道的地方，管对话状态、重试、统计、存取；被 import 的库
   - `cli.py`：命令行界面--读输入、本地分发命令、调类聊天、统一收尾；程序本体，不含 API 细节
   - `tests/test_cli.py`：回归防线--子进程跑 CLI 断言行为，重构时"没改行为"的证明
   - `pytest.ini`：测试配置--默认排除 api 标记，防日常回归误烧 token
   - `requirements.txt`：环境配方--环境不入库，入库的是重建环境的一条命令
   - `.gitignore`：入库过滤器--把隐私、环境、缓存、运行时产物挡在仓库外
   - `.env.example`：配置模板--告诉读者需要哪些环境变量，只有变量名没有值
   - `README.md`：仓库门面--产品视角，30 秒看懂是什么、怎么跑
   - `docs/`：学习叙事的归宿--README 不写的"为什么"放这里
   - `llm_client/__init__.py`：包身份标记--让目录成为可 import 的单元

3. **四问都有明确答案和理由**（AI 生成浓缩版，2026-09-02 复核通过，全文见上方 Q1-Q4）：
   - 仓库边界：`projects/` 下独立建仓，一项目一 repo，学习过程不混入
   - 文件拆分：包结构（client / cli 分离）+ tests + 标准件（requirements / gitignore / env.example / README / docs）
   - 什么不进库：六分类法（隐私 / 可重建环境 / 缓存生成物 / 运行时产物 / 日志 / 项目不相关），五个具体文件逐一归位验证
   - 读者：无上下文的访问者，30 秒看懂功能与用法；由此推出 README 禁止自指引用

### 本节记住五件事

1. **`.gitignore` 只对未跟踪文件生效**：事后补救是三步（`rm --cached` → commit → 改写历史）；隐私泄露唯一可靠补救是作废重发
2. **一项目一仓库**：`projects/` 是求职项目的家，今天定的边界服务阶段 2/4/5 的每个产出
3. **"测试数据"是陷阱词**：测试代码必须入库（回归资产 + 加分项），不入库的只是运行时产物
4. **环境不入库，入库的是配方**：`.venv` 是"可重建环境"不是"项目不相关"，归对类才知道自己删得起
5. **README 面向无上下文读者**：禁止自指引用、前置知识为零；学习叙事归 `docs/`

---

## 编码节：拆分文件 + 补关键注释 + 回归验证（Step 2）

> 来源：Step 2 编码任务 · 产出：`projects/llm_client/`（llm_client 包 + tests + 配置件）· 流程：初版为自写的复制迁移，review 实测不通过（零 API 8/8 红、`-m` 启动崩）→ 按 review 方案修复 → 全绿定稿 · 2026-09-02

### 教训的主体：初版是"文件搬家"，不是重构

目录骨架和标准件（requirements.txt / .gitignore / .env.example）都对了，但 Step 2 的实质动作零落地，review 实测当场现形：

| Step 2 要求 | 初版实际 | 实测后果 |
|---|---|---|
| 包内正确 import | 裸平级 `from client import` | `python -m llm_client.cli` ModuleNotFoundError |
| `__main__` 守卫 | 模块级代码裸在顶层 | 任何人 import llm_client.cli 即启动 REPL |
| 测试适配 | day11 原样复制 | `CHAT_CLI` 指向不存在的 tests/chat_cli.py，8/8 全红 |
| 补关键注释 | client.py 零 docstring、cli.py 注释全删 | 文档资产倒退 |

**重构的定义是"不改行为"，证明只能来自测试**。初版连测试都没跑就交付——而测试红了 0.26 秒就暴露全部问题。"我觉得没改"不是证据，"测试全绿"才是。

### 机制 1：包内 import 的三种写法

```text
裸平级   from client import LLMClient
         只在"直接跑文件"时碰巧工作：sys.path[0] = 文件所在目录；
         -m 包方式下顶层不存在 client 模块 -> 崩

绝对     from llm_client.client import LLMClient      （本仓库采用）
         前提：项目根在 sys.path——-m 靠 cwd、测试靠注入的 PYTHONPATH

相对     from .client import LLMClient
         只依赖文件自身位置（沿 __init__.py 链定位包），
         IDE 静态分析零配置可解析（见"红线决策"）
```

### 机制 2：`-m` 运行方式与测试隔离的兼容

测试的隔离机制是"子进程 cwd = tmp_path"（history.json 相对运行目录落盘，不碰真实历史）；`-m` 的包查找又要求项目根可见——cwd 是临时目录，两者天然打架。解法：**cwd 保持 tmp_path（隔离不动），包路径改走环境变量**——`env["PYTHONPATH"] = 项目根`（拼接已有值），子进程两头都满足。

### 机制 3：`__main__` 守卫的前提变化

Day 11 的结论是"CLI 顶层不套守卫，因为没人 import CLI"。进包后**前提失效**：包成员天然可被 import（测试、其他程序都可能是调用方）。前提变，结论跟着变——模块级代码收进 `main()`，加 `if __name__ == "__main__"` 守卫。附带收益：启动前校验有了自然的落点（Step 3 用到）。

### IDE 红线：两套找包机制（已认知，决定不修）

- **红线本质**：IDE 静态分析的解析告警，不是运行时错误——pytest 8/8 绿、程序能跑
- **机制**：运行时找包靠 sys.path（`-m` 给 cwd、测试给 PYTHONPATH）；IDE 找包靠它自己的搜索路径（工作区根 + 解释器 site-packages + extraPaths）。**两边互不知情**：openai / dotenv 没红线是因为真装在 venv 里；llm_client 只活在运行时约定里，IDE 看不见
- **四方案**：相对导入（零配置消红）/ 独立工作区打开项目 / extraPaths（.vscode 已被 gitignore，不随仓库走）/ pyproject + `pip install -e .`（终态方向：装进环境后运行时 / IDE / 他人 clone 全一致）
- **决定**：保持绝对导入，不修。红线是 IDE 私有问题，不影响运行、测试、提交；阶段 2 手写框架升级到 pip install -e 时自然消解
- 定位：Day 11"缺库红线 = 解释器绑定问题"的进阶变体——解释器绑对了，缺的是自家包不在搜索路径上

### 读者原则的三级延伸：README 禁自指 → 注释自包含 → 笔记脱敏

day11 注释里的"Q3 镜像原则""Day 10 在类内部 catch"对仓库读者是断链引用，随迁时改为自包含表述（"与 load() 的整体替换互为镜像""save() 内部已捕获全部异常"）。**读者原则管的不止 README，是一切会被别人读到的文本**。

**第三级（Day 12 收官补）：笔记文本本身脱敏**。触发：git 身份信息（macOS 自动生成的 `用户名@主机名.local`）被写进笔记时发现——笔记将来要整理进仓库 `docs/` 随仓库公开，读者原则对它同样生效。规则：个人身份信息（用户名 / 主机名 / 邮箱 / Key / 个人对话内容）一律用通用占位；判断标准很朴素——**通用占位不损知识点，真实值不增任何信息量**（`用户名@主机名.local` 照样讲得清坑在哪）。

### 本节记住五件事

1. **文件搬家 ≠ 重构**：import 方式、守卫、测试适配、注释——不动这些就只是移动文件；"没改行为"的证据只能是测试全绿
2. **裸平级 import 是幻觉路径**：它借"直接跑文件"的 sys.path[0] 碰巧工作；包的正道是绝对（根在 path）或相对（靠文件位置）
3. **守卫判据会漂移**："有没有人 import 我"取决于代码住在哪——进包那一刻判据就翻转了
4. **两难拆给两个维度**：cwd 管隔离、PYTHONPATH 管找包——冲突不必二选一
5. **红线先问"谁在报、影响什么"**：静态分析告警 ≠ 运行错误；先分清性质，再决定修不修

---

## 编码节：README 与新人视角自查（Step 3）

> 来源：Step 3 编码任务 · 产出：`README.md`（七节）+ cli.py 启动前校验 · 流程：AI 起草 → 新人视角全链路自查抓到三个真问题并修复 → 验证链全绿 → 本人 review 通过 · 2026-09-02

### 方法：把"新人视角"变成可执行流程

"每条命令验证过"不是态度，是动作清单：

```text
① 复制项目到 /tmp，剔除 .env / history.json / 缓存    == 模拟 git clone
② 新建 venv + pip install -r requirements.txt         == 验证配方完整性
③ 不带 .env 启动                                       == 验证配置缺失路径
④ dummy .env（无效 Key + 真实 BASE_URL）+ pytest       == 验证测试可复跑
⑤ 真实项目回归 pytest                                   == 确认修复没碰坏原行为
```

### 真问题 1：无 .env 启动裸崩 → 启动前校验

- **现象**：`OpenAI(api_key=None)` 构造即抛 OpenAIError——英文裸 traceback，还提示设置 `OPENAI_API_KEY`（本项目变量是 `API_KEY`，双重误导）
- **修复**：`main()` 开头校验 `os.getenv("API_KEY")`，缺失则中文可操作提示 + `SystemExit(1)`
- **原则落地**：系统边界处本地校验（Day 11"本地可判断的先本地处理"）；`not os.getenv(...)` 同时覆盖 None 和空串，与类内 `api_key or os.getenv` 的 falsy 语义一致

### 真问题 2：BASE_URL 的缺省行为是文档义务

- **现象**：dummy .env 没配 BASE_URL → 请求发往官方 api.openai.com → 本网络不可达 → 每轮挂满 30s 超时 × 重试 4 次 → `test_wrong_key` 120s 超时爆红
- **两个教训**：
  1. 配置项的缺省行为（不配会怎样、请求发给谁）必须写进文档，不是读者的推理题——README 变量表已补"不配置则请求发往官方 OpenAI 接口"
  2. Day 9 的重试设计救不了配置错误：重试的语义对象是**暂时性故障**，对"永久不可达"只会白白烧时间——鉴权错误立即放弃已经区分了这一点，连接错误在协议层区分不了暂时/永久（记录认知，不改代码）

### 真问题 3：Python 3.10+ 是 pip 级硬门槛

- **现象**：系统 `python3` = 3.9.6，`pip install -r` 报 "No matching distribution found for openai==3.1.0"——版本明明存在
- **机制**：openai 3.x 声明 requires-python ≥3.10，pip 在低版本解释器上直接把它从候选里过滤，报错只字不提原因
- **教训**：README 第一行的环境要求不是仪式感；macOS 系统 python3 的版本要主动确认（验证改用 3.13 venv 即通过）

### 测量教训：`$?` 必须紧跟取值

`out=$(cmd); echo "$out"; echo "exit=$?"`——第二个 `$?` 取到的是 **echo 的退出码**（恒 0），制造了"exit=0"假象。正确姿势：`out=$(cmd); code=$?; ...`。管道同理：`$?` 取的是管道最后一个命令的退出码。

### 零 API 套件的隐性配置依赖

测试要构造 `LLMClient()`，就得过 `OpenAI()` 的 Key 校验——所以零 API 套件也需要 **API_KEY 有值**（值无效亦可：不发真实请求，`test_wrong_key` 反而要求无效 Key）。"测试对环境的依赖"同样是文档义务，README 测试节已写明。

### 本节记住五件事

1. **新人视角自查是流程不是口号**：clone 模拟 / 新 venv / 缺配置 / dummy 配置 / 原项目回归——五步走完才算"命令验证过"
2. **报错信息是系统边界的一部分**：裸 traceback + 误导变量名 = 边界失守；启动前校验用一条 if 消解
3. **配置项缺省行为是文档义务**；重试救不了配置错误——它的语义对象是暂时性故障
4. **requires-python 的报错最具迷惑性**：pip 报"版本不存在"，实际是"解释器不够格"
5. **`$?` 紧跟取值**：隔一条命令，就是别人的退出码

---

## 操作节：git init 与首次提交（Step 4）

> 来源：Step 4 操作任务 · 产出：本地仓库（分支 main）+ 首次提交 `f6b68c5` · 流程：自写 init / add / commit → review 首查（入库范围 / ignore 生效 / 提交内容三查全过）→ 作者身份修正 → 复审定稿 · 2026-09-02

### 首次提交的检查闭环

顺序即安全（"检查点做在决定之前"的 git 版）：

```text
.gitignore 先行（Step 1 定稿）
  -> add 具体文件（不用 add .，把检查做在决定之前）
  -> git status 肉眼过目
  -> git ls-files 确认入库清单（.env / .venv / __pycache__ / history.json 均不在）
  -> commit（一行说清是什么，feat: 前缀）
  -> git log / git show --stat 复核
```

**check-ignore -v 的角色**：光看 ls-files 干净，分不清是"规则挡住的"还是"碰巧没 add"。`git check-ignore -v .env history.json` 输出命中的规则行号（.gitignore:2 / :3），把 ignore 的生效性本身变成可验证的事实——"证明交给可重复的机制"在 git 操作上的又一次应用。

### Git 身份：name 是显示文本，email 是关联键

| | user.name | user.email |
|---|---|---|
| GitHub 是否检查 | 完全不看 | 关联提交与账号的**唯一依据** |
| 匹配要求 | 无（求职建议与简历一致） | 账号绑定邮箱列表中任意一个（真实邮箱或 noreply 均可） |
| 不匹配后果 | 无 | 提交不关联账号：无头像、贡献图（绿格子）不计入 |

- **macOS 默认身份的坑**：git 未配置身份时会自动生成 `用户名 <用户名@主机名.local>`（macOS 默认值）——公开仓库的作者栏会显示这个；且邮箱不绑定账号 → 绿格子不计。修正两步：`git config --global user.name / user.email` → `git commit --amend --reset-author --no-edit`
- **为什么用 noreply**：公开仓库的提交邮箱人人可读（`git log --format=%ae` 一行命令），爬虫专抓——noreply 是"能关联账号 + 不暴露真实邮箱"的两全方案。地址在 GitHub Settings → Emails 直接复制（格式 `{ID}+{用户名}@users.noreply.github.com`，ID 是随机的，别自己拼）
- **amend 的副作用认知**：hash 变（9f5da5a → f6b68c5）、时间戳更新为 amend 时刻——对未推送的单条首次提交无害；但 push 之后就不该再改写历史，**身份修正必须排在第一次 push 之前**

### GitHub 远程：不在本日范围，但把坑先记下

- **时机决策**：完成标志只要求本地；定 Day 14 整理 `docs/` 后再建远程，首次 push 即完整成果
- **建仓第一坑**：新建仓库时**不要勾任何初始化选项**（README / .gitignore / license）——勾了远程凭空多一个 commit、比本地新，push 直接被拒，还得先处理远程那份提交。本地已有完整内容时，远程建**空仓**
- push 三步（Day 14 用；SSH 需先配 key，HTTPS 首次 push 需 personal access token）：

```bash
git remote add origin git@github.com:用户名/llm_client.git
git push -u origin main      # -u 建立跟踪关系，之后直接 git push
```

### 本节记住五件事

1. **检查闭环六步**：ignore 先行 → add 具体文件 → status → ls-files → commit → log 复核；顺序即安全
2. **ls-files 干净 ≠ ignore 生效**：check-ignore -v 输出命中规则行号——"碰巧没 add"与"规则挡住"要用命令区分
3. **name 是显示文本，email 是关联键**：绿格子计不计入只看 email 是否在账号绑定列表；noreply 邮箱防爬虫
4. **改写历史有时间窗**：amend / reset-author 只在 push 前安全——身份修正永远排在第一次 push 之前
5. **远程建仓建空仓**：勾了初始化选项 = 远程凭空领先 = push 被拒

---

## 验收节：完成标志自测（Step 5）

> 原始作答：`self_test_step5` · 2026-09-02 review：4 题通过（含精度打磨）、自测点 5 一处实质修正、自测点 1 补终结论 · 完整演练由 Step 3 新人视角验证链 + Step 4 git 复核代证

### 完成标志对照：本地仓库建立，有规范的首次提交 ✅

`git init` 于 `projects/llm_client`（分支 main）→ 首次提交 `feat: LLMClient 项目初始版本——多轮对话、历史持久化、错误重试、token 统计、命令行界面`（9 文件 611 行）→ 作者身份修正为 GitHub noreply → review 三查全过（入库清单 / ignore 规则生效 / 提交内容无 Key）。演练证据：Step 3 的新人视角五步验证链（clone 模拟 → 新 venv → 缺配置 → dummy 配置 → 原项目回归）+ Step 4 的 `git log` / `git ls-files` / `check-ignore` 复核。阶段 0 验收清单"Git 仓库建立并有首次提交"一项随之达成。

### 自测记录（5/5 答出，一处修正）

1. **.gitignore 时机** -- 通过，补终结论
   - 原始作答：`.gitignore` 只管未跟踪文件、提交记录中仍存在 Key 信息 ✓
   - 补（review）：`git rm --cached` 只是停止跟踪，历史提交里那份还在；已 push 则"有没有人看过"不可证明。**终结论：Key 一旦进过提交就应视为已泄露，唯一可靠补救是作废重发（rotate）**
2. **文件职责 + 守卫前提** -- 通过（两处措辞精度）
   - 十件套职责全对；守卫解释准确：Day 11 是脚本没人 import，进包后是包成员天然可被 import——前提变，结论变
   - 精化：`requirements.txt` 是"**重建环境的配方**"（环境本身不入库，归错类就会以为该提交 venv）；`tests/` 是"**回归防线**"（8/8 红暴露文件搬家就是它的价值现场）
3. **重构的行为证明** -- 通过
   - "客观存在的成功 vs 主观认为的成功"框架 ✓
   - 补证明力边界：测试只证明**覆盖到的行为**没变（8 用例 = 8 个行为契约）——覆盖面即证明力，这正是 Day 11 把实验沉淀为 pytest 用例的意义
4. **README / docs 分工** -- 通过
   - 精化：分界的轴是**产品视角**（是什么、怎么用）vs **过程视角**（为什么、怎么来的）；`docs/` 不只服务作者的知识积累，也服务想深入理解设计取舍的读者
5. **history.json 归类** -- 修正后通过
   - 前半段成立：运行时产物、可重现、非必要入库
   - **修正："即使入库也无影响"不成立**——它是个人对话内容（测试夹具里就有姓名、年龄、住址），公开仓库即个人信息暴露。与 `.env` 在六分类里**同属隐私数据**，差别在严重度与补救路径：Key 泄露**有补救动作**（作废重发，立即止损）；对话泄露**无补救动作**（内容不可撤回）但伤害量级小——同性质、不同量级、不同补救

### Day 12 收官

从 day11 的三件散装脚本到规范仓库：拆分重构（类 / 界面 / 测试三层职责分离）→ README 面向无上下文读者 → 启动前校验补齐系统边界 → git init + 规范首提。沉淀两条主线：**检查点做在决定之前**（.gitignore 先行、启动前校验、新人视角五步验证、add 前先 status）与**证明交给可重复的机制**（回归测试、check-ignore、git ls-files，而非"我觉得没问题"）。伏笔移交：pyproject + `pip install -e .`（消 IDE 红线的终态方案）→ 阶段 2；GitHub 远程建仓 + 学习笔记整理进 `docs/` → Day 14。
