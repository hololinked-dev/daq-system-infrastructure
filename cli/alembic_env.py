from __future__ import annotations

import sys
from pathlib import Path

from .config_models import AppConfig
from .dotenv_ops import write_env_file


def write_alembic_dotenv(config: AppConfig, output: Path) -> None:
    hololinked = config.database.hololinked
    if not hololinked:
        print("ERROR: database.hololinked section is required to build alembic dotenv", file=sys.stderr)
        raise SystemExit(2)

    env = {
        "HOLOLINKED_DB_NAME": hololinked.name,
        "HOLOLINKED_DB_USERNAME": hololinked.username,
        "HOLOLINKED_DB_PASSWORD": hololinked.password,
    }
    write_env_file(output, env)
