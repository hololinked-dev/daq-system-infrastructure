#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import tomllib
from enum import StrEnum
from pathlib import Path

from pydantic import ValidationError

from cli.certs import DEFAULT_CA_CN, OpenSSLUnavailable, generate_certificates
from cli.models import AppConfig, MQTTSettings, MQTTUser
from cli.output import (
    build_dotenv_variables,
    update_dbeaver_config,
    write_alembic_dotenv,
    write_dotenv_file,
    write_mqtt_password_file,
)
from cli.passwords import (
    DEFAULT_MQTT_ITERATIONS,
    DEFAULT_MQTT_SALT_BYTES,
    generate_mqtt_password,
)

CONFIG_DEFAULT_PATH = Path("config.toml")
DOTENV_DEFAULT_PATH = Path(".env")
ALEMBIC_DOTENV_DEFAULT_PATH = Path(f"db-migrations{os.sep}.env")
CERTS_DEFAULT_BASE = Path("certs")
MQTT_PASSWORD_FILE_DEFAULT = Path("conf/passwords.txt")


class Args(argparse.Namespace):
    """Namespace of the CLI arguments after parsing"""

    # top level
    config: Path
    command: str
    output: Path | None
    adapt_dbeaver: bool
    # mqtt
    mqtt_command: str | None
    mqtt_usernames: list[str] | None
    mqtt_passwords: list[str] | None
    iterations: int
    salt_bytes: int
    overwrite: bool
    # certs
    base: Path
    service: str
    ca_name: str
    mqtt_dns: list[str]
    http_dns: list[str]
    client: list[str]


class Commands(StrEnum):
    """Available CLI commands"""

    DOTENV = "dotenv"
    MQTT = "mqtt"
    MQTT_GENERATE_PASSWORD = "generate-password"
    ALEMBIC = "alembic-env"
    CERTS = "certs"


def add_dotenv_commands(subparsers: argparse._SubParsersAction) -> None:
    """adds dotenv file generation commands"""
    dotenv_parser = subparsers.add_parser(
        Commands.DOTENV,
        help="Generate .env file from config",
    )  # type: argparse.ArgumentParser

    dotenv_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DOTENV_DEFAULT_PATH,
        help="Output dotenv path (default: .env)",
    )
    dotenv_parser.add_argument(
        "--adapt-dbeaver",
        action="store_true",
        help="Adapt DBeaver initial data sources",
    )


def add_alembic_commands(subparsers: argparse._SubParsersAction) -> None:
    """adds alembic related commands"""
    alembic_parser = subparsers.add_parser(
        Commands.ALEMBIC,
        help="Generate .env for alembic migrations for hololinked database",
    )  # type: argparse.ArgumentParser

    alembic_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=ALEMBIC_DOTENV_DEFAULT_PATH,
        help=f"Output dotenv path (default: {ALEMBIC_DOTENV_DEFAULT_PATH})",
    )


def add_mqtt_commands(subparsers: argparse._SubParsersAction) -> None:
    """adds MQTT related commands"""

    mqtt_parser = subparsers.add_parser(
        Commands.MQTT,
        help="Generate mosquitto MQTT config, like password files",
    )  # type: argparse.ArgumentParser
    mqtt_subparsers = mqtt_parser.add_subparsers(dest="mqtt_command", required=False)

    mqtt_password_parser = mqtt_subparsers.add_parser(
        Commands.MQTT_GENERATE_PASSWORD,
        help="Generate MQTT password file (default command for 'mqtt')",
    )  # type: argparse.ArgumentParser

    mqtt_password_parser.add_argument(
        "--usernames",
        type=str,
        help="Username for MQTT user (comma separated values when multiple given)",
        action="append",
        dest="mqtt_usernames",
    )
    mqtt_password_parser.add_argument(
        "--passwords",
        type=str,
        help="Password for MQTT user (comma separated values when multiple given, order must match --usernames)",
        action="append",
        dest="mqtt_passwords",
    )
    mqtt_password_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Password file path (default: mqtt.password_file or conf/passwords.txt)",
    )
    mqtt_password_parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_MQTT_ITERATIONS,
        help="PBKDF2 iterations (default: 101)",
    )
    mqtt_password_parser.add_argument(
        "--salt-bytes",
        type=int,
        default=DEFAULT_MQTT_SALT_BYTES,
        help="Salt length in bytes (default: 12)",
    )
    mqtt_password_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing password file instead of appending",
    )


