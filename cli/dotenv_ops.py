from __future__ import annotations

import json
import sys
from pathlib import Path

from .config_models import AppConfig

DEFAULT_DB_HOST = "host.docker.internal"
DEFAULT_DB_PORT = 5432


def build_dotenv_variables(config: AppConfig) -> dict[str, str]:
    env: dict[str, str] = {
        "POSTGRES_ADMIN": config.postgres.admin_username,
        "POSTGRES_ADMIN_PASSWORD": config.postgres.admin_password,
        "POSTGRES_LISTEN_ADDRESSES": config.postgres.listen_addresses,
        "POSTGRES_MAX_CONNECTIONS": str(config.postgres.max_connections),
        "POSTGRES_MAX_WORKER_PROCESSES": str(config.postgres.max_worker_processes),
        "POSTGRES_MAX_PARALLEL_WORKERS": str(config.postgres.max_parallel_workers),
        "POSTGRES_MAX_PARALLEL_WORKERS_PER_GATHER": str(config.postgres.max_parallel_workers_per_gather),
        "POSTGRES_SHARED_BUFFERS": config.postgres.shared_buffers,
        "POSTGRES_EFFECTIVE_CACHE_SIZE": config.postgres.effective_cache_size,
        "POSTGRES_MAINTENANCE_WORK_MEM": config.postgres.maintenance_work_mem,
        "POSTGRES_INITDB_ARGS": config.postgres.initdb_args,
        "KEYCLOAK_ADMIN": config.keycloak.admin_username,
        "KEYCLOAK_ADMIN_PASSWORD": config.keycloak.admin_password,
        "KEYCLOAK_DB_USERNAME": config.database.keycloak.username if config.database.keycloak else "",
        "KEYCLOAK_DB_PASSWORD": config.database.keycloak.password if config.database.keycloak else "",
        "KEYCLOAK_DB_NAME": config.database.keycloak.name if config.database.keycloak else "",
        "DBEAVER_ADMIN_USERNAME": config.dbeaver.admin_username,
        "DBEAVER_ADMIN_PASSWORD": config.dbeaver.admin_password,
    }

    if config.database.keycloak or config.database.hololinked:
        db_entries = list(config.database.iter_databases())
        env["POSTGRES_DATABASES"] = ",".join(db.name for db in db_entries)
        env["POSTGRES_DATABASE_USERNAMES"] = ",".join(db.username for db in db_entries)
        env["POSTGRES_DATABASE_PASSWORDS"] = ",".join(db.password for db in db_entries)

    if config.mongodb:
        env["MONGO_ADMIN"] = config.mongodb.admin_username
        env["MONGO_ADMIN_PASSWORD"] = config.mongodb.admin_password
        if config.mongodb.express:
            env["MONGOEXPRESS_ADMIN"] = config.mongodb.express.admin_username
            env["MONGOEXPRESS_ADMIN_PASSWORD"] = config.mongodb.express.admin_password

    return env


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
