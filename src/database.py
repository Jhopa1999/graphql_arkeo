"""Conexión y ejecución de consultas contra SQL Server.

Usa pytds (python-tds): driver TDS puro en Python, sin dependencias
nativas ni drivers ODBC, lo que lo hace ideal para empaquetar en Lambda.

La conexión se reutiliza entre invocaciones dentro del mismo contenedor
(patrón "warm start") y se valida/reconstruye si quedó en mal estado.
Todas las consultas son parametrizadas (paramstyle 'pyformat': %(nombre)s).
"""
from __future__ import annotations

import datetime
import decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

import pytds

import config

logger = logging.getLogger(__name__)

# Conexión reutilizable a nivel de módulo (persiste en contenedores calientes).
_connection: Optional["pytds.Connection"] = None


def _connect() -> "pytds.Connection":
    creds = config.get_db_credentials()
    return pytds.connect(
        server=creds["host"],
        port=creds["port"],
        database=creds["database"],
        user=creds["username"],
        password=creds["password"],
        login_timeout=config.DB_LOGIN_TIMEOUT,
        timeout=config.DB_QUERY_TIMEOUT,
        as_dict=True,          # cada fila es un dict columna->valor
        autocommit=True,       # solo lecturas (SELECT)
        appname="arkeo-graphql-api",
    )


def _get_connection() -> "pytds.Connection":
    """Devuelve una conexión viva, reconectando si la anterior murió."""
    global _connection
    if _connection is not None:
        try:
            # Ping barato para validar la conexión reutilizada.
            with _connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchall()
            return _connection
        except Exception:  # noqa: BLE001 - conexión en mal estado, se reconstruye
            logger.warning("Conexión SQL en mal estado, reconectando.")
            try:
                _connection.close()
            except Exception:  # noqa: BLE001
                pass
            _connection = None

    _connection = _connect()
    return _connection


def _serialize(value: Any) -> Any:
    """Convierte tipos de SQL Server a valores JSON-friendly para GraphQL."""
    if isinstance(value, (datetime.datetime, datetime.date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value.strip()
    return value


def _serialize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _serialize(v) for k, v in row.items()}


def fetch_count(sql: str, params: Dict[str, Any]) -> int:
    """Ejecuta el COUNT y devuelve el total de registros."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    if not row:
        return 0
    # as_dict=True -> {'total': N}
    return int(next(iter(row.values())))


def fetch_page(sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Ejecuta la consulta paginada y devuelve las filas serializadas."""
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [_serialize_row(r) for r in rows]


def run_paginated(
    count_sql: str,
    count_params: Dict[str, Any],
    page_sql: str,
    page_params: Dict[str, Any],
) -> Tuple[int, List[Dict[str, Any]]]:
    """Ejecuta COUNT + página en la misma conexión. Devuelve (total, filas)."""
    total = fetch_count(count_sql, count_params)
    # Si no hay registros, evitamos la segunda consulta.
    rows = fetch_page(page_sql, page_params) if total > 0 else []
    return total, rows
