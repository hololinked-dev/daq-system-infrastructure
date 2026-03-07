from __future__ import annotations

import json
import sys
from pathlib import Path

from .models import AppConfig

DEFAULT_DB_HOST = "host.docker.internal"
DEFAULT_DB_PORT = 5432


def build_dotenv_variables(config: AppConfig) -> dict[str, str]:
    """Build a dictionary of environment variables from the given config."""
    env: dict[str, str] = dict()
    config.update_dotenv(env)
    return env


def write_dotenv_file(path: Path, env: dict[str, str]) -> None:
    """Write the given environment variables to a .env file at the specified path."""
    ordered = {k: env[k] for k in sorted(env)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in ordered.items():
            fh.write(f"{key}={value}\n")
    print(
        f"INFO: Wrote {len(ordered)} entries to {path}, "
        + "use `docker compose up <module name> -d` to start the services you need"
    )


def write_alembic_dotenv(config: AppConfig, output: Path) -> None:
    if not config.hololinked:
        print("ERROR: database.hololinked section is required to build alembic dotenv", file=sys.stderr)
        raise SystemExit(2)

    env = {
        "HOLOLINKED_DB_NAME": config.hololinked.database.name,
        "HOLOLINKED_DB_USERNAME": config.hololinked.database.username,
        "HOLOLINKED_DB_PASSWORD": config.hololinked.database.password,
    }
    write_dotenv_file(output, env)


def update_dbeaver_config(config: AppConfig) -> None:
    target = config.dbeaver.config_path
    if not target.exists():
        print(f"WARNING: DBeaver config not found at {target}, skipping update", file=sys.stderr)
        return

    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: Failed to parse DBeaver config at {target}: {exc}", file=sys.stderr)
        raise SystemExit(2)

    connections = data.get("connections", {})
    updated = False
    for db in config.iter_databases():
        for conn_id, conn in list(connections.items()):
            name = str(conn.get("name", "")).lower()
            if db.name.lower() not in name:
                continue
            configuration = conn.setdefault("configuration", {})
            url = f"jdbc:postgresql://{DEFAULT_DB_HOST}:{DEFAULT_DB_PORT}/{db.name}"
            configuration.update(
                {
                    "user": db.username,
                    "database": db.name,
                    "url": url,
                }
            )
            connections[conn_id] = conn
            updated = True
            print(f"INFO: Updated DBeaver connection '{conn.get('name', conn_id)}' with user '{db.username}'")

    if updated:
        data["connections"] = connections
        target.write_text(json.dumps(data, indent=4), encoding="utf-8")
        print(f"INFO: Saved DBeaver configuration to {target}")
    else:
        print("INFO: No DBeaver connections matched configured databases; nothing changed")


def write_mqtt_password_file(output: Path, passwords: list[str], append: bool = True) -> None:
    """
    Write given list of MQTT password entries to the given output file.
    Use `append=True` to append to existing file instead of overwriting.
    """
    lines = "\n".join(passwords)
    output.parent.mkdir(parents=True, exist_ok=True)
    if append and output.exists():
        existing = output.read_text(encoding="utf-8").strip()
        if existing:
            lines = f"{existing}\n{lines}"
    output.write_text(f"{lines}\n", encoding="utf-8")
    print(f"INFO: Wrote {len(passwords)} MQTT credentials to {output}")
