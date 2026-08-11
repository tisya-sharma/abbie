#!/usr/bin/env python3
"""Inspect Benchling warehouse schema metadata without reading record values."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit


ALLOWED_SSL_MODES = {"verify-ca", "verify-full"}
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPOSITORY_ROOT / "config" / "benchling.local.json"
OUTPUT_PATH = REPOSITORY_ROOT / "schema-audit" / "warehouse-schema.tsv"


def require_value(name: str, value: str) -> str:
    value = value.strip()
    if not value:
        raise SystemExit(f"Missing required connection setting: {name}")
    return value


def load_config() -> dict[str, str]:
    if CONFIG_PATH.is_file():
        loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {key: str(value) for key, value in loaded.items()}
    return {}


def config_value(config: dict[str, str], key: str, environment_name: str) -> str:
    return os.environ.get(environment_name, config.get(key, ""))


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


def keychain_password(config: dict[str, str]) -> str:
    service = config.get("keychain_service", "")
    account = config.get("keychain_account", "")
    if not service or not account:
        return ""

    completed = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-a",
            account,
            "-s",
            service,
            "-w",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "Benchling password was not found in macOS Keychain. "
            "Run scripts/configure_benchling_connection.py first."
        )
    return completed.stdout.rstrip("\n")


def run_psql(args: list[str], environment: dict[str, str]) -> str:
    psql = shutil.which("psql")
    if psql is None:
        raise SystemExit("psql was not found on PATH")

    completed = subprocess.run(
        [psql, "-X", "-v", "ON_ERROR_STOP=1", "-At", *args],
        check=False,
        env=environment,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        error = completed.stderr.strip() or "psql failed without an error message"
        raise SystemExit(error)
    return completed.stdout


def connection_environment() -> dict[str, str]:
    config = load_config()
    sslmode = config_value(
        config,
        "sslmode",
        "BENCHLING_SSLMODE",
    ).strip() or "verify-ca"
    if sslmode not in ALLOWED_SSL_MODES:
        raise SystemExit(
            "BENCHLING_SSLMODE must be verify-ca or verify-full; "
            "unencrypted or unverified modes are rejected"
        )

    environment = os.environ.copy()
    host = require_value(
        "host",
        config_value(config, "host", "BENCHLING_HOST"),
    )
    port = (
        config_value(config, "port", "BENCHLING_PORT").strip() or "5432"
    )
    host, port = normalize_host_and_port(host, port)
    environment["PGHOST"] = host
    environment["PGPORT"] = port
    environment["PGDATABASE"] = require_value(
        "database",
        config_value(config, "database", "BENCHLING_DATABASE"),
    )
    environment["PGUSER"] = require_value(
        "username",
        config_value(config, "username", "BENCHLING_USER"),
    )
    environment["PGSSLMODE"] = sslmode

    root_certificate = config_value(
        config,
        "sslrootcert",
        "BENCHLING_SSLROOTCERT",
    ).strip()
    if root_certificate:
        environment["PGSSLROOTCERT"] = root_certificate

    password = os.environ.get("BENCHLING_PASSWORD", "") or keychain_password(config)
    if password:
        environment["PGPASSWORD"] = password
    return environment


def assert_read_only(environment: dict[str, str]) -> None:
    read_only_status = run_psql(
        [
            "-c",
            "BEGIN READ ONLY; "
            "SELECT current_setting('transaction_read_only'); "
            "ROLLBACK;",
        ],
        environment,
    )
    if "\non\n" not in f"\n{read_only_status}\n":
        raise SystemExit("The connection did not confirm a read-only transaction")


def main() -> None:
    environment = connection_environment()
    assert_read_only(environment)

    query = """
        SELECT
            table_schema,
            table_name,
            ordinal_position,
            column_name,
            data_type,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY table_schema, table_name, ordinal_position;
    """
    metadata = run_psql(["-F", "\t", "-c", query], environment)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(metadata, encoding="utf-8")
    os.chmod(OUTPUT_PATH, 0o600)

    metadata_rows = sum(1 for line in metadata.splitlines() if line.strip())
    print("Connected using a read-only transaction.")
    print(f"Saved {metadata_rows} schema metadata rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
