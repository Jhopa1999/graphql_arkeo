"""Handler Lambda para los resolvers de AppSync (ARKEO Fleet GraphQL).

Integración: AppSync Direct Lambda Resolver.
AppSync invoca esta función con un evento que incluye:
  - event["field"]      -> nombre del campo resuelto (p.ej. "productos")
  - event["arguments"]  -> argumentos de la query (page, pageSize, filter, orderBy)

Devuelve el objeto que AppSync mapea al tipo de salida del esquema.
El cliente GraphQL elige qué subcampos recibir (consultas flexibles); AppSync
se encarga de proyectar únicamente los campos solicitados.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import config
import database
import query_builder

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


class ResolverError(Exception):
    """Error controlado que se devuelve a AppSync como mensaje seguro."""


def _resolve_productos(arguments: Dict[str, Any]) -> Dict[str, Any]:
    page = config.normalize_page(arguments.get("page"))
    page_size = config.clamp_page_size(arguments.get("pageSize"))
    filt = arguments.get("filter") or None
    order_by = arguments.get("orderBy")

    count_sql, count_params = query_builder.build_count_query(filt)
    page_sql, page_params = query_builder.build_page_query(
        filt, order_by, page, page_size
    )

    total, rows = database.run_paginated(
        count_sql, count_params, page_sql, page_params
    )

    total_paginas = (total + page_size - 1) // page_size if page_size else 0

    return {
        "data": rows,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalRegistros": total,
            "totalPaginas": total_paginas,
            "hasNextPage": page < total_paginas,
            "hasPreviousPage": page > 1 and total > 0,
        },
    }


def _resolve_productos_inactivos(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Resuelve la query productosInactivos.
    
    Funciona igual que productos pero fuerza el filtro de estado INACTIVO.
    """
    page = config.normalize_page(arguments.get("page"))
    page_size = config.clamp_page_size(arguments.get("pageSize"))
    filt = arguments.get("filter") or None
    order_by = arguments.get("orderBy")

    # force_inactive=True aplica automáticamente el filtro de productos inactivos
    count_sql, count_params = query_builder.build_count_query(filt, force_inactive=True)
    page_sql, page_params = query_builder.build_page_query(
        filt, order_by, page, page_size, force_inactive=True
    )

    total, rows = database.run_paginated(
        count_sql, count_params, page_sql, page_params
    )

    total_paginas = (total + page_size - 1) // page_size if page_size else 0

    return {
        "data": rows,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalRegistros": total,
            "totalPaginas": total_paginas,
            "hasNextPage": page < total_paginas,
            "hasPreviousPage": page > 1 and total > 0,
        },
    }


def _resolve_sistemas_subsistemas(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Resuelve la query sistemasSubsistemas.
    
    Retorna lista DISTINCT de sistemas y subsistemas (sin paginación).
    Útil para poblar filtros en interfaces de usuario.
    """
    order_by = arguments.get("orderBy")
    
    sql, params = query_builder.build_sistemas_subsistemas_query(order_by)
    rows = database.fetch_all(sql, params)
    
    return rows


# Despachador por campo del esquema (extensible a futuras queries).
_RESOLVERS = {
    "productos": _resolve_productos,
    "productosInactivos": _resolve_productos_inactivos,
    "sistemasSubsistemas": _resolve_sistemas_subsistemas,
}


def lambda_handler(event: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    field = event.get("field") or event.get("info", {}).get("fieldName")
    arguments = event.get("arguments", {}) or {}

    logger.info("Resolviendo campo '%s' args=%s", field, json.dumps(arguments, default=str))

    resolver = _RESOLVERS.get(field)
    if resolver is None:
        raise ResolverError(f"Campo no soportado: {field}")

    try:
        return resolver(arguments)
    except ResolverError:
        raise
    except Exception as exc:  # noqa: BLE001
        # Manejo seguro de errores: se registra el detalle en CloudWatch pero
        # al cliente solo se le devuelve un mensaje genérico (sin credenciales,
        # SQL ni detalles internos que faciliten un ataque).
        logger.exception("Error resolviendo '%s'", field)
        raise ResolverError(
            "Error interno al consultar el catálogo de productos."
        ) from exc
