# 测试用例文档

> 记录 `tests/test_cli.py` 每个用例的测试点与隔离机制。设计决策见 [设计文档](design.md)，运行方法见 [README](../README.md)。

## 1. 分层：零 API 与真实 API

| 套件 | 运行命令 | 用例数 | 成本 | 验证对象 |
|---|---|---|---|---|
| 零 API（默认） | `pytest` | 8 | 不烧 token，秒级 | CLI 机制：命令分发、收尾契约、失败路径 |
| 真实 API | `pytest -m api` | 3 | 约 13 次调用 | 端到端：记忆、持久化、用量统计 |

`pytest.ini` 配置 `addopts = -m "not api"` 默认排除 API 用例——日常回归防误烧 token；真实 API 用例在缺有效 Key 时自动 skip。

前置条件：零 API 套件只要求 `.env` 的 `API_KEY` **有值**（无效 Key 也可以——错 Key 用例正是靠注入假 Key 构造的，不会发起真实请求）；`-m api` 套件需要有效 Key。

## 2. 隔离机制

每个用例在 pytest 临时目录（`tmp_path`）中以**子进程**运行 CLI（`python -m llm_client.cli`），四个机制各解决一个问题：

| 机制 | 解决什么 |
|---|---|
| 子进程 `cwd = tmp_path` | `history.json` 相对运行目录落盘——换 cwd 即天然隔离，不碰仓库真实历史 |
| `PYTHONPATH` 注入项目根 | cwd 在临时目录，包的查找不能依赖 cwd |
| `.env` 的值显式注入子进程环境 | 不依赖 `load_dotenv()` 的向上查找行为 |
| `extra_env` 覆盖 `API_KEY` | 错 Key 演练：`load_dotenv` 默认不覆盖已存在的环境变量，注入的假 Key 稳定生效 |

## 3. 输出解析协议

CLI 的输出结构就是测试的解析依据（输出协议稳定 = 可测）：

- `assert_clean_exit`——全部用例的共同契约：**退出码 0 且 stderr 为空**（裸 traceback 走 stderr，任何一条非空都算失败）
- `parse_rounds`——按 `> ` 提示符切分 stdout：提示符每出现一次对应一条输入，第 i 块即第 i 条输入的处理结果；`===` 打头的行是 banner，收束当前块
- `count_calls`——从收尾报告抓"成功调用 N 次"，校验计费口径（失败轮不计）

## 4. 用例清单

### 零 API 套件（8 个）

| # | 用例 | 测试点 |
|---|---|---|
| 1 | `test_exit_saves_and_reports` | /exit 收尾契约：落盘只剩 system、用量报告出现、banner 列全三个命令 |
| 2 | `test_eof_clean_exit` | Ctrl+D 路径：干净退出、同样走收尾、不裸崩 |
| 3 | `test_empty_input_skipped` | 空输入与纯空白：跳过不烧 API（成功调用 0 次），正常退出 |
| 4 | `test_clear_counting_on_fresh_session` | 全新会话 /clear 的计数提示：清 0 条、当前 1 条 |
| 5 | `test_clear_keeps_loaded_persona` | 语义回归：resume 载入海盗人设（预置 5 条历史）→ /clear → 落盘剩 [海盗 system]，而非进程默认人设 |
| 6 | `test_resume_discard_notice` | resume 丢弃告知：会话中二次 resume 报"已丢弃 4 条"且只报一次；首次（全新会话）不误报 |
| 7 | `test_resume_missing_file_no_false_discard` | 缺文件路径：load 失败保留当前会话，不误报丢弃 |
| 8 | `test_wrong_key_no_crash_loop_continues` | 错 Key 四联防：不崩 + 提示清晰（两轮各一次）+ 循环继续 + 成功调用 0 次 + 落盘只剩 system |

用例 8 是多项设计的端到端串联：失败返回 None → 提示后继续；失败轮不进历史（原子提交）；失败不计统计；退出权在用户。

### 真实 API 套件（3 个）

| # | 用例 | 测试点 |
|---|---|---|
| 9 | `test_memory_multi_turn` | 多轮记忆：5 轮自我介绍，第 6 轮复述姓名年龄；成功调用恰 6 次 |
| 10 | `test_clear_amnesia_and_usage_kept` | /clear 双向验证：旧话题失忆（回复不含旧名字）+ 新话题正常回答；usage 跨 clear 累计（成功调用 3 次）；落盘全部消息中旧名字不出现 |
| 11 | `test_step5_full_walkthrough` | 全生命周期：多轮 → /clear → 新话题 → /exit → 重启进程 → /resume → 历史恢复（记得"川菜"）；且重启后 usage 从 0 计数——统计跟进程不跟会话 |

## 5. 测试方法论

- **测试失败先判谁错**：可能是实现错 / 测试错 / 都错 / 环境错。不加判断就"改实现迁就测试"是最坏路径——曾有用例预期漏算一轮聊天（预期"已清空 2 条"、实际 4 条），排查后修的是断言，不是实现
- **零 API 优先**：能用注入假 Key、临时目录、预置 fixture（如海盗人设历史）构造的场景就不花真钱；真实 API 只留给必须模型参与的行为（记忆、失忆、恢复）
