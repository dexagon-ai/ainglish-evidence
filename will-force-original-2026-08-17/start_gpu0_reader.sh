#!/usr/bin/env bash
set -euo pipefail

# Dedicated, loopback-only experiment server. CUDA_VISIBLE_DEVICES exposes only
# physical GPU 0; model and request concurrency remain one, so the experiment
# cannot spill across cards or evict itself between cells.
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_CONTEXT_LENGTH=4096

exec ollama serve
