"""Construcción segura del SQL parametrizado para el catálogo de productos.

Reglas clave:
- Las condiciones ORIGINALES del SELECT base son inmutables y siempre se aplican.
- Los filtros dinámicos se AÑADEN con AND; nunca reemplazan las reglas de negocio.
- Todo valor de usuario viaja como parámetro (%s / %d), nunca concatenado:
  se evita por completo la inyección SQL.
- La paginación se resuelve en el motor con OFFSET/FETCH (SQL Server 2012+),
  sin cargar todos los registros en memoria.
- El ordenamiento es determinista: la columna elegida más PRO_CODI como desempate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Vista base con las reglas de negocio originales. Cualquier filtro dinámico
# se aplica sobre esta subconsulta, garantizando que las condiciones del
# SELECT original se conserven intactas.
BASE_FROM = """
FROM IN_PRODU
INNER JOIN IN_TIPRO
    ON IN_PRODU.TIP_CODI = IN_TIPRO.TIP_CODI
   AND IN_PRODU.EMP_CODI = IN_TIPRO.EMP_CODI
INNER JOIN IN_UNIME
    ON IN_PRODU.UNI_CODI = IN_UNIME.UNI_CODI
   AND IN_PRODU.EMP_CODI = IN_UNIME.EMP_CODI
WHERE IN_PRODU.EMP_CODI = %(emp_codi)s
  AND LEFT(PRO_CO01, 1) = %(co01_prefix)s
  AND LEN(PRO_CO02) = %(co02_len)s
  AND LEN(PRO_CODI) >= %(codi_min_len)s
"""

# Proyección completa (alias idénticos al SELECT original y al esquema GraphQL).
SELECT_COLUMNS = """
    PRO_CODI                                                        AS codigo_producto,
    PRO_NOMB                                                        AS nombre_producto,
    IN_PRODU.TIP_CODI                                               AS codigo_tipo,
    IN_TIPRO.TIP_NOMB                                               AS nombre_tipo,
    CASE WHEN PRO_ACTI = 'A' THEN 'ACTIVO' ELSE 'INACTIVO' END      AS estado,
    PRO_CO01                                                        AS codigo_sistema,
    PRO_NO01                                                        AS nombre_sistema,
    PRO_CO02                                                        AS codigo_subsistema,
    PRO_NO02                                                        AS nombre_subsistema,
    PRO_FECR                                                        AS fecha_creacion,
    IN_PRODU.AUD_UFAC                                               AS fecha_actualizacion,
    IN_UNIME.UNI_CODI                                               AS codigo_unidad,
    IN_UNIME.UNI_NOMB                                               AS nombre_unidad,
    CASE WHEN PRO_CO02 LIKE '%%M%%' THEN 'TRABAJO' ELSE 'REPUESTO' END AS trabajo_repuesto
