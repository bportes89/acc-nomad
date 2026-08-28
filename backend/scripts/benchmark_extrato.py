#!/usr/bin/env python3
"""Benchmark de extrato — uso: python scripts/benchmark_extrato.py caminho.pdf"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acc_nomad.golive_check import run_golive_check


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python scripts/benchmark_extrato.py <extrato.pdf> [--local-only]")
        sys.exit(1)

    pdf = sys.argv[1]
    skip_llm = "--local-only" in sys.argv
    report = run_golive_check(pdf, skip_llm=skip_llm)
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    main()
