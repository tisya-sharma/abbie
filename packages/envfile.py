"""Minimal loader for the repo-root credentials file.

Reads KEY=VALUE lines, skipping comments, blanks, and empty values, and sets
only variables the environment does not already define, so an exported shell
variable always wins. Kept dependency-free on purpose.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# keys.env is preferred because it matches the name datasheet_generator uses,
# and .env is still read so existing checkouts keep working. Both are gitignored.
CANDIDATE_PATHS = (REPO_ROOT / "keys.env", REPO_ROOT / ".env")

ENV_PATH = CANDIDATE_PATHS[0]


def load_env_file(path: Path | None = None) -> None:
    """Apply KEY=VALUE pairs from a local env file without overriding the shell."""
    if path is None:
        path = next((candidate for candidate in CANDIDATE_PATHS if candidate.exists()), None)
        if path is None:
            return
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
