# test_cli.py

> 源文件：`projects/llm_client/tests/test_cli.py`

```python
"""llm_client.cli 自动化测试

分层：
    零 API 套件（默认运行，不烧 token）——CLI 机制验证
        pytest
    真实 API 套件（烧 token，全套约 13 次调用）
        pytest -m api

设计要点：
    - 每个用例在 pytest 临时目录（tmp_path）里以子进程运行 CLI
      （python -m llm_client.cli），history.json 相对运行目录落盘
      -> 天然隔离，不碰仓库真实历史
    - 包的查找路径靠 PYTHONPATH 注入项目根（cwd 是临时目录，不能靠它找到包）
    - .env 的真实 Key 显式注入子进程环境（不依赖 load_dotenv 的查找行为）；
      错 Key 演练靠 env 覆盖——load_dotenv 默认不覆盖已存在的环境变量
    - 输出解析：CLI 的 "> " 提示符每出现一次对应一条输入，
      第 i 块 = 第 i 条输入的处理结果（parse_rounds）
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from dotenv import dotenv_values

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
ENV_FILE = PROJECT_ROOT / ".env"

# 显式读 .env：只取值，不改本进程环境
_DOTENV = {k: v for k, v in dotenv_values(ENV_FILE).items() if v}
API_READY = bool(_DOTENV.get("API_KEY"))

PIRATE_FIXTURE = [
    {"role": "system", "content": "测试人设：你是一个海盗，所有回答都用海盗口音"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "啊哈，水手！有什么可以帮你的？"},
    {"role": "user", "content": "今天天气如何"},
    {"role": "assistant", "content": "暴风雨要来了，抓紧桅杆！"},
]

NAME, AGE = "小测", "28"


# ---------- 工具 ----------

def run_cli(inputs, cwd, extra_env=None, timeout=120):
    """管道方式运行 CLI（python -m llm_client.cli）：inputs 逐行喂给 stdin。

    -m 以包方式启动，包的查找路径靠 PYTHONPATH 指向项目根
    （cwd 是临时目录，不能靠它找到包）；cwd 保持调用方传入的临时目录，
    history.json 相对运行目录落盘，天然隔离。
    """
    env = {**os.environ, **_DOTENV}
    # 项目根注入 PYTHONPATH（保留已有值），包结构靠它对子进程可见
    env["PYTHONPATH"] = (
        f"{PROJECT_ROOT}{os.pathsep}{env['PYTHONPATH']}"
        if "PYTHONPATH" in env
        else str(PROJECT_ROOT)
    )
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "llm_client.cli"],
        input="\n".join(inputs) + "\n",
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        timeout=timeout,
    )


def assert_clean_exit(proc):
    """所有退出路径的共同契约：退出码 0、stderr 无输出（裸 traceback 走 stderr）。"""
    assert proc.returncode == 0, f"非零退出码，stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    assert proc.stderr == "", f"stderr 非空（疑似裸 traceback）:\n{proc.stderr}"


def parse_rounds(stdout):
    """按 '> ' 提示符切分输出：第 i 块 = 第 i 条输入的处理结果。

    '>' 打头的行 = 新一轮开始；'===' 打头的行 = banner（启动/报告），收束当前块。
    """
    rounds, current = [], None
    for line in stdout.splitlines():
        if line.startswith("> "):
            if current is not None:
                rounds.append(current)
            current = line[2:]
        elif line.startswith("==="):
            if current is not None:
                rounds.append(current)
                current = None
        elif current is not None:
            current += "\n" + line
    if current is not None:
        rounds.append(current)
    return rounds


def read_history(cwd):
    return json.loads((Path(cwd) / "history.json").read_text(encoding="utf-8"))


def write_fixture(cwd, messages):
    (Path(cwd) / "history.json").write_text(
        json.dumps(messages, ensure_ascii=False, indent=4), encoding="utf-8"
    )


def count_calls(stdout):
    m = re.search(r"成功调用 (\d+) 次", stdout)
    assert m, f"report 中找不到'成功调用 N 次':\n{stdout}"
    return int(m.group(1))


# ---------- 零 API 套件：CLI 机制 ----------

def test_exit_saves_and_reports(tmp_path):
    """exit 收尾契约：save（只剩 system）+ report + banner 列全命令。"""
    proc = run_cli(["/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "命令：/exit 退出 · /clear 清空会话 · /resume 恢复上次会话" in proc.stdout
    assert "会话用量报告" in proc.stdout
    history = read_history(tmp_path)
    assert len(history) == 1 and history[0]["role"] == "system"


def test_eof_clean_exit(tmp_path):
    """Ctrl+D（EOF）路径：干净退出、走收尾、不裸崩。"""
    proc = run_cli([], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "收到 Ctrl+D（输入结束）" in proc.stdout
    assert read_history(tmp_path)[0]["role"] == "system"


def test_empty_input_skipped(tmp_path):
    """空输入与纯空白：跳过不烧 API，正常退出。"""
    proc = run_cli(["", "   ", "/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert count_calls(proc.stdout) == 0
    assert read_history(tmp_path)[0]["role"] == "system"


def test_clear_counting_on_fresh_session(tmp_path):
    """全新会话 /clear：清 0 条、当前 1 条（任务清单"打印确认信息和当前消息数"）。"""
    proc = run_cli(["/clear", "/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "已清空 0 条对话，保留人设（当前 1 条消息）" in proc.stdout


def test_clear_keeps_loaded_persona(tmp_path):
    """语义回归：resume 后 clear 保留载入历史的人设。

    载入海盗人设（5 条）-> /clear -> 落盘应只剩 [海盗 system]，
    而不是进程默认人设——"原始" = 本会话原始，非进程原始。
    """
    write_fixture(tmp_path, PIRATE_FIXTURE)
    proc = run_cli(["/resume", "/clear", "/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "已清空 4 条对话，保留人设（当前 1 条消息）" in proc.stdout
    history = read_history(tmp_path)
    assert len(history) == 1
    assert history[0]["content"] == PIRATE_FIXTURE[0]["content"]


def test_resume_discard_notice(tmp_path):
    """resume 丢弃告知：会话中二次 resume 报丢弃条数；首次（全新会话）不误报。"""
    write_fixture(tmp_path, PIRATE_FIXTURE)
    proc = run_cli(["/resume", "/resume", "/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "已丢弃当前未保存的 4 条对话" in proc.stdout
    assert proc.stdout.count("已丢弃") == 1


def test_resume_missing_file_no_false_discard(tmp_path):
    """缺文件路径：load 失败原样保留当前会话，不误报丢弃。"""
    proc = run_cli(["/resume", "/exit"], cwd=tmp_path)
    assert_clean_exit(proc)
    assert "history.json 不存在，开始新会话" in proc.stdout
    assert "已丢弃" not in proc.stdout


def test_wrong_key_no_crash_loop_continues(tmp_path):
    """错 Key 时 CLI 不崩、提示清晰、循环继续、零计费、失败轮不落盘。

    串联四天结论：Day 9 悬案（None -> 提示后继续）+ Day 8 原子提交（失败不进历史）
    + Day 10 统计（失败不计成功调用）+ Day 11 循环（退出权在用户）。
    """
    proc = run_cli(["你好", "再试一次", "/exit"], cwd=tmp_path, extra_env={"API_KEY": "wrong"})
    assert_clean_exit(proc)
    assert proc.stdout.count("API Key 无效") == 2
    assert proc.stdout.count("调用失败，本轮对话未记录") == 2
    assert count_calls(proc.stdout) == 0
    history = read_history(tmp_path)
    assert len(history) == 1 and history[0]["role"] == "system"


# 运行方式：pytest -m api（烧 token，全套约 13 次调用）

@pytest.mark.api
@pytest.mark.skipif(not API_READY, reason="项目根 .env 缺 API_KEY")
def test_memory_multi_turn(tmp_path):
    """实验 1：连聊 5 轮自我介绍，第 6 轮验证记忆。"""
    inputs = [
        f"我叫{NAME}，今年{AGE}岁",
        "我住在上海",
        "我正在学习 AI Agent 开发",
        "我的爱好是爬山",
        "我养了一只猫叫咪咪",
        "我刚才告诉你我叫什么名字？今年多大？",
        "/exit",
    ]
    proc = run_cli(inputs, cwd=tmp_path, timeout=420)
    assert_clean_exit(proc)
    rounds = parse_rounds(proc.stdout)
    assert NAME in rounds[5] and AGE in rounds[5]
    assert count_calls(proc.stdout) == 6


@pytest.mark.api
@pytest.mark.skipif(not API_READY, reason="项目根 .env 缺 API_KEY")
def test_clear_amnesia_and_usage_kept(tmp_path):
    """实验 2：clear 后旧话题失忆、新话题正常；usage 统计不清零（跨 clear 累计）。"""
    inputs = [
        f"我叫{NAME}，今年{AGE}岁",
        "/clear",
        "我刚才告诉你我叫什么名字？",
        "讲一个 Python 列表的特点",
        "/exit",
    ]
    proc = run_cli(inputs, cwd=tmp_path, timeout=420)
    assert_clean_exit(proc)
    rounds = parse_rounds(proc.stdout)
    assert "已清空 2 条对话，保留人设（当前 1 条消息）" in rounds[1]
    assert NAME not in rounds[2], f"clear 后应失忆，但回复含旧名字:\n{rounds[2]}"
    assert len(rounds[3]) > 0
    assert count_calls(proc.stdout) == 3
    history = read_history(tmp_path)
    assert history[0]["role"] == "system"
    assert all(NAME not in m.get("content", "") for m in history)


@pytest.mark.api
@pytest.mark.skipif(not API_READY, reason="项目根 .env 缺 API_KEY")
def test_step5_full_walkthrough(tmp_path):
    """多轮聊天（记忆）-> /clear -> 新话题 -> /exit -> 重启 -> /resume -> 历史恢复。"""
    session_a = [
        f"我叫{NAME}，今年{AGE}岁",
        "我刚才说我叫什么名字？",
        "/clear",
        "我最近在学做川菜",
        "/exit",
    ]
    proc_a = run_cli(session_a, cwd=tmp_path, timeout=420)
    assert_clean_exit(proc_a)
    rounds_a = parse_rounds(proc_a.stdout)
    assert NAME in rounds_a[1]
    assert "已清空 4 条对话" in rounds_a[2]  # 两轮聊天（报姓名 + 记忆验证）= 4 条非 system 消息
    assert count_calls(proc_a.stdout) == 3

    # 重启进程：usage 跟进程不跟会话——从 0 重新计数
    session_b = ["/resume", "我刚才说我在学做什么菜？", "/exit"]
    proc_b = run_cli(session_b, cwd=tmp_path, timeout=420)
    assert_clean_exit(proc_b)
    rounds_b = parse_rounds(proc_b.stdout)
    assert "history.json 加载成功" in rounds_b[0]
    assert "川菜" in rounds_b[1]
    assert "已丢弃" not in proc_b.stdout
    assert count_calls(proc_b.stdout) == 1
```
