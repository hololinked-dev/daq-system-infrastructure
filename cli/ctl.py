#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .certs import DEFAULT_CA_CN, OpenSSLUnavailable, generate_certificates
from .config_models import DEFAULT_MQTT_ITERATIONS, DEFAULT_MQTT_SALT_BYTES, MQTT_PASSWORD_FILE_DEFAULT
from .file_ops import (
    build_dotenv_variables,
    load_config,
    update_dbeaver_config,
    write_alembic_dotenv,
    write_env_file,
    write_mqtt_password_file,
)

CONFIG_DEFAULT_PATH = Path("config.toml")
DOTENV_DEFAULT_PATH = Path(".env")
ALEMBIC_DOTENV_DEFAULT_PATH = Path(f"db-migrations{os.sep}.env")
CERTS_DEFAULT_BASE = Path("certs")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctl", description="Infrastructure utility CLI")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=CONFIG_DEFAULT_PATH,
        help="Path to TOML config (default: config.toml)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    dotenv_parser = subparsers.add_parser("dotenv", help="Generate .env file from config")
    dotenv_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=DOTENV_DEFAULT_PATH,
        help="Output dotenv path (default: .env)",
    )
    dotenv_parser.add_argument(
        "--skip-dbeaver",
        action="store_true",
        help="Skip updating DBeaver initial data sources",
    )

    mqtt_parser = subparsers.add_parser("mqtt-passwords", help="Generate mosquitto password file from config")
    mqtt_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Password file path (default: mqtt.password_file or conf/passwords.txt)",
    )
    mqtt_parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_MQTT_ITERATIONS,
        help="PBKDF2 iterations (default: 101)",
    )
    mqtt_parser.add_argument(
        "--salt-bytes",
        type=int,
        default=DEFAULT_MQTT_SALT_BYTES,
        help="Salt length in bytes (default: 12)",
    )

    alembic_parser = subparsers.add_parser("alembic-env", help="Generate .env for Alembic using hololinked database")
    alembic_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=ALEMBIC_DOTENV_DEFAULT_PATH,
        help=f"Output dotenv path (default: {ALEMBIC_DOTENV_DEFAULT_PATH})",
    )

    certs_parser = subparsers.add_parser("certs", help="Generate self-signed MQTT and HTTP certificates")
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

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if args.command == "certs":
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

    if args.command == "dotenv":
        env = build_dotenv_variables(config)
        write_env_file(args.output, env)
        if not args.skip_dbeaver:
            update_dbeaver_config(config)
    elif args.command == "mqtt-passwords":
        output = args.output or (config.mqtt.password_file if config.mqtt else MQTT_PASSWORD_FILE_DEFAULT)
        write_mqtt_password_file(config, output, iterations=args.iterations, salt_bytes=args.salt_bytes)
    elif args.command == "alembic-env":
        write_alembic_dotenv(config, args.output)
    else:
        print(f"ERROR: Unknown command: {args.command}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
