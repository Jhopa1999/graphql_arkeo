"""Carga de configuración y credenciales.

Las credenciales NUNCA se leen de variables de entorno en texto plano:
se obtienen de AWS Secrets Manager y se cachean en memoria durante la
vida del contenedor Lambda (reduce latencia y llamadas a Secrets Manager).
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict

import boto3
from botocore.config import Config as BotoConfig

# --- Parámetros técnicos configurables vía variables de entorno ---------------

# Nombre/ARN del secret en Secrets Manager (inyectado por la plantilla SAM).
SECRET_ID = os.environ.get("DB_SECRET_ID", "seven-db-credentials")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-2")

# Tamaño de página por defecto y máximo por página (límite técnico, NO global).
# No se impone un máximo total de registros: se recorre todo vía paginación.
DEFAULT_PAGE_SIZE = int(os.environ.get("DEFAULT_PAGE_SIZE", "100"))
MAX_PAGE_SIZE = int(os.environ.get("MAX_PAGE_SIZE", "1000"))

# Timeouts de conexión/consulta en segundos.
DB_LOGIN_TIMEOUT = int(os.environ.get("DB_LOGIN_TIMEOUT", "10"))
DB_QUERY_TIMEOUT = int(os.environ.get("DB_QUERY_TIMEOUT", "25"))

_boto_config = BotoConfig(
    region_name=AWS_REGION,
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=10,
)


@lru_cache(maxsize=1)
def get_db_credentials() -> Dict[str, Any]:
    """Obtiene y cachea las credenciales de SQL Server desde Secrets Manager.

    Se espera un JSON con las claves: host, port, database, username, password.
    """
    client = boto3.client("secretsmanager", config=_boto_config)
    resp = client.get_secret_value(SecretId=SECRET_ID)
    secret = json.loads(resp["SecretString"])

    required = ("host", "port", "database", "username", "password")
    missing = [k for k in required if k not in secret]
    if missing:
        # No se exponen valores, solo los nombres de claves faltantes.
        raise RuntimeError(
            f"El secret '{SECRET_ID}' no contiene las claves requeridas: {missing}"
        )
    return {
        "host": secret["host"],
        "port": int(secret["port"]),
        "database": secret["database"],
        "username": secret["username"],
        "password": secret["password"],
    }


def clamp_page_size(page_size: int | None) -> int:
    """Normaliza pageSize dentro de los límites técnicos permitidos."""
    if not page_size or page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def normalize_page(page: int | None) -> int:
    """La paginación es 1-based. Valores inválidos vuelven a la página 1."""
    if not page or page < 1:
        return 1
    return page