def add_certs_commands(subparsers: argparse._SubParsersAction) -> None:
    """adds certificate generation commands"""
    certs_parser = subparsers.add_parser(
        Commands.CERTS,
        help="Generate self-signed MQTT and HTTP certificates",
    )  # type: argparse.ArgumentParser

    certs_parser.add_argument(
        "--base",
        "-b",
        type=Path,
        default=CERTS_DEFAULT_BASE,
        help="Base directory for certificates (default: certs)",
    )
    certs_parser.add_argument(
        "--service",
        "-s",
        choices=["mqtt", "http", "both"],
        default="both",
        help="Which services to generate certificates for",
    )
    certs_parser.add_argument(
        "--ca-name",
        type=str,
        default=DEFAULT_CA_CN,
        help="Common Name for the certificate authority",
    )
    certs_parser.add_argument(
        "--mqtt-dns",
        action="append",
        default=[],
        help="DNS names to include in MQTT server certificate (can be repeated)",
    )
    certs_parser.add_argument(
        "--http-dns",
        action="append",
        default=[],
        help="DNS names to include in HTTP server certificate (can be repeated)",
    )
    certs_parser.add_argument(
        "--client",
        action="append",
        default=[],
        help="Generate client certificate for this name (can be repeated)",
    )


def load_config(path: str) -> AppConfig:
    """Load TOML config from the given path and validate it against the `AppConfig` model."""
    try:
        with open(path, "rb") as fh:
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


def merge_config_with_input_arguments(config: AppConfig, args: Args) -> AppConfig:
    """Merge the loaded config with input arguments, e.g. for MQTT user credentials."""
    if args.mqtt_command != Commands.MQTT_GENERATE_PASSWORD:
        return config
    if args.mqtt_usernames and args.mqtt_passwords:
        if len(args.mqtt_usernames) != len(args.mqtt_passwords):
            print("ERROR: The number of --usernames and --passwords must match", file=sys.stderr)
            raise SystemExit(2)
        users = [MQTTUser(username=u, password=p) for u, p in zip(args.mqtt_usernames, args.mqtt_passwords)]
        mqtt_settings = config.mqtt or MQTTSettings(password_file=MQTT_PASSWORD_FILE_DEFAULT, users=users)
        mqtt_settings.users = users
        config.mqtt = mqtt_settings
    elif args.mqtt_usernames or args.mqtt_passwords:
        print("ERROR: Both --usernames and --passwords must be provided together", file=sys.stderr)
        raise SystemExit(2)
    return config


def parser() -> argparse.ArgumentParser:
    """Create and return the argument parser for the CLI."""
    parser = argparse.ArgumentParser(prog="ctl", description="IoT infrastructure utility CLI")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=CONFIG_DEFAULT_PATH,
        help="Path to TOML config (default: config.toml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_dotenv_commands(subparsers)
    add_mqtt_commands(subparsers)
    add_alembic_commands(subparsers)
    add_certs_commands(subparsers)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv, namespace=Args())  # type: Args

    for attr in Args.__annotations__:
        if not hasattr(args, attr):
            setattr(args, attr, None)

    if args.command == Commands.CERTS:
        services = {"mqtt", "http"} if args.service == "both" else {args.service}
        try:
            generate_certificates(
                base_dir=args.base,
                services=services,
                ca_common_name=args.ca_name,
                mqtt_dns=args.mqtt_dns,
                http_dns=args.http_dns,
                client_names=args.client,
            )
        except OpenSSLUnavailable as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise SystemExit(1)
        return

    config = load_config(args.config)
    config = merge_config_with_input_arguments(config, args)

    if args.command == Commands.DOTENV:
        env = build_dotenv_variables(config)
        write_dotenv_file(args.output, env)
        if args.adapt_dbeaver:
            update_dbeaver_config(config)
    elif args.command == Commands.MQTT:
        if args.mqtt_command == Commands.MQTT_GENERATE_PASSWORD:
            output = args.output or (config.mqtt.password_file if config.mqtt else MQTT_PASSWORD_FILE_DEFAULT)
            passwords = generate_mqtt_password(config, iterations=args.iterations, salt_bytes=args.salt_bytes)
            write_mqtt_password_file(output, passwords, append=not args.overwrite)
            return
        print(
            f"ERROR: subcommand is required for 'mqtt' (e.g. '{Commands.MQTT_GENERATE_PASSWORD}'); see --help for details",
            file=sys.stderr,
        )
        raise SystemExit(1)
    elif args.command == Commands.ALEMBIC:
        write_alembic_dotenv(config, args.output)
    else:
        print(f"ERROR: Unknown command: {args.command}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
