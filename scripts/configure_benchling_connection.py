#!/usr/bin/env python3
"""Configure a local Benchling warehouse connection without storing its password."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPOSITORY_ROOT / "config" / "benchling.local.json"
KEYCHAIN_SERVICE = "org.ipi.abbie.benchling-warehouse"
ALLOWED_SSL_MODES = {"verify-ca", "verify-full"}


def prompt(label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    if value:
        return value
    if default is not None:
        return default
    raise SystemExit(f"{label} is required")


def normalize_host_and_port(host: str, port: str) -> tuple[str, str]:
    candidate = host.removeprefix("jdbc:")
    if "://" in candidate:
        parsed = urlsplit(candidate)
        if not parsed.hostname:
            raise SystemExit("Could not parse the Benchling hostname")
        return parsed.hostname, str(parsed.port or port)

    hostname, separator, possible_port = candidate.rpartition(":")
    if separator and possible_port.isdigit():
        return hostname, possible_port
    return candidate, port


def main() -> None:
    host = prompt("Benchling hostname")
    port = prompt("Port", "5432")
    host, port = normalize_host_and_port(host, port)
    database = prompt("Database name", "warehouse")
    username = prompt("Username")
    sslmode = prompt("SSL mode", "verify-ca")
    if sslmode not in ALLOWED_SSL_MODES:
        raise SystemExit("SSL mode must be verify-ca or verify-full")

    default_certificate = REPOSITORY_ROOT / "config" / "aws-rds-global-bundle.pem"
    default_certificate_value = (
        str(default_certificate) if default_certificate.is_file() else ""
    )
    root_certificate = input(
        "Absolute CA certificate path "
        f"[{default_certificate_value}]: "
    ).strip() or default_certificate_value
    if root_certificate:
        certificate_path = Path(root_certificate).expanduser().resolve()
        if not certificate_path.is_file():
            raise SystemExit(f"CA certificate not found: {certificate_path}")
        root_certificate = str(certificate_path)

    keychain_account = f"{username}@{host}:{port}/{database}"
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "sslmode": sslmode,
        "sslrootcert": root_certificate,
        "keychain_service": KEYCHAIN_SERVICE,
        "keychain_account": keychain_account,
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    os.chmod(CONFIG_PATH, 0o600)

    print("\nmacOS Keychain will now prompt for the Benchling password.")
    completed = subprocess.run(
        [
            "security",
            "add-generic-password",
            "-U",
            "-a",
            keychain_account,
            "-s",
            KEYCHAIN_SERVICE,
            "-l",
            "Abbie Benchling warehouse",
            "-w",
        ],
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "Keychain storage failed. The local metadata file was created, "
            "but no password was saved."
        )

    print(f"\nSaved non-secret connection metadata to {CONFIG_PATH}")
    print("Saved the password in macOS Keychain; it was not written to the repository.")


if __name__ == "__main__":
    main()
