from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from pydantic import ValidationError

from .config_models import AppConfig


def load_config(path: Path) -> AppConfig:
    try:
        with path.open("rb") as fh:
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
