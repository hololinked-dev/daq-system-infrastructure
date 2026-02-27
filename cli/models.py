from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Database(BaseModel):
    """
    Representation of a general database and its credentials,
    to be finally used for creating/connecting to any database.
    """

    name: str
    """name of the database to create/use"""
    username: str
    """username for the database"""
    password: str
    """password for the database"""

    model_config = ConfigDict(extra="ignore")


class PostgresSettings(BaseModel):
    """PostgreSQL runtime settings"""

    admin_username: str
    """admin username"""
    admin_password: str
    """admin password"""
    listen_addresses: str | list[str] = "*"
    """machine listen addresses (default: *, meaning exposed on all interfaces)"""
    max_connections: int = 100
    """max client connections (default: 100)"""
    max_worker_processes: int = 2
    """max worker processes (default: 2)"""
    max_parallel_workers: int = 2
    """max parallel workers (default: 2)"""
    max_parallel_workers_per_gather: int = 1
    """max parallel workers per gather (default: 1) """
    shared_buffers: str = "128MB"
    """shared buffer size (default: 128MB)"""

    effective_cache_size: str = "256MB"
    """effective cache size (default: 256MB)"""
    maintenance_work_mem: str = "64MB"
    """maintenance work memory (default: 64MB)"""
    initdb_args: str = Field(
        default="--auth-host=scram-sha-256 --auth-local=scram-sha-256",
        validation_alias=AliasChoices("initdb_args", "init_db_args"),
    )
    """additional arguments to initdb (default: --auth-host=scram-sha-256 --auth-local=scram-sha-256)"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        env["POSTGRES_ADMIN"] = self.admin_username
        env["POSTGRES_ADMIN_PASSWORD"] = self.admin_password
        env["POSTGRES_LISTEN_ADDRESSES"] = (
            self.listen_addresses if isinstance(self.listen_addresses, str) else ",".join(self.listen_addresses)
        )
        env["POSTGRES_MAX_CONNECTIONS"] = str(self.max_connections)
        env["POSTGRES_MAX_WORKER_PROCESSES"] = str(self.max_worker_processes)
        env["POSTGRES_MAX_PARALLEL_WORKERS"] = str(self.max_parallel_workers)
        env["POSTGRES_MAX_PARALLEL_WORKERS_PER_GATHER"] = str(self.max_parallel_workers_per_gather)
        env["POSTGRES_SHARED_BUFFERS"] = self.shared_buffers
        env["POSTGRES_EFFECTIVE_CACHE_SIZE"] = self.effective_cache_size
        env["POSTGRES_MAINTENANCE_WORK_MEM"] = self.maintenance_work_mem
        env["POSTGRES_INITDB_ARGS"] = self.initdb_args


class DBeaverSettings(BaseModel):
    """DBeaver settings"""

    admin_username: str
    """admin username"""
    admin_password: str
    """admin password"""
    config_path: Path = Path("conf/dbeaver-initial-data-sources.conf")
    """path to DBeaver initial data sources config (default: conf/dbeaver-initial-data-sources.conf)"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        env["DBEAVER_ADMIN_USERNAME"] = self.admin_username
        env["DBEAVER_ADMIN_PASSWORD"] = self.admin_password


class KeycloakSettings(BaseModel):
    """Keycloak settings"""

    database_engine: str = "postgres"
    """database engine for Keycloak (default: postgres)"""
    admin_username: str
    """admin username"""
    admin_password: str
    """admin password"""
    database: Database
    """Database block"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        env["KEYCLOAK_ADMIN"] = self.admin_username
        env["KEYCLOAK_ADMIN_PASSWORD"] = self.admin_password
        env["KEYCLOAK_DB_USERNAME"] = self.database.username if self.database else ""
        env["KEYCLOAK_DB_PASSWORD"] = self.database.password if self.database else ""
        env["KEYCLOAK_DB_NAME"] = self.database.name if self.database else ""

        if not self.database:
            return

        if not env.get("POSTGRES_DATABASES", None):
            env["POSTGRES_DATABASES"] = self.database.name
            env["POSTGRES_DATABASE_USERNAMES"] = self.database.username
            env["POSTGRES_DATABASE_PASSWORDS"] = self.database.password
        else:
            env["POSTGRES_DATABASES"] += f",{self.database.name}"
            env["POSTGRES_DATABASE_USERNAMES"] += f",{self.database.username}"
            env["POSTGRES_DATABASE_PASSWORDS"] += f",{self.database.password}"


class MongoExpressSettings(BaseModel):
    """MongoExpress settings"""

    admin_username: str
    """admin username"""
    admin_password: str
    """admin password"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        env["MONGOEXPRESS_ADMIN"] = self.admin_username
        env["MONGOEXPRESS_ADMIN_PASSWORD"] = self.admin_password


class MongoSettings(BaseModel):
    """MongoDB settings"""

    admin_username: str
    """admin username"""
    admin_password: str
    """admin password"""
    express: MongoExpressSettings | None = None

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        env["MONGO_ADMIN"] = self.admin_username
        env["MONGO_ADMIN_PASSWORD"] = self.admin_password
        if self.express:
            self.express.update_dotenv(env)


class HololinkedSettings(BaseModel):
    """package settings"""

    database: Database
    """database block"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        if not env.get("POSTGRES_DATABASES", None):
            env["POSTGRES_DATABASES"] = self.database.name
            env["POSTGRES_DATABASE_USERNAMES"] = self.database.username
            env["POSTGRES_DATABASE_PASSWORDS"] = self.database.password
        else:
            env["POSTGRES_DATABASES"] += f",{self.database.name}"
            env["POSTGRES_DATABASE_USERNAMES"] += f",{self.database.username}"
            env["POSTGRES_DATABASE_PASSWORDS"] += f",{self.database.password}"


class MQTTSettings(BaseModel):
    password_file: Path

    model_config = ConfigDict(extra="ignore")


class AppConfig(BaseModel):
    """Representation of the config loaded from the TOML file"""

    postgres: PostgresSettings | None = None
    """PostgreSQL settings block"""
    dbeaver: DBeaverSettings | None = None
    """DBeaver settings block"""
    keycloak: KeycloakSettings | None = None
    """Keycloak settings block"""
    mongodb: MongoSettings | None = None
    """MongoDB settings block"""
    mqtt: MQTTSettings | None = None
    """MQTT settings block"""
    hololinked: HololinkedSettings | None = None
    """Hololinked settings block"""

    model_config = ConfigDict(extra="ignore")

    def update_dotenv(self, env: dict[str, str]) -> None:
        if self.postgres:
            self.postgres.update_dotenv(env)
        if self.dbeaver:
            self.dbeaver.update_dotenv(env)
        if self.keycloak:
            self.keycloak.update_dotenv(env)
        if self.mongodb:
            self.mongodb.update_dotenv(env)
        # if self.mqtt:
        #     self.mqtt.update_dotenv(env)
        if self.hololinked:
            self.hololinked.update_dotenv(env)

    def iter_databases(self) -> Iterable[Database]:
        if self.keycloak and self.keycloak.database:
            yield self.keycloak.database
        if self.hololinked and self.hololinked.database:
            yield self.hololinked.database
