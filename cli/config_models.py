from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

MQTT_PASSWORD_FILE_DEFAULT = Path("conf/passwords.txt")
DEFAULT_MQTT_ITERATIONS = 101
DEFAULT_MQTT_SALT_BYTES = 12


class DatabaseCredential(BaseModel):
    name: str
    username: str
    password: str

    model_config = ConfigDict(extra="ignore")


class PostgresSettings(BaseModel):
    admin_username: str
    admin_password: str
    listen_addresses: str = "*"
    max_connections: int = 100
    max_worker_processes: int = 2
    max_parallel_workers: int = 2
    max_parallel_workers_per_gather: int = 1
    shared_buffers: str = "128MB"
    effective_cache_size: str = "256MB"
    maintenance_work_mem: str = "64MB"
    initdb_args: str = Field(
        default="--auth-host=scram-sha-256 --auth-local=scram-sha-256",
        validation_alias=AliasChoices("initdb_args", "init_db_args"),
    )

    model_config = ConfigDict(extra="ignore")


class DBeaverSettings(BaseModel):
    admin_username: str
    admin_password: str
    config_path: Path = Path("conf/dbeaver-initial-data-sources.conf")

    model_config = ConfigDict(extra="ignore")


class KeycloakSettings(BaseModel):
    database_engine: str = "postgres"
    admin_username: str
    admin_password: str

    model_config = ConfigDict(extra="ignore")


class MongoExpressSettings(BaseModel):
    admin_username: str
    admin_password: str

    model_config = ConfigDict(extra="ignore")


class MongoSettings(BaseModel):
    admin_username: str
    admin_password: str
    express: MongoExpressSettings | None = None

    model_config = ConfigDict(extra="ignore")


class MQTTUser(BaseModel):
    username: str
    password: str

    model_config = ConfigDict(extra="ignore")


class MQTTSettings(BaseModel):
    users: list[MQTTUser] = Field(default_factory=list)
    password_file: Path = MQTT_PASSWORD_FILE_DEFAULT
    iterations: int = DEFAULT_MQTT_ITERATIONS
    salt_bytes: int = DEFAULT_MQTT_SALT_BYTES

    model_config = ConfigDict(extra="ignore")


class DatabaseBlock(BaseModel):
    hololinked: DatabaseCredential | None = None
    keycloak: DatabaseCredential | None = None

    model_config = ConfigDict(extra="ignore")

    def iter_databases(self) -> Iterable[DatabaseCredential]:
        for item in (self.keycloak, self.hololinked):
            if item:
                yield item


class AppConfig(BaseModel):
    postgres: PostgresSettings
    database: DatabaseBlock
    dbeaver: DBeaverSettings
    keycloak: KeycloakSettings
    mongodb: MongoSettings | None = None
    mqtt: MQTTSettings | None = None

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def _validate_dependencies(self) -> "AppConfig":
        errors: list[str] = []
        if self.keycloak and not self.database.keycloak:
            errors.append("database.keycloak is required when keycloak is configured")
        if not any(self.database.iter_databases()):
            errors.append("at least one database entry (keycloak or hololinked) is required")
        if self.mqtt and not self.mqtt.users:
            errors.append("mqtt.users must not be empty when mqtt section is present")
        if errors:
            raise ValueError("; ".join(errors))
        return self
