#!/usr/bin/env python3
import argparse
import json
import sys
import tomllib
from copy import deepcopy
from typing import Any

# globals
cfg = None

config_path = "config.example.toml"

mapping = {
    # postgres
    "POSTGRES_ADMIN": "postgres.admin_username",
    "POSTGRES_ADMIN_PASSWORD": "postgres.admin_password",
    "POSTGRES_LISTEN_ADDRESSES": "postgres.listen_addresses",
    "POSTGRES_MAX_CONNECTIONS": "postgres.max_connections",
    "POSTGRES_MAX_WORKER_PROCESSES": "postgres.max_worker_processes",
    "POSTGRES_MAX_PARALLEL_WORKERS": "postgres.max_parallel_workers",
    "POSTGRES_MAX_PARALLEL_WORKERS_PER_GATHER": "postgres.max_parallel_workers_per_gather",
    "POSTGRES_SHARED_BUFFERS": "postgres.shared_buffers",
    "POSTGRES_EFFECTIVE_CACHE_SIZE": "postgres.effective_cache_size",
    "POSTGRES_MAINTENANCE_WORK_MEM": "postgres.maintenance_work_mem",
    "POSTGRES_INITDB_ARGS": "postgres.initdb_args",
    # keycloak
    "KEYCLOAK_ADMIN": "keycloak.admin_username",
    "KEYCLOAK_ADMIN_PASSWORD": "keycloak.admin_password",
    "KEYCLOAK_DB_USERNAME": "database.keycloak.username",
    "KEYCLOAK_DB_PASSWORD": "database.keycloak.password",
    "KEYCLOAK_DB_NAME": "database.keycloak.name",
    # dbeaver
    "DBEAVER_ADMIN_USERNAME": "dbeaver.admin_username",
    "DBEAVER_ADMIN_PASSWORD": "dbeaver.admin_password",
}

defaults = {
    "postgres.listen_addresses": "*",
    "postgres.max_connections": 100,
    "postgres.max_worker_processes": 2,
    "postgres.max_parallel_workers": 2,
    "postgres.max_parallel_workers_per_gather": 1,
    "postgres.shared_buffers": "128MB",
    "postgres.effective_cache_size": "256MB",
    "postgres.maintenance_work_mem": "64MB",
    "postgres.initdb_args": "--auth-host=scram-sha-256 --auth-local=scram-sha-256",
    "dbeaver.config_path": "conf/dbeaver-initial-data-sources.conf",
    "database.hololinked.name": "hololinked",
    "database.keycloak.name": "keycloak",
    "keycloak.database_engine": "postgres",
}

database_keys = ["database.hololinked", "database.keycloak"]


def load_file(path: str) -> dict[str, Any]:
    global cfg
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    print("INFO: Loaded config from", path)


def get_value(path: str, default: Any = None) -> Any:
    cur = cfg
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            if default is not None:
                return default
            if defaults and path in defaults:
                return defaults[path]
            raise KeyError(path)
        cur = cur[part]
    return cur


def load_variables() -> dict[str, str]:

    missing = []
    exports = {}

    for env_var, toml_path in mapping.items():
        try:
            val = get_value(toml_path)
        except KeyError:
            missing.append(toml_path)
            continue
        if val is None:
            missing.append(toml_path)
            continue
        exports[env_var] = str(val)

    if missing:
        print("ERROR: Missing required keys in TOML:", file=sys.stderr)
        for k in missing:
            print(f"- {k}", file=sys.stderr)
        raise SystemExit(2)

    databases = []
    database_usernames = []
    database_passwords = []

    dbbeaver_conf_path = get_value("dbeaver.config_path", "conf/dbeaver-initial-data-sources.conf")
    dbbeaver_conf = json.loads(open(dbbeaver_conf_path).read())
    print("INFO: Loaded DBeaver config from", dbbeaver_conf_path)

    for db in database_keys:
        try:
            db_name = get_value(f"{db}.name")
            db_user = get_value(f"{db}.username")
            db_pwd = get_value(f"{db}.password")
        except KeyError as ex:
            print(f"WARNING: database configuration for '{db}' inconsistent: keyerror {ex}", file=sys.stderr)
            raise SystemExit(2)
        if not db_name or not db_user or not db_pwd:
            print(f"WARNING: Incomplete database configuration for '{db}', skipping", file=sys.stderr)
            raise SystemExit(2)

        databases.append(db_name)
        database_usernames.append(db_user)
        database_passwords.append(db_pwd)

        for id, db_conf in deepcopy(dbbeaver_conf.get("connections", {})).items():
            if db.split(".")[1] in db_conf.get("name").lower():
                url = f"jdbc:postgresql://host.docker.internal:5432/{db_name}"
                db_conf["configuration"]["user"] = db_user
                db_conf["configuration"]["database"] = db_name
                db_conf["configuration"]["url"] = url
                dbbeaver_conf["connections"][id] = db_conf

                print(f"INFO: Updated DBeaver config for database '{db_name}' with username '{db_user}', url '{url}'")

    with open(dbbeaver_conf_path, "w") as f:
        json.dump(dbbeaver_conf, f, indent=4)
        print("INFO: Saved updated DBeaver config")

    exports["POSTGRES_DATABASES"] = ",".join(databases)
    exports["POSTGRES_DATABASE_USERNAMES"] = ",".join(database_usernames)
    exports["POSTGRES_DATABASE_PASSWORDS"] = ",".join(database_passwords)

    return exports


def shell_quote(s: str) -> str:
    # safe single-quote for bash:  abc'd -> 'abc'"'"'d'
    return "'" + s.replace("'", "'\"'\"'") + "'"


def export_envs_posix(envs: dict[str, str]) -> None:
    for k, v in envs.items():
        cmd = f"export {k}={shell_quote(v)}"
        print(cmd)


def export_envs_windows(envs: dict[str, str]) -> None:
    for k, v in envs.items():
        cmd = f"call set {k}={v}"
        print(cmd)


def arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export environment variables from config.toml")

    parser.add_argument(
        "--config",
        "-c",
        default=config_path,
        help="Path to config TOML file, default is 'config.toml'",
    )

    return parser.parse_args()


def main() -> None:
    args = arg_parser()
    load_file(args.config)
    exports = load_variables()

    if sys.platform.startswith("win"):
        export_envs_windows(exports)
    else:
        export_envs_posix(exports)


if __name__ == "__main__":
    main()
