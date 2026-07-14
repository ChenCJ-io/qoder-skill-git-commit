# 本地模型部署指南

本 Skill 的推理**必须纯本地（localhost）**，禁止云端 API。下面两种方式均基于 OpenVINO，满足比赛「OpenVINO / Optimum-intel」要求。

## 模型选型

| 模型 | 参数 | int4 量化大小 | 适用 |
|------|------|--------------|------|
| Qwen2.5-Coder-3B-Instruct | 3B | ~2GB | NPU 友好，git commit 场景足够（**首选**） |
| Qwen2.5-Coder-7B-Instruct | 7B | ~4–5GB | 效果更好，需 GPU 或较强 NPU |

下载（魔搭，国内快）：
```bash
pip install modelscope
modelscope download --model Qwen/Qwen2.5-Coder-3B-Instruct --local_dir ./models/qwen-coder-3b
```

## 方案 A：vLLM OpenVINO 后端（推荐，一条命令起 OpenAI 兼容端点）

`scripts/start_model_server.sh` 用的就是这套。Skill 脚本零改动接入。

```bash
pip install -U "vllm[openvino]"
bash scripts/start_model_server.sh
# 等价于：
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-Coder-3B-Instruct \
  --device openvino --port 8000 --max-model-len 8192
```

验证：
```bash
curl http://localhost:8000/v1/models
```

## 方案 B：Optimum-intel 转 IR + int4 量化（更贴比赛「Optimum-intel」字眼，适合写进技术文章）

```bash
pip install "optimum[openvino]" nncf

# 1. 转 OpenVINO IR + int4 量化
optimum-cli export openvino \
  --model Qwen/Qwen2.5-Coder-3B-Instruct \
  --weight-format int4 \
  ./openvino_ir/qwen-coder-3b-int4

# 2. 用 openvino-genai 暴露 OpenAI 兼容端点（localhost:8000）
#    参考 openvino.genai 的 llm_chat_chat_sample 或自包 FastAPI
```

> 方案 B 需要自行把推理包成 `localhost:8000/v1/chat/completions`（OpenAI 兼容），这样 Skill 脚本与方案 A 完全一致。

## 硬件目标

- **Intel Core Ultra**（CPU + GPU + NPU 异构），比赛主题即 AI PC
- NPU 运行需装 NPU 驱动；vLLM/OpenVINO 通过 `--device` 切换 `CPU/GPU/NPU`
- 性能预期：3B int4 在 NPU 上首 token 通常 <1s，commit 生成体验流畅

## 故障排查

| 现象 | 处理 |
|------|------|
| `connection refused` | 服务未起，先 `bash scripts/start_model_server.sh` |
| OOM | 换 3B / 降 `--max-model-len` |
| NPU 不可用 | 回退 `--device GPU` 或 `--device CPU` |
| 模型下载慢 | 用魔搭 `modelscope download`，不走 HF |
