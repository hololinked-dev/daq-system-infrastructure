from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

from pydantic import ValidationError

from .config_models import AppConfig
from .mqtt_passwords import generate_mqtt_hash

DEFAULT_DB_HOST = "host.docker.internal"
DEFAULT_DB_PORT = 5432


def build_dotenv_variables(config: AppConfig) -> dict[str, str]:
    env: dict[str, str] = dict()
    config.update_dotenv(env)
    return env


def load_config(path: Path) -> AppConfig:
    try:
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    except tomllib.TOMLDecodeError as exc:
        print(f"ERROR: Could not parse TOML at {path}: {exc}", file=sys.stderr)
        raise SystemExit(1)

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        print("ERROR: Configuration validation failed:", file=sys.stderr)
        for err in exc.errors():
            loc = ".".join(str(part) for part in err["loc"])
            print(f" - {loc}: {err['msg']}", file=sys.stderr)
        raise SystemExit(2)
    except ValueError as exc:
        print(f"ERROR: Configuration validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2)


def write_env_file(path: Path, env: dict[str, str]) -> None:
    ordered = {k: env[k] for k in sorted(env)}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for key, value in ordered.items():
            fh.write(f"{key}={value}\n")
    print(f"INFO: Wrote {len(ordered)} entries to {path}")


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
    for db in config.database.iter_databases():
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


def write_mqtt_password_file(config: AppConfig, output: Path, iterations: int, salt_bytes: int) -> None:
    if not config.mqtt:
        print("ERROR: mqtt section is missing in the config; cannot generate password file", file=sys.stderr)
        raise SystemExit(2)

    if iterations < 1:
        print("ERROR: iterations must be a positive integer", file=sys.stderr)
        raise SystemExit(2)
    if salt_bytes < 1:
        print("ERROR: salt-bytes must be a positive integer", file=sys.stderr)
        raise SystemExit(2)

    lines = []
    for user in config.mqtt.users:
        hashed = generate_mqtt_hash(user.password, iterations, salt_bytes)
        lines.append(f"{user.username}:{hashed}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"INFO: Wrote {len(lines)} MQTT credentials to {output}")


def write_alembic_dotenv(config: AppConfig, output: Path) -> None:
    hololinked = config.database.hololinked
    if not hololinked:
        print("ERROR: database.hololinked section is required to build alembic dotenv", file=sys.stderr)
        raise SystemExit(2)

    env = {
        "HOLOLINKED_DB_NAME": hololinked.name,
        "HOLOLINKED_DB_USERNAME": hololinked.username,
        "HOLOLINKED_DB_PASSWORD": hololinked.password,
    }
    write_env_file(output, env)
