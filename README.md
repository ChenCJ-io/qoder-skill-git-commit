# git-commit-msg — 本地化 Git Commit 自动生成 Skill

面向 [Production AI Skills 大赛](https://modelscope.cn/events/289)（英特尔 × 魔搭）的参赛 Skill。
读取代码 diff → 本地代码模型（OpenVINO 部署）→ 符合 **Conventional Commits** 规范的提交信息。
**全程纯 localhost，数据不出本机**，贴合比赛「端侧生产力 + 隐私不出机」主题。

遵循 Anthropic Agent Skills 协议，可被 **Qoder**、**魔搭 Skills 中心**、**Claude Code** 等任意兼容客户端加载。

## 特性

- 🔒 纯本地推理（Qwen2.5-Coder + OpenVINO / NPU），隐私安全、离线可用
- 🎯 staged 优先，暂存区空时自动回退工作区 diff
- 📐 Conventional Commits 规范输出 + 兜底格式校验
- 🔌 适配 Qoder（`~/.qoder/skills/`）/ 魔搭 Skills 中心 / MS-Agent

## 快速开始

```bash
# 1. 起本地模型服务（vLLM OpenVINO 后端）
pip install -U "vllm[openvino]"
bash scripts/start_model_server.sh

# 2. 在任意 git 仓库生成 commit
python scripts/generate_commit.py            # 预览
python scripts/generate_commit.py --commit   # 确认后直接提交
```

> 部署细节（含 Optimum-intel 量化方案、NPU 配置）见 [`references/model_deploy.md`](references/model_deploy.md)。

## 在 Qoder 中使用

```bash
# 放到 Qoder 用户级技能目录
cp -r . ~/.qoder/skills/git-commit-msg/
```
重启 Qoder，在对话里说「**帮我生成 commit**」即可自动触发（模型按 SKILL.md 的 description 判断）。

## 提交到魔搭 Skills 中心（参赛交付）

1. `modelscope.cn/skills` → **新建 Skill** → 上传本目录打包
2. 打 **「AI PC」** 自定义标签
3. 作品含：代码（`scripts/`）+ 文档（`SKILL.md` / `references/`）+ 测试用例（`evals/`）
4. 配套在魔搭研习社发技术文章（**「Intel AI PC」** 标签）

## 评估

```bash
python scripts/run_eval.py
```

## 目录结构

```
qoder-skill-git-commit/
├── SKILL.md                     # 技能定义（触发描述 + 工作流）
├── scripts/
│   ├── generate_commit.py       # 主逻辑：diff → 本地模型 → commit msg
│   ├── start_model_server.sh    # 一键拉起本地模型服务
│   └── run_eval.py              # 测试用例运行器
├── references/
│   ├── commit_convention.md     # Conventional Commits 规范
│   └── model_deploy.md          # OpenVINO 部署指南
├── assets/prompt_template.txt   # commit 生成 prompt 模板
├── evals/evals.json             # 测试用例
└── README.md · LICENSE · .gitignore
```

## 参赛评分对标

| 维度 | 权重 | 本作品落点 |
|------|------|-----------|
| 场景价值 | 30% | git commit 是开发者每天的高频痛点，用户群体广 |
| 商用生产力 | 30% | 可嵌入真实开发工作流，本地化满足企业隐私合规 |
| 工具使用 | 20% | Qoder 稳定调用 + OpenVINO/NPU 本地推理 |
| 文章质量 | 10% | 部署可复现 + Hybrid AI 思考 |
| 创新性 | 10% | 纯本地 commit 生成 + 隐私差异化 |
| 传播附加 | 5% | 小红书 @OpenVINO中文社区 @魔搭ModelScope社区 |

## License

Apache-2.0（与 Qwen 模型协议一致）。完整文本见 http://www.apache.org/licenses/LICENSE-2.0
