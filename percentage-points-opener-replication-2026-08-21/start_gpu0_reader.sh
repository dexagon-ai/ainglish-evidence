#!/usr/bin/env bash
set -euo pipefail

export CUDA_VISIBLE_DEVICES=0
export OLLAMA_HOST=127.0.0.1:11435
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_CONTEXT_LENGTH=4096
export OLLAMA_MODELS=/home/dexagon/.ollama/models

exec ollama serve
