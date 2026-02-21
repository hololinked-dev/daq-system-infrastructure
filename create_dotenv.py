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
    # mongodb
    "MONGO_ADMIN": "mongodb.admin_username",
    "MONGO_ADMIN_PASSWORD": "mongodb.admin_password",
    # mongo-express
    "MONGOEXPRESS_ADMIN": "mongodb.express.admin_username",
    "MONGOEXPRESS_ADMIN_PASSWORD": "mongodb.express.admin_password",
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

database_keys = [
    "database.hololinked",
    "database.keycloak",
]

sections = [
    "postgres",
    "keycloak",
    "dbeaver",
    "mongodb",
    "mongo_express",
    "database.hololinked",
    "database.keycloak",
]

config_section_dependencies = {
    "keycloak": ["database.keycloak"],
}


def load_file(path: str) -> dict[str, Any]:
    global cfg
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    print("INFO: Loaded config from", path)


def get_value(path: str, default: Any = None) -> Any:
    global cfg
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


def validate_dependencies() -> None:
    global cfg
    for section, dependencies in config_section_dependencies.items():
        if section not in cfg:
            continue
        for dep in dependencies:
            try:
                get_value(dep)
            except KeyError:
                print(f"ERROR: Missing required configuration '{dep}' for section '{section}'", file=sys.stderr)
                raise SystemExit(2)


def validate_sections() -> None:
    global cfg
    for section in sections:
        if section not in cfg:
            continue
        # Check for username/password or admin_username/admin_password
        section_data = cfg[section]
        has_user_pass = ("username" in section_data and "password" in section_data) or (
            "admin_username" in section_data and "admin_password" in section_data
        )
        if not has_user_pass:
            print(
                f"WARNING: Section '{section}' missing username/password or admin_username/admin_password",
                file=sys.stderr,
            )


def load_variables() -> dict[str, str]:

    exports = {}

    for env_var, toml_path in mapping.items():
        try:
            val = get_value(toml_path)
        except KeyError:
            continue
        exports[env_var] = str(val)

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


def export_dotenv(envs: dict[str, str]) -> None:
    with open(".env", "w") as f:
        for k, v in envs.items():
            f.write(f"{k}={v}\n")
    print("INFO: Exported environment variables to .env file")


def arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export environment variables from config.toml")

    parser.add_argument(
        "--config",
        "-c",
        default=config_path,
        help="Path to config TOML file, default is 'config.toml'",
    )

    parser.add_argument(
        "--export-dotenv",
        action="store_true",
        default=False,
        help="Export environment variables to .env file (default: false)",
    )

    parser.add_argument(
        "--create-mqtt-passwords",
        action="store_true",
        default=False,
        help="Create MQTT password files for mosquitto (default: false)",
    )

    return parser.parse_args()


def main() -> None:
    args = arg_parser()

    if args.export_dotenv:
        print("INFO: Exporting environment variables to .env file")
        load_file(args.config)
        validate_sections()
        validate_dependencies()
        exports = load_variables()
        export_dotenv(exports)


if __name__ == "__main__":
    main()
