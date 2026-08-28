# Existing-reader benchmark results

Status: **complete**

This is project-operated internal benchmark evidence over already-installed local model artifacts.
Cold means prompt-cold; model training exposure is unknown. The one-exposure track includes a
task-local Ainglish definition. Tracks are not pooled, and no call-level independence is claimed.

## Completeness

- Observations: 2904 / 2904
- Unique readers observed: 22 / 22

## Primary paired comparison: Ainglish minus careful English

| Reader | Track | Pairs | Difference | Ainglish only | Careful only | Both | Neither |
|---|---:|---:|---:|---:|---:|---:|---:|
| `ollama/command-r7b:latest@sha256:ff4e9696ef9f19b62e3f7d7261c95dcc9bb15a7c0398493366d851119fe2e1ef` | cold | 22 | -0.136364 | 1 | 4 | 9 | 8 |
| `ollama/command-r7b:latest@sha256:ff4e9696ef9f19b62e3f7d7261c95dcc9bb15a7c0398493366d851119fe2e1ef` | one_exposure | 22 | 0.0 | 3 | 3 | 10 | 6 |
| `ollama/deepseek-v2:16b@sha256:7c8c332f2df7ac4d657f3514d757d969b84ac6d3fec5b0c02bc8491bd0dc5ea1` | cold | 22 | 0.0 | 0 | 0 | 0 | 22 |
| `ollama/deepseek-v2:16b@sha256:7c8c332f2df7ac4d657f3514d757d969b84ac6d3fec5b0c02bc8491bd0dc5ea1` | one_exposure | 22 | 0.045455 | 1 | 0 | 0 | 21 |
| `ollama/exaone3.5:32b@sha256:f2f69abac3dadd89fb740b06e78a529baf0295d70b7a96b48c6bb9061a7e247b` | cold | 22 | -0.090909 | 0 | 2 | 15 | 5 |
| `ollama/exaone3.5:32b@sha256:f2f69abac3dadd89fb740b06e78a529baf0295d70b7a96b48c6bb9061a7e247b` | one_exposure | 22 | 0.045455 | 2 | 1 | 16 | 3 |
| `ollama/falcon3:10b@sha256:1653ff122acd9292fe21a097c0f08ce419439be595b312d6d6d06ee33df91b88` | cold | 22 | -0.181818 | 0 | 4 | 13 | 5 |
| `ollama/falcon3:10b@sha256:1653ff122acd9292fe21a097c0f08ce419439be595b312d6d6d06ee33df91b88` | one_exposure | 22 | -0.090909 | 0 | 2 | 15 | 5 |
| `ollama/gemma3:12b@sha256:f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | cold | 22 | -0.272727 | 1 | 7 | 7 | 7 |
| `ollama/gemma3:12b@sha256:f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a` | one_exposure | 22 | -0.136364 | 1 | 4 | 10 | 7 |
| `ollama/glm4:9b@sha256:5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44` | cold | 22 | -0.227273 | 0 | 5 | 4 | 13 |
| `ollama/glm4:9b@sha256:5b699761eca535dc55047ad9d2dbf54e3b8697709419ef78a70503ed4bfbcf44` | one_exposure | 22 | -0.136364 | 1 | 4 | 3 | 14 |
| `ollama/granite3.3:8b@sha256:fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7` | cold | 22 | -0.045455 | 0 | 1 | 1 | 20 |
| `ollama/granite3.3:8b@sha256:fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7` | one_exposure | 22 | 0.090909 | 2 | 0 | 2 | 18 |
| `ollama/internlm2:20b@sha256:a864ac8dade269ecd21d030dae5fe14be73bf27b1a6f5582537bbf4fd538ec2e` | cold | 22 | -0.181818 | 1 | 5 | 6 | 10 |
| `ollama/internlm2:20b@sha256:a864ac8dade269ecd21d030dae5fe14be73bf27b1a6f5582537bbf4fd538ec2e` | one_exposure | 22 | -0.181818 | 1 | 5 | 6 | 10 |
| `ollama/lfm2:24b@sha256:d6c816d74887ed480a3afd5baa2dd2a5987ef6b359b8661e80e1e9fb3501650c` | cold | 22 | 0.0 | 2 | 2 | 11 | 7 |
| `ollama/lfm2:24b@sha256:d6c816d74887ed480a3afd5baa2dd2a5987ef6b359b8661e80e1e9fb3501650c` | one_exposure | 22 | 0.0 | 2 | 2 | 11 | 7 |
| `ollama/llama3.1:8b@sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | cold | 22 | 0.0 | 3 | 3 | 8 | 8 |
| `ollama/llama3.1:8b@sha256:46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | one_exposure | 22 | 0.045455 | 2 | 1 | 10 | 9 |
| `ollama/mistral-small3.2:24b-instruct-2506-q4_K_M@sha256:5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b` | cold | 22 | -0.181818 | 0 | 4 | 16 | 2 |
| `ollama/mistral-small3.2:24b-instruct-2506-q4_K_M@sha256:5a408ab55df5c1b5cf46533c368813b30bf9e4d8fc39263bf2a3338cfa3b895b` | one_exposure | 22 | -0.181818 | 1 | 5 | 14 | 2 |
| `ollama/olmo2:13b@sha256:6c279ebc980fb07ca7b49cccf17b5faef6a73082cac4b3d44d2226981de676da` | cold | 22 | -0.045455 | 2 | 3 | 4 | 13 |
| `ollama/olmo2:13b@sha256:6c279ebc980fb07ca7b49cccf17b5faef6a73082cac4b3d44d2226981de676da` | one_exposure | 22 | 0.181818 | 4 | 0 | 7 | 11 |
| `ollama/phi4:14b@sha256:ac896e5b8b34a1f4efa7b14d7520725140d5512484457fab45d2a4ea14c69dba` | cold | 22 | -0.136364 | 1 | 4 | 12 | 5 |
| `ollama/phi4:14b@sha256:ac896e5b8b34a1f4efa7b14d7520725140d5512484457fab45d2a4ea14c69dba` | one_exposure | 22 | -0.090909 | 1 | 3 | 13 | 5 |
| `ollama/qwen2.5:7b@sha256:845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | cold | 22 | 0.045455 | 2 | 1 | 11 | 8 |
| `ollama/qwen2.5:7b@sha256:845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e` | one_exposure | 22 | 0.0 | 1 | 1 | 11 | 9 |
| `ollama/qwen3.5:27b@sha256:7653528ba5cba4dd8e19da24aaddc7f4d0b5ecd93571c0825dfd4137958ec06e` | cold | 22 | -0.272727 | 0 | 6 | 14 | 2 |
| `ollama/qwen3.5:27b@sha256:7653528ba5cba4dd8e19da24aaddc7f4d0b5ecd93571c0825dfd4137958ec06e` | one_exposure | 22 | -0.090909 | 0 | 2 | 18 | 2 |
| `ollama/qwen3.5:35b-a3b@sha256:3460ffeede5453ead027dbd2f821b12ad0aa3de54630971993babdb2165221f7` | cold | 22 | -0.181818 | 0 | 4 | 16 | 2 |
| `ollama/qwen3.5:35b-a3b@sha256:3460ffeede5453ead027dbd2f821b12ad0aa3de54630971993babdb2165221f7` | one_exposure | 22 | 0.0 | 1 | 1 | 19 | 1 |
| `ollama/qwen3.5:9b@sha256:6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | cold | 22 | -0.272727 | 0 | 6 | 4 | 12 |
| `ollama/qwen3.5:9b@sha256:6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | one_exposure | 22 | -0.045455 | 0 | 1 | 9 | 12 |
| `ollama/qwen3.6:27b@sha256:a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e` | cold | 22 | -0.136364 | 1 | 4 | 16 | 1 |
| `ollama/qwen3.6:27b@sha256:a50eda8ed977ab48a12431878896b27ffd5cef552c17af3317d9623b939a7f1e` | one_exposure | 22 | -0.045455 | 1 | 2 | 18 | 1 |
| `ollama/qwen3.6:35b@sha256:07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522` | cold | 22 | -0.181818 | 1 | 5 | 14 | 2 |
| `ollama/qwen3.6:35b@sha256:07d35212591fc27746f0a317c975a6d68754fb38e9053d82e25f06057af28522` | one_exposure | 22 | 0.0 | 2 | 2 | 17 | 1 |
| `ollama/qwen3.8-27b-q4:latest@sha256:2226824d099e20746957039c845a90474c5718cec8e7b0cf28420363afdb6e01` | cold | 22 | -0.318182 | 1 | 8 | 11 | 2 |
| `ollama/qwen3.8-27b-q4:latest@sha256:2226824d099e20746957039c845a90474c5718cec8e7b0cf28420363afdb6e01` | one_exposure | 22 | -0.045455 | 2 | 3 | 16 | 1 |
| `ollama/solar-pro:22b@sha256:9a8c71c441ca6aecf7d9435e5eb91911a5202fecea714634ce95201487534011` | cold | 22 | 0.0 | 0 | 0 | 0 | 22 |
| `ollama/solar-pro:22b@sha256:9a8c71c441ca6aecf7d9435e5eb91911a5202fecea714634ce95201487534011` | one_exposure | 22 | 0.0 | 0 | 0 | 0 | 22 |
| `ollama/yi:34b@sha256:ff94bc7c1b7a4792e2fb6a9e8d1062e205c97180b18cc93c4ec943961bd8ab53` | cold | 22 | -0.181818 | 1 | 5 | 12 | 4 |
| `ollama/yi:34b@sha256:ff94bc7c1b7a4792e2fb6a9e8d1062e205c97180b18cc93c4ec943961bd8ab53` | one_exposure | 22 | -0.136364 | 1 | 4 | 13 | 4 |

A positive difference means more zero-repair successes for Ainglish on the same frozen items;
zero means parity; negative means careful English did better. This table does not establish human
intuitiveness, external adoption, pretraining exposure, or future token efficiency.

## Across-reader descriptive distribution

| Comparison | Track | Readers | Min | Median | Max | Positive | Zero | Negative |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ainglish_minus_careful | cold | 22 | -0.318182 | -0.159091 | 0.045455 | 1 | 4 | 17 |
| ainglish_minus_careful | one_exposure | 22 | -0.181818 | -0.0227275 | 0.181818 | 5 | 6 | 11 |
| ainglish_minus_bare | cold | 22 | -0.090909 | 0.045455 | 0.272727 | 13 | 7 | 2 |
| ainglish_minus_bare | one_exposure | 22 | -0.090909 | 0.181818 | 0.454545 | 19 | 2 | 1 |

These are descriptive distributions of reader-level paired effects, not confidence intervals.
Complete arm metrics, item differences, construct strata, token coverage, and latency coverage are
preserved in `RESULTS.json`; complete raw observations remain in `results/responses.jsonl`.
