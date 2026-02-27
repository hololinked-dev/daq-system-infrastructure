from __future__ import annotations

import base64
import hashlib
import secrets
import sys
from pathlib import Path

MQTT_PASSWORD_FILE_DEFAULT = Path("conf/passwords.txt")
DEFAULT_MQTT_ITERATIONS = 101
DEFAULT_MQTT_SALT_BYTES = 12


def generate_mqtt_hash(password: str, iterations: int, salt_bytes: int) -> str:
    salt = secrets.token_bytes(salt_bytes)
    mosquitto_password_entry = "$7$"
    digest = hashlib.pbkdf2_hmac("sha512", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"{mosquitto_password_entry}{iterations}${salt_b64}${digest_b64}"


def generate_mqtt_password(config, iterations: int, salt_bytes: int) -> list[str]:
    """Generate MQTT password entries for all users in the config using the specified iterations and salt length."""
    from .models import AppConfig

    if not isinstance(config, AppConfig):
        raise TypeError("config must be an instance of AppConfig")

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

    return lines
