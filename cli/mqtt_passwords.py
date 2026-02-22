from __future__ import annotations

import base64
import hashlib
import secrets
import sys
from pathlib import Path

from .config_models import AppConfig


def generate_mqtt_hash(password: str, iterations: int, salt_bytes: int) -> str:
    salt = secrets.token_bytes(salt_bytes)
    digest = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"$7${iterations}${salt_b64}${digest_b64}"


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
