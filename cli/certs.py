from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

DEFAULT_CERT_DAYS = 825
DEFAULT_KEY_BITS = 4096
DEFAULT_SERVER_KEY_BITS = 2048
DEFAULT_CA_CN = "DAQ Infrastructure CA"
DEFAULT_MQTT_CN = "mqtt.local"
DEFAULT_HTTP_CN = "http.local"


class OpenSSLUnavailable(Exception):
    pass


def _run_openssl(args: list[str], cwd: Path | None = None) -> None:
    try:
        result = subprocess.run(["openssl", *args], cwd=cwd, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise OpenSSLUnavailable("openssl executable not found; install OpenSSL and retry") from exc
    except subprocess.CalledProcessError as exc:
        print(exc.stdout, file=sys.stderr)
        print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())


def _write_req_config(common_name: str, dns_names: Iterable[str]) -> Path:
    alt_names = [name for name in dns_names if name] or [common_name]
    san_lines = [f"DNS.{idx+1} = {name}" for idx, name in enumerate(alt_names)]
    san_block = "\n".join(san_lines)
    cfg = f"""
[ req ]
default_bits = {DEFAULT_SERVER_KEY_BITS}
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[ dn ]
CN = {common_name}

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
{san_block}
"""
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".cnf")
    tmp.write(cfg)
    tmp.flush()
    return Path(tmp.name)


def ensure_ca(base_dir: Path, common_name: str) -> tuple[Path, Path]:
    ca_key = base_dir / "ca.key"
    ca_cert = base_dir / "ca.crt"
    base_dir.mkdir(parents=True, exist_ok=True)

    if ca_key.exists() and ca_cert.exists():
        return ca_key, ca_cert

    print(f"INFO: Generating CA at {base_dir}")
    _run_openssl(
        [
            "req",
            "-x509",
            "-nodes",
            "-newkey",
            f"rsa:{DEFAULT_KEY_BITS}",
            "-days",
            str(DEFAULT_CERT_DAYS),
            "-subj",
            f"/CN={common_name}",
            "-keyout",
            str(ca_key),
            "-out",
            str(ca_cert),
        ]
    )
    return ca_key, ca_cert


def generate_server_cert(
    base_dir: Path,
    ca_key: Path,
    ca_cert: Path,
    common_name: str,
    dns_names: Iterable[str],
    prefix: str,
) -> tuple[Path, Path]:
    service_dir = base_dir
    service_dir.mkdir(parents=True, exist_ok=True)
    key_path = service_dir / f"{prefix}_server.key"
    csr_path = service_dir / f"{prefix}_server.csr"
    crt_path = service_dir / f"{prefix}_server.crt"

    cfg_path = _write_req_config(common_name, dns_names)

    print(f"INFO: Generating {prefix} server key/cert")
    _run_openssl([
        "req",
        "-new",
        "-nodes",
        "-newkey",
        f"rsa:{DEFAULT_SERVER_KEY_BITS}",
        "-keyout",
        str(key_path),
        "-out",
        str(csr_path),
        "-subj",
        f"/CN={common_name}",
        "-config",
        str(cfg_path),
    ])

    _run_openssl([
        "x509",
        "-req",
        "-in",
        str(csr_path),
        "-CA",
        str(ca_cert),
        "-CAkey",
        str(ca_key),
        "-CAcreateserial",
        "-out",
        str(crt_path),
        "-days",
        str(DEFAULT_CERT_DAYS),
        "-sha256",
        "-extensions",
        "v3_req",
        "-extfile",
        str(cfg_path),
    ])

    cfg_path.unlink(missing_ok=True)
    csr_path.unlink(missing_ok=True)
    return key_path, crt_path


def generate_client_cert(
    base_dir: Path,
    ca_key: Path,
    ca_cert: Path,
    client_name: str,
    prefix: str,
) -> tuple[Path, Path]:
    client_dir = base_dir / "clients"
    client_dir.mkdir(parents=True, exist_ok=True)
    key_path = client_dir / f"{prefix}_{client_name}.key"
    csr_path = client_dir / f"{prefix}_{client_name}.csr"
    crt_path = client_dir / f"{prefix}_{client_name}.crt"

    print(f"INFO: Generating {prefix} client certificate for {client_name}")
    _run_openssl([
        "req",
        "-new",
        "-nodes",
        "-newkey",
        f"rsa:{DEFAULT_SERVER_KEY_BITS}",
        "-keyout",
        str(key_path),
        "-out",
        str(csr_path),
        "-subj",
        f"/CN={client_name}",
    ])

    _run_openssl([
        "x509",
        "-req",
        "-in",
        str(csr_path),
        "-CA",
        str(ca_cert),
        "-CAkey",
        str(ca_key),
        "-CAcreateserial",
        "-out",
        str(crt_path),
        "-days",
        str(DEFAULT_CERT_DAYS),
        "-sha256",
    ])

    csr_path.unlink(missing_ok=True)
    return key_path, crt_path


def generate_certificates(
    base_dir: Path,
    services: set[str],
    ca_common_name: str,
    mqtt_dns: list[str],
    http_dns: list[str],
    client_names: list[str],
) -> None:
    ca_key, ca_cert = ensure_ca(base_dir, ca_common_name)

    if "mqtt" in services:
        mqtt_dir = base_dir / "mqtt"
        generate_server_cert(
            mqtt_dir,
            ca_key,
            ca_cert,
            common_name=mqtt_dns[0] if mqtt_dns else DEFAULT_MQTT_CN,
            dns_names=mqtt_dns,
            prefix="mqtt",
        )
        for client in client_names:
            generate_client_cert(mqtt_dir, ca_key, ca_cert, client, prefix="mqtt")

    if "http" in services:
        http_dir = base_dir / "http"
        generate_server_cert(
            http_dir,
            ca_key,
            ca_cert,
            common_name=http_dns[0] if http_dns else DEFAULT_HTTP_CN,
            dns_names=http_dns,
            prefix="http",
        )
        for client in client_names:
            generate_client_cert(http_dir, ca_key, ca_cert, client, prefix="http")

    print("INFO: Certificate generation complete")
