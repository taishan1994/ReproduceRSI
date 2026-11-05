#!/usr/bin/env bash
set -euo pipefail
export VLLM_HUMMING_INPUT_QUANT_CONFIG='{"dtype":"float8e4m3"}'
export VLLM_USE_RUST_FRONTEND=1
exec vllm serve /mnt/md0/checkpoints/deepseek-ai/DeepSeek-V4-Flash-0731 \
  --host 127.0.0.1 --port 18173 --served-model-name repro-dsv4-tp4 \
  --trust-remote-code --kv-cache-dtype fp8 --block-size 256 \
  --tensor-parallel-size 4 --pipeline-parallel-size 1 \
  --tokenizer-mode deepseek_v4 --no-enable-prefix-caching \
  --moe-backend humming --gpu-memory-utilization 0.90