"""

# Constantes de las reglas de negocio originales.
BASE_PARAMS: Dict[str, Any] = {
    "emp_codi": 409,
    "co01_prefix": "7",
    "co02_len": 5,
    "codi_min_len": 10,
}

# Mapa de ordenamientos permitidos -> expresión ORDER BY segura (lista blanca).
# Nunca se interpola texto del usuario en ORDER BY: solo claves conocidas.
_ORDER_BY_MAP = {
    "CODIGO_PRODUCTO_ASC": "PRO_CODI ASC",
    "CODIGO_PRODUCTO_DESC": "PRO_CODI DESC",
    "NOMBRE_PRODUCTO_ASC": "PRO_NOMB ASC, PRO_CODI ASC",
    "NOMBRE_PRODUCTO_DESC": "PRO_NOMB DESC, PRO_CODI ASC",
    "FECHA_CREACION_ASC": "PRO_FECR ASC, PRO_CODI ASC",
    "FECHA_CREACION_DESC": "PRO_FECR DESC, PRO_CODI ASC",
}
_DEFAULT_ORDER = "CODIGO_PRODUCTO_ASC"

# Mapa de ordenamientos para sistemas/subsistemas
_SISTEMA_ORDER_BY_MAP = {
    "CODIGO_SISTEMA_ASC": "PRO_CO01 ASC, PRO_CO02 ASC",
    "CODIGO_SISTEMA_DESC": "PRO_CO01 DESC, PRO_CO02 ASC",
    "NOMBRE_SISTEMA_ASC": "PRO_NO01 ASC, PRO_CO01 ASC, PRO_CO02 ASC",
    "NOMBRE_SISTEMA_DESC": "PRO_NO01 DESC, PRO_CO01 ASC, PRO_CO02 ASC",
    "CODIGO_SUBSISTEMA_ASC": "PRO_CO02 ASC, PRO_CO01 ASC",
    "CODIGO_SUBSISTEMA_DESC": "PRO_CO02 DESC, PRO_CO01 ASC",
}
_DEFAULT_SISTEMA_ORDER = "CODIGO_SISTEMA_ASC"


def _build_dynamic_filters(
    filt: Optional[Dict[str, Any]], force_inactive: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """Traduce el input GraphQL ProductoFilter a cláusulas AND parametrizadas.
    
    Args:
        filt: Diccionario de filtros del usuario
        force_inactive: Si es True, fuerza el filtro de productos INACTIVOS
    """
    if not filt:
        filt = {}

    clauses: List[str] = []
    params: Dict[str, Any] = {}

    def add(clause: str, key: str, value: Any) -> None:
        clauses.append(clause)
        params[key] = value

    # Si force_inactive está activado, forzar estado INACTIVO
    if force_inactive:
        clauses.append("PRO_ACTI <> 'A'")
    elif filt.get("estado"):
        # ACTIVO -> PRO_ACTI = 'A'; INACTIVO -> PRO_ACTI <> 'A'
        if filt["estado"] == "ACTIVO":
            clauses.append("PRO_ACTI = 'A'")
        elif filt["estado"] == "INACTIVO":
            clauses.append("PRO_ACTI <> 'A'")

    if filt.get("codigo_producto"):
        add("PRO_CODI = %(f_codigo_producto)s", "f_codigo_producto", filt["codigo_producto"])

    if filt.get("codigo_producto_contains"):
        add(
            "PRO_CODI LIKE %(f_codigo_producto_like)s",
            "f_codigo_producto_like",
            f"%{filt['codigo_producto_contains']}%",
        )

    if filt.get("nombre_producto_contains"):
        add(
            "PRO_NOMB LIKE %(f_nombre_producto_like)s",
            "f_nombre_producto_like",
            f"%{filt['nombre_producto_contains']}%",
        )

    if filt.get("codigo_tipo"):
        add("IN_PRODU.TIP_CODI = %(f_codigo_tipo)s", "f_codigo_tipo", filt["codigo_tipo"])

    if filt.get("codigo_sistema"):
        add("PRO_CO01 = %(f_codigo_sistema)s", "f_codigo_sistema", filt["codigo_sistema"])

    if filt.get("codigo_subsistema"):
        add("PRO_CO02 = %(f_codigo_subsistema)s", "f_codigo_subsistema", filt["codigo_subsistema"])

    if filt.get("codigo_unidad"):
        add("IN_UNIME.UNI_CODI = %(f_codigo_unidad)s", "f_codigo_unidad", filt["codigo_unidad"])

    if filt.get("trabajo_repuesto"):
        # TRABAJO -> PRO_CO02 LIKE '%M%'; REPUESTO -> PRO_CO02 NOT LIKE '%M%'.
        # El patrón '%M%' viaja como PARÁMETRO (no literal) para no colisionar
        # con el paramstyle %(..)s del driver y mantener la consulta parametrizada.
        if filt["trabajo_repuesto"] == "TRABAJO":
            add("PRO_CO02 LIKE %(f_trabajo_like)s", "f_trabajo_like", "%M%")
        elif filt["trabajo_repuesto"] == "REPUESTO":
            add("PRO_CO02 NOT LIKE %(f_trabajo_like)s", "f_trabajo_like", "%M%")

    where = (" AND " + " AND ".join(clauses)) if clauses else ""
    return where, params


def build_count_query(
    filt: Optional[Dict[str, Any]], force_inactive: bool = False
) -> Tuple[str, Dict[str, Any]]:
    """SQL que cuenta el total de registros que cumplen reglas + filtros.
    
    Args:
        filt: Filtros del usuario
        force_inactive: Si es True, cuenta solo productos INACTIVOS
    """
    dyn_where, dyn_params = _build_dynamic_filters(filt, force_inactive)
    sql = f"SELECT COUNT(1) AS total {BASE_FROM}{dyn_where}"
    params = {**BASE_PARAMS, **dyn_params}
    return sql, params


def build_page_query(
    filt: Optional[Dict[str, Any]],
    order_by: Optional[str],
    page: int,
    page_size: int,
    force_inactive: bool = False,
) -> Tuple[str, Dict[str, Any]]:
    """SQL que devuelve una página concreta usando OFFSET/FETCH (paginación real).

    OFFSET = (page - 1) * page_size. El motor solo materializa page_size filas.
    
    Args:
        filt: Filtros del usuario
        order_by: Criterio de ordenamiento
        page: Número de página (1-based)
        page_size: Tamaño de página
        force_inactive: Si es True, filtra solo productos INACTIVOS
    """
    dyn_where, dyn_params = _build_dynamic_filters(filt, force_inactive)
    order_expr = _ORDER_BY_MAP.get(order_by or _DEFAULT_ORDER, _ORDER_BY_MAP[_DEFAULT_ORDER])
    offset = (page - 1) * page_size

    sql = (
        f"SELECT {SELECT_COLUMNS}{BASE_FROM}{dyn_where}\n"
        f"ORDER BY {order_expr}\n"
        f"OFFSET %(offset)s ROWS FETCH NEXT %(limit)s ROWS ONLY"
    )
    params = {
        **BASE_PARAMS,
        **dyn_params,
        "offset": offset,
        "limit": page_size,
    }
    return sql, params


def build_sistemas_subsistemas_query(
    order_by: Optional[str]
) -> Tuple[str, Dict[str, Any]]:
    """SQL que devuelve la lista DISTINCT de sistemas y subsistemas.
    
    Retorna grupos únicos (codigo_sistema, nombre_sistema, codigo_subsistema, nombre_subsistema)
    útil para poblar filtros o catálogos en interfaces de usuario.
    
    Args:
        order_by: Criterio de ordenamiento para sistemas/subsistemas
    """
    order_expr = _SISTEMA_ORDER_BY_MAP.get(
        order_by or _DEFAULT_SISTEMA_ORDER, 
        _SISTEMA_ORDER_BY_MAP[_DEFAULT_SISTEMA_ORDER]
    )
    
    sql = f"""
SELECT DISTINCT
    PRO_CO01 AS codigo_sistema,
    PRO_NO01 AS nombre_sistema,
    PRO_CO02 AS codigo_subsistema,
    PRO_NO02 AS nombre_subsistema
{BASE_FROM}
ORDER BY {order_expr}
"""
    
    params = {**BASE_PARAMS}
    return sql, params
