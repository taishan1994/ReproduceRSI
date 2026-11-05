#!/usr/bin/env bash
set -euo pipefail
export VLLM_HUMMING_INPUT_QUANT_CONFIG='{"dtype":"float8e4m3"}'
export VLLM_USE_RUST_FRONTEND=1
export VLLM_USE_V2_MODEL_RUNNER=1
export VLLM_SKIP_V2_DECODE_WARMUP=1
exec vllm serve /mnt/md0/checkpoints/deepseek-ai/DeepSeek-V4-Flash-0731 \
  --host 127.0.0.1 --port 18174 --served-model-name repro-dsv4-tp2pp2-v2patched-mnbt2048 \
  --trust-remote-code --kv-cache-dtype fp8 --block-size 256 \
  --tensor-parallel-size 2 --pipeline-parallel-size 2 \
  --tokenizer-mode deepseek_v4 --no-enable-prefix-caching \
  --moe-backend humming --gpu-memory-utilization 0.90 \
  --max-num-seqs 32 --max-num-batched-tokens 2048 \
  --cudagraph-capture-sizes 1 2 4 8 16 \
  --disable-custom-all-reduce
