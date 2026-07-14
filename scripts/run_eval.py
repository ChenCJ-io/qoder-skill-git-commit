#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_eval.py — 运行 evals/evals.json，校验生成 commit 的 type/scope 是否符合预期。

依赖：先启动本地模型服务（bash scripts/start_model_server.sh）。
退出码：全部通过 0，否则 1。
"""
import json
import sys
from pathlib import Path

# 复用主脚本的核心函数
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_commit as gc  # noqa: E402

EVALS = Path(__file__).resolve().parent.parent / "evals" / "evals.json"


def main() -> int:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    endpoint = data.get("endpoint", gc.DEFAULT_ENDPOINT)
    model = data.get("model", gc.DEFAULT_MODEL)
    cases = data["cases"]

    # health_check 内部会把 /v1/chat/completions 转成 /v1/models
    if not gc.health_check(endpoint):
        print(f"本地模型服务未就绪（{endpoint}）。请先 bash scripts/start_model_server.sh")
        return 2

    passed = 0
    for i, c in enumerate(cases, 1):
        try:
            res = gc.generate_from_diff(c["diff"], endpoint=endpoint, model=model)
        except Exception as e:  # noqa: BLE001
            print(f"[{i}/{len(cases)}] {c['name']} ✗ 调用失败: {e}")
            continue

        expect = c["expect_type"] + (f"({c['expect_scope']})" if c.get("expect_scope") else "")
        ok_type = res.get("type") == c["expect_type"]
        ok_scope = c.get("expect_scope") is None or res.get("scope") == c.get("expect_scope")
        ok = ok_type and ok_scope and res.get("valid")

        print(f"[{i}/{len(cases)}] {c['name']} {'✓' if ok else '✗'}")
        print(f"    期望: {expect}")
        print(f"    实际: {res.get('header')}")
        if ok:
            passed += 1

    print(f"\n通过 {passed}/{len(cases)}")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
