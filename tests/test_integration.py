"""Pruebas de integración (opcionales, gated por variables de entorno).

- test_db_*: requieren RUN_DB_INTEGRATION=1 y acceso de red a SQL Server
  (VPN) + el secret en Secrets Manager. Validan conexión, consulta real,
  paginación y filtros contra la base.
- test_graphql_*: requieren RUN_GRAPHQL_INTEGRATION=1 + APPSYNC_URL y
  APPSYNC_API_KEY. Validan la respuesta GraphQL extremo a extremo.

Se omiten automáticamente si las variables no están presentes, de modo que
la suite unitaria siempre corre sin dependencias externas.
"""
import os
import urllib.request
import json

import pytest


# ------------------------------------------------------------------ DB directa
run_db = os.environ.get("RUN_DB_INTEGRATION") == "1"
db_reason = "define RUN_DB_INTEGRATION=1 y acceso a SQL Server para ejecutar"


@pytest.mark.skipif(not run_db, reason=db_reason)
def test_db_conexion_y_count():
    import database, query_builder

    sql, params = query_builder.build_count_query(None)
    total = database.fetch_count(sql, params)
    assert isinstance(total, int)
    assert total >= 0


@pytest.mark.skipif(not run_db, reason=db_reason)
def test_db_paginacion_devuelve_pagesize_filas():
    import database, query_builder

    count_sql, count_params = query_builder.build_count_query(None)
    page_sql, page_params = query_builder.build_page_query(None, None, page=1, page_size=5)
    total, rows = database.run_paginated(count_sql, count_params, page_sql, page_params)
    if total >= 5:
        assert len(rows) == 5
    # Verifica reglas de negocio en los datos devueltos.
    for r in rows:
        assert r["codigo_producto"] and len(r["codigo_producto"]) >= 10
        assert r["codigo_subsistema"] and len(r["codigo_subsistema"]) == 5
        assert str(r["codigo_sistema"]).startswith("7")


@pytest.mark.skipif(not run_db, reason=db_reason)
def test_db_filtro_estado_activo_solo_activos():
    import database, query_builder

    count_sql, count_params = query_builder.build_count_query({"estado": "ACTIVO"})
    page_sql, page_params = query_builder.build_page_query(
        {"estado": "ACTIVO"}, None, page=1, page_size=10
    )
    _, rows = database.run_paginated(count_sql, count_params, page_sql, page_params)
    for r in rows:
        assert r["estado"] == "ACTIVO"


# ---------------------------------------------------------------- GraphQL e2e
run_gql = os.environ.get("RUN_GRAPHQL_INTEGRATION") == "1"
gql_reason = "define RUN_GRAPHQL_INTEGRATION=1, APPSYNC_URL y APPSYNC_API_KEY"


@pytest.mark.skipif(not run_gql, reason=gql_reason)
def test_graphql_productos_paginado():
    url = os.environ["APPSYNC_URL"]
    api_key = os.environ["APPSYNC_API_KEY"]
    query = """
    query ($p:Int!, $s:Int!) {
      productos(page:$p, pageSize:$s) {
        data { codigo_producto nombre_producto estado trabajo_repuesto }
        pagination { page pageSize totalRegistros totalPaginas hasNextPage hasPreviousPage }
      }
    }
    """
    body = json.dumps({"query": query, "variables": {"p": 1, "s": 10}}).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read())

    assert "errors" not in payload, payload
    data = payload["data"]["productos"]
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["pageSize"] == 10
    assert len(data["data"]) <= 10
