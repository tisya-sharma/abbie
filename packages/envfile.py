"""Minimal loader for the repo-root .env file.

Reads KEY=VALUE lines, skipping comments, blanks, and empty values, and sets
only variables the environment does not already define, so an exported shell
variable always wins. Kept dependency-free on purpose.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def load_env_file(path: Path = ENV_PATH) -> None:
    """Apply KEY=VALUE pairs from a local env file without overriding the shell."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value
