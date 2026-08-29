# Pre-run gate note

The first execution request on 2026-08-29 made zero model calls and created no response file. It
stopped because the original free-memory gate allowed only 512 MiB of baseline device use, while
WSL and the NVIDIA driver reserved about 1.4 GiB on GPU 1. Ollama reported no resident model,
utilisation was 0–1%, and both the compute-app query and `nvidia-smi pmon` reported no process.

Before any item exposure, the runner was amended and republished to fail on any reported compute
process, any resident Ollama model, utilisation above 5%, or more than 2 GiB of baseline device
memory. The model roster, prompts, answer keys, request parameters, retry policy, and analysis code
did not change. Git history retains the initially published gate and this prospective repair.
