#!/usr/bin/env bash
# 一键拉起本地代码模型服务（vLLM OpenVINO 后端，OpenAI 兼容端点）
# 纯 localhost，默认端口 8000。环境变量可覆盖：MODEL / PORT / MAX_LEN
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-Coder-3B-Instruct}"
PORT="${PORT:-8000}"
MAX_LEN="${MAX_LEN:-8192}"

cat <<BANNER
╔══════════════════════════════════════════════════╗
║  git-commit-msg · 本地模型服务 (OpenVINO 后端)   ║
╚══════════════════════════════════════════════════╝
模型: $MODEL
端口: $PORT   (OpenAI 兼容: http://localhost:$PORT/v1)
BANNER

# 前置依赖检查：vllm + openvino 后端
if ! python -c "import vllm" 2>/dev/null; then
  cat <<HINT
未检测到 vllm。请先安装 OpenVINO 后端：
    pip install -U "vllm[openvino]"
或改用 Optimum-intel 离线部署（见 references/model_deploy.md 方案 B）。
HINT
  exit 1
fi

exec python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL" \
  --device openvino \
  --port "$PORT" \
  --max-model-len "$MAX_LEN" \
  --trust-remote-code
