---
name: git-commit-msg
description: 读取当前 Git 仓库的暂存改动（staged diff；暂存区为空时回退到工作区 diff），调用本地部署的代码模型，生成符合 Conventional Commits 规范的提交信息（type/scope/简述 + 可选正文）。当用户说"帮我提交""写个 commit""生成 commit message""这改动怎么描述""commit 一下"，或在查看 git diff 后想生成提交说明时使用。即使用户没明确说出"commit"，只要意图是给代码改动写提交信息，都应触发本技能。
---

# Git Commit 自动生成

把"写 commit"这件高频小事自动化：读 diff → 本地代码模型理解改动 → 输出规范的 Conventional Commits message。
**全程数据不出本机**（模型与推理均在 localhost），适合隐私敏感 / 离线开发场景。

## 何时使用
- 改完代码想提交，需要一条规范的 commit message
- 用户说"帮我提交 / 写个 commit / 这改动怎么写提交信息 / commit 一下"
- 查看 `git diff` 后想生成提交说明

## 前置条件（首次使用需确认）
本地代码模型服务需在 `http://localhost:8000` 运行（OpenAI 兼容接口）。
- 部署方式见 `references/model_deploy.md`
- 一键拉起：`bash scripts/start_model_server.sh`
- 健康检查：`curl http://localhost:8000/v1/models`

## 工作流
1. **取改动**：调用 `scripts/generate_commit.py`。脚本优先读 `git diff --staged`；暂存区为空则回退到 `git diff`，并在输出中提示用户先 `git add`。
2. **本地推理**：脚本把 diff 套入 `assets/prompt_template.txt`，POST 到 `localhost:8000/v1/chat/completions`。
3. **规范输出**：模型按 `references/commit_convention.md` 输出 `type(scope): 简述` + 可选正文；脚本做格式兜底校验。
4. **确认 / 提交**：默认 `--dry-run` 只打印 message；用户确认后加 `--commit` 直接提交。

## 使用示例
```bash
# 预览（默认）
python scripts/generate_commit.py

# 指定仓库路径
python scripts/generate_commit.py --repo /path/to/repo

# 确认后直接提交
python scripts/generate_commit.py --commit

# 结构化输出（供评估脚本）
python scripts/generate_commit.py --json
```

## 约束
- **纯本地**：只调用 `localhost` 模型服务，禁止任何云端 API（隐私与比赛硬约束）。
- **规范优先**：输出必须符合 Conventional Commits，详见 `references/commit_convention.md`。
- **大 diff**：当 diff 超过模型上下文预算（默认 12000 字符）时，脚本截断并在文末提示，避免请求失败。

## 评估
测试用例在 `evals/evals.json`，运行 `python scripts/run_eval.py`。每个用例给定 diff 与期望的 type/scope，用于回归。
