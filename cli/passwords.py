from __future__ import annotations

import base64
import hashlib
import secrets
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
