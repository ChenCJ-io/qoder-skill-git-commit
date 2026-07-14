#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_commit.py — Git Commit 自动生成主脚本

读取当前仓库的代码改动，调用本地（localhost）部署的代码模型，
生成符合 Conventional Commits 规范的提交信息。

设计要点：
- 纯本地推理：只请求 http://localhost:8000，绝不调用云端 API。
- staged 优先：先读 `git diff --staged`，暂存区为空则回退 `git diff` 并提示。
- 可注入 diff：核心函数 generate_from_diff(diff_text) 供 eval 复用，不绑定真实仓库。
- 规范校验：对模型输出做 Conventional Commits 格式兜底校验。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import URLError

# ---------- 配置 ----------
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENDPOINT = "http://localhost:8000/v1/chat/completions"
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
PROMPT_TEMPLATE = (ROOT / "assets" / "prompt_template.txt").read_text(encoding="utf-8")
MAX_DIFF_CHARS = 12000  # 单次送入模型的 diff 上限，超出截断
VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert",
}
# 匹配 Conventional Commits 头：type(scope)?: 描述
COMMIT_HEADER_RE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?!?:\s*.+")


def health_check(endpoint: str = DEFAULT_ENDPOINT, timeout: float = 2.0) -> bool:
    """检查本地模型服务是否在运行。"""
    base = endpoint.replace("/v1/chat/completions", "/v1/models")
    try:
        with urlrequest.urlopen(base, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def _run_git(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"git 命令失败：{e.stderr.strip() or e}")


def get_git_diff(repo: str = ".") -> tuple[str, str]:
    """
    读取仓库改动。返回 (diff_text, source)。
    source 为 "staged" 或 "unstaged"。两者皆空时退出。
    """
    staged = _run_git(["git", "-C", repo, "diff", "--staged"])
    if staged.strip():
        return staged, "staged"
    unstaged = _run_git(["git", "-C", repo, "diff"])
    if unstaged.strip():
        return unstaged, "unstaged"
    raise SystemExit("没有可生成 commit 的改动：暂存区与工作区均为空。请先 git add 或修改文件。")


def call_local_model(diff_text: str, *, endpoint: str = DEFAULT_ENDPOINT,
                     model: str = DEFAULT_MODEL, max_chars: int = MAX_DIFF_CHARS) -> str:
    """调用本地 OpenAI 兼容接口，返回模型生成的 commit message。"""
    truncated = diff_text[:max_chars]
    if len(diff_text) > max_chars:
        truncated += f"\n\n[注：diff 超过 {max_chars} 字符已截断，请基于已显示部分总结]"
    prompt = PROMPT_TEMPLATE.replace("{diff}", truncated)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        raise SystemExit(
            f"本地模型服务调用失败（{endpoint}）：{e}\n"
            "请先运行 bash scripts/start_model_server.sh"
        )
    return body["choices"][0]["message"]["content"].strip()


def parse_message(raw: str) -> dict:
    """从模型输出中解析 type/scope/header，做 Conventional Commits 兜底。"""
    lines = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
    header = lines[0] if lines else raw.strip()
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""

    m = COMMIT_HEADER_RE.match(header)
    if not m or m.group("type") not in VALID_TYPES:
        # 兜底：无法识别为规范格式时，默认归 chore 并保留原文语义
        return {"valid": False, "header": f"chore: {header.lstrip('-* ').lower()}", "body": body}
    return {
        "valid": True,
        "type": m.group("type"),
        "scope": m.group("scope"),
        "header": header,
        "body": body,
    }


def generate_from_diff(diff_text: str, *, endpoint: str = DEFAULT_ENDPOINT,
                       model: str = DEFAULT_MODEL, max_chars: int = MAX_DIFF_CHARS) -> dict:
    """核心：给定 diff 文本，生成结构化 commit 信息（CLI 与 eval 共用）。"""
    raw = call_local_model(diff_text, endpoint=endpoint, model=model, max_chars=max_chars)
    return parse_message(raw)


def do_commit(message: str, repo: str = ".") -> None:
    """用生成的 message 执行 git commit。"""
    result = subprocess.run(
        ["git", "-C", repo, "commit", "-m", message],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise SystemExit(f"git commit 失败：{result.stderr.strip()}")
    print(result.stdout.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="生成本地化、规范化的 Git 提交信息")
    ap.add_argument("--repo", default=".", help="目标 git 仓库路径")
    ap.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="本地模型服务端点")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="本地模型名")
    ap.add_argument("--max-diff-chars", type=int, default=MAX_DIFF_CHARS, help="送入模型的 diff 上限")
    ap.add_argument("--commit", action="store_true", help="生成后直接 git commit（默认仅预览）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出（供 eval）")
    args = ap.parse_args()

    if not health_check(args.endpoint):
        raise SystemExit(
            f"本地模型服务未就绪（{args.endpoint}）。\n"
            "请先启动：bash scripts/start_model_server.sh\n"
            "部署细节见 references/model_deploy.md"
        )

    diff_text, source = get_git_diff(args.repo)
    result = generate_from_diff(
        diff_text, endpoint=args.endpoint, model=args.model, max_chars=args.max_diff_chars
    )

    if source == "unstaged":
        print("⚠️ 暂存区为空，已用工作区 diff 生成。建议先 git add 再提交。\n", file=sys.stderr)

    message = result["header"] + (f"\n\n{result['body']}" if result["body"] else "")

    if args.json:
        print(json.dumps({**result, "source": source, "message": message}, ensure_ascii=False, indent=2))
        return 0

    print("生成的提交信息：")
    print("-" * 40)
    print(message)
    print("-" * 40)
    if not result["valid"]:
        print("（⚠️ 未严格匹配 Conventional Commits，已兜底为 chore，请人工复核）", file=sys.stderr)

    if args.commit:
        do_commit(message, repo=args.repo)
    else:
        print("\n预览模式（加 --commit 可直接提交）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
