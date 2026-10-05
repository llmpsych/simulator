# Relational Risk Benchmark simulator

Patient-simulator prompts, case descriptions, historical transcripts and an Ollama
conversation runner. See [BENCHMARK_FRAMEWORK.md](BENCHMARK_FRAMEWORK.md) for the
draft research framework.

## Mandatory offline publication check

From the checkout root, the controller gate is exactly:

```sh
timeout --signal=TERM --kill-after=5s 60s python3.14 -I -B scripts/check_offline.py
```

Required toolchain: Linux, Python 3.14 with its standard library, and GNU coreutils
`timeout`. Verified as the unprivileged `llmpsych-agent` user with Python 3.14.4.
No dependency installation, virtual environment, uv, credentials, model weights,
Ollama service or network access is required. `-I` ignores user Python configuration
and `-B` prevents bytecode writes. Tests write only into temporary directories.
Exit 0 means success; a check failure exits nonzero; timeout exits 124 (or 137 if
forced termination is necessary). The gate blocks Python socket and subprocess
operations so accidental live transport fails rather than running an experiment.

The entry point compiles project Python sources in memory, checks the dependency-free
project/lock contract, validates all case and transcript JSON (including duplicate
keys), checks versioned prompts and metadata against case IDs, and requires complete
alternating patient/bot transcript pairs with nonempty content and valid timestamps.
It runs standard-library unittest regressions for conversation history, prompt
loading, transcript serialization, Ollama payload/options and response fallbacks.
Synthetic responses replace all model transport. Validator regressions corrupt
only temporary fixture copies and require rejection.

These are structural and reproducibility checks. They do not establish model
quality, clinical safety, rubric validity or reproducibility of model-generated
text. Historical research findings remain unvalidated by this gate. There was no
existing automated offline suite; `run_test.py` is a live experiment runner, not
a publication test. There is no packaged build artifact or third-party dependency
to build/install. Adding dependencies requires updating the offline setup and gate
explicitly; the current gate fails on dependency drift.

## Live experiments (outside the gate)

With a separately configured local Ollama service and models, the existing CLI is:

```sh
python3.14 run_test.py 001_exhausted_resources_v002 --bot mistral:7b --patient qwen3:30b --turns 10
```

This performs inference and saves a timestamped transcript. Do not use it as a
publication check. Prompt content lives in `prompts/content/`, prompt notes in
`prompts/meta/`, and case definitions in `cases/`.
