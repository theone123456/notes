#!/usr/bin/env python3
"""笔记一键同步脚本。

扫描 sync_config.json 中配置的源目录，过滤敏感信息后同步到 docs/ 下，
可配合 --deploy 提交推送，触发 GitHub Pages 自动部署。

用法：
    python3 scripts/sync_notes.py             # 仅同步到 docs/
    python3 scripts/sync_notes.py --dry-run   # 预演（不写入，仅报告）
    python3 scripts/sync_notes.py --deploy    # 同步并 git 提交推送
"""

import fnmatch
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONFIG = ROOT / "sync_config.json"

# 目录级排除（含默认值，可在 sync_config.json 每个源里用 exclude_dirs 覆盖）
DEFAULT_EXCLUDE_DIRS = {
    ".git", ".venv", ".idea", ".vscode", "__pycache__",
    ".pytest_cache", "node_modules", "dist", "build", "site",
}

# 文件级排除（glob 通配）
DEFAULT_EXCLUDE_FILES = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.crt",
    "id_rsa*", "*.sqlite*", "*.db", ".DS_Store",
]

# 代码后缀 -> Markdown 代码块语言（命中 include_exts 且在此表中的后缀会转代码页）
CODE_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".sh": "bash",
    ".go": "go",
    ".java": "java",
    ".sql": "sql",
}

# 整串匹配即脱敏的密钥形态
SECRET_PATTERNS = [
    re.compile(r"ark-[A-Za-z0-9\-]{20,}"),           # 火山方舟
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),           # OpenAI 风格
    re.compile(r"AKIA[0-9A-Z]{16}"),                 # AWS AccessKeyId
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),             # GitHub PAT
    re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),    # Slack
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}"),    # Bearer Token
]

# key=value 形式：保留键名，仅脱敏值
KV_PATTERN = re.compile(
    r"((?:api[_-]?key|apikey|secret|password|passwd|token)"
    r"\s*[:=]\s*[\"']?)([A-Za-z0-9_\-.]{16,})",
    re.IGNORECASE,
)

REDACTED = "**已脱敏**"


def redact(text: str) -> tuple[str, int]:
    """返回脱敏后的文本与替换次数。"""
    count = 0
    for pat in SECRET_PATTERNS:
        text, n = pat.subn(REDACTED, text)
        count += n
    text, n = KV_PATTERN.subn(lambda m: m.group(1) + REDACTED, text)
    count += n
    return text, count


def code_to_markdown(rel: Path, content: str) -> str:
    lang = CODE_LANG.get(rel.suffix.lower(), "")
    lines = [
        f"# {rel.name}",
        "",
        f"> 源文件：`{rel.as_posix()}`",
        "",
        f"```{lang}",
        content.rstrip("\n"),
        "```",
        "",
    ]
    return "\n".join(lines)


def sync_source(source: dict, dry_run: bool):
    src = Path(source["path"]).expanduser()
    name = source["name"]
    include_exts = {e.lower() for e in source.get("include_exts", [".md"])}
    exclude_dirs = set(source.get("exclude_dirs", DEFAULT_EXCLUDE_DIRS))
    exclude_files = source.get("exclude_files", DEFAULT_EXCLUDE_FILES)

    if not src.is_dir():
        print(f"[错误] 源目录不存在，跳过：{src}")
        return

    target = DOCS / name
    stats = {"md": 0, "code": 0, "skipped": 0, "redacted_files": {}}

    if not dry_run:
        # 目标目录整体由脚本管理，每次全量重建
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        parts = rel.parts
        # 隐藏目录 / 排除目录
        if any(p.startswith(".") or p in exclude_dirs for p in parts[:-1]):
            continue
        fname = parts[-1]
        # 隐藏文件 / 排除文件（如 .env）
        if fname.startswith(".") or any(
            fnmatch.fnmatch(fname, pat) for pat in exclude_files
        ):
            stats["skipped"] += 1
            print(f"  [跳过·敏感/忽略] {rel.as_posix()}")
            continue
        if path.suffix.lower() not in include_exts:
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            stats["skipped"] += 1
            print(f"  [跳过·非文本] {rel.as_posix()}")
            continue

        content, n = redact(content)
        if n:
            stats["redacted_files"][rel.as_posix()] = n

        out_rel = rel if rel.suffix.lower() == ".md" else rel.with_suffix(".md")
        if out_rel == rel:
            page = content
            stats["md"] += 1
        else:
            page = code_to_markdown(rel, content)
            stats["code"] += 1

        if not dry_run:
            out_path = target / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(page, encoding="utf-8")

    print(f"[{name}] markdown {stats['md']} 篇，代码 {stats['code']} 个，"
          f"跳过 {stats['skipped']} 个文件")
    if stats["redacted_files"]:
        print(f"[{name}] 以下文件内容已脱敏：")
        for f, n in stats["redacted_files"].items():
            print(f"    - {f}（{n} 处）")


def deploy():
    """提交 docs/ 变更并推送，触发 GitHub Pages 部署。"""
    def run(*args):
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True)

    run("git", "add", "docs", "sync_config.json")
    status = run("git", "status", "--porcelain", "docs", "sync_config.json")
    if not status.stdout.strip():
        print("笔记无变更，无需提交。")
        return
    msg = f"docs: 同步笔记 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    r = run("git", "commit", "-m", msg)
    if r.returncode != 0:
        print(f"[错误] 提交失败：{r.stderr.strip()}")
        sys.exit(1)
    print(f"已提交：{msg}")
    r = run("git", "push")
    if r.returncode != 0:
        print(f"[提示] 推送失败（可能尚未配置远程仓库）：{r.stderr.strip()}")
    else:
        print("已推送，GitHub Actions 将自动部署。")


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    do_deploy = "--deploy" in args

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    for source in config["sources"]:
        sync_source(source, dry_run)

    if dry_run:
        print("（预演模式，未写入任何文件）")
    else:
        print(f"同步完成 -> {DOCS}")
    if do_deploy and not dry_run:
        deploy()


if __name__ == "__main__":
    main()
