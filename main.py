#!/usr/bin/env python3
"""
0x14-ai-therapist: Relational Risk Benchmark for AI therapy chatbots.

Available scripts:
  uv run benchmark/run_test.py <prompt_id> [--bot MODEL] [--patient MODEL] [--turns N]

Example:
  uv run benchmark/run_test.py 001_exhausted_resources_v002 --bot mistral:7b --turns 10

See benchmark/prompts/content/ for available prompt IDs.
See benchmark/cases/ for case documentation.
"""


def main():
    print(__doc__)


if __name__ == "__main__":
    main()
