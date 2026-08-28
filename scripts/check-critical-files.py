#!/usr/bin/env python3
"""Bloqueia commit que esvazia arquivos críticos."""

from __future__ import annotations

import subprocess
import sys

GUARDED = (
    "backend/requirements.txt",
    "backend/src/acc_nomad/services/llm_providers.py",
    "backend/src/acc_nomad/main.py",
    "backend/src/acc_nomad/pipeline.py",
)


def staged_content(path: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def main() -> int:
    diff = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [p.strip() for p in diff.stdout.splitlines() if p.strip()]
    errors: list[str] = []

    for path in changed:
        if path not in GUARDED:
            continue
        content = staged_content(path)
        if content is not None and content.strip() == "":
            errors.append(f"{path} está vazio no commit — abortado.")

    if errors:
        print("pre-commit: arquivos críticos não podem ser apagados:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
