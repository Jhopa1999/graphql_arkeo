"""Pruebas del handler AppSync: cálculo de paginación, despacho por campo
y manejo seguro de errores. Se mockea la capa de base de datos."""
import sys
from unittest import mock

# pytds no está instalado en el entorno de test unitario: se stubea para que
# 'src.database' (y por ende 'src.handler') puedan importarse.
sys.modules.setdefault("pytds", mock.MagicMock())

import handler  # noqa: E402


def _patch_db(total, rows):
    return mock.patch.object(
        handler.database, "run_paginated", return_value=(total, rows)
    )


def test_productos_pagina_intermedia():
    rows = [{"codigo_producto": "0000000001", "nombre_producto": "X"}]
    with _patch_db(250, rows):
        event = {"field": "productos", "arguments": {"page": 2, "pageSize": 100}}
        res = handler.lambda_handler(event)

    pg = res["pagination"]
    assert res["data"] == rows
    assert pg["page"] == 2
    assert pg["pageSize"] == 100
    assert pg["totalRegistros"] == 250
    assert pg["totalPaginas"] == 3  # ceil(250/100)
    assert pg["hasNextPage"] is True
    assert pg["hasPreviousPage"] is True


def test_productos_primera_pagina():
    with _patch_db(50, [{"codigo_producto": "a"}]):
        res = handler.lambda_handler(
            {"field": "productos", "arguments": {"page": 1, "pageSize": 100}}
        )
    pg = res["pagination"]
    assert pg["totalPaginas"] == 1
    assert pg["hasNextPage"] is False
    assert pg["hasPreviousPage"] is False


def test_productos_ultima_pagina():
    with _patch_db(250, [{"codigo_producto": "a"}]):
        res = handler.lambda_handler(
            {"field": "productos", "arguments": {"page": 3, "pageSize": 100}}
        )
    pg = res["pagination"]
    assert pg["hasNextPage"] is False
    assert pg["hasPreviousPage"] is True


def test_productos_sin_resultados():
    with _patch_db(0, []):
        res = handler.lambda_handler(
            {"field": "productos", "arguments": {"page": 1, "pageSize": 100}}
        )
    pg = res["pagination"]
    assert res["data"] == []
    assert pg["totalRegistros"] == 0
    assert pg["totalPaginas"] == 0
    assert pg["hasNextPage"] is False
    assert pg["hasPreviousPage"] is False


def test_campo_no_soportado():
    try:
        handler.lambda_handler({"field": "desconocido", "arguments": {}})
        assert False, "debía fallar"
    except handler.ResolverError as e:
        assert "no soportado" in str(e)


def test_error_db_se_enmascara():
    with mock.patch.object(
        handler.database, "run_paginated", side_effect=Exception("detalle sensible SQL")
    ):
        try:
            handler.lambda_handler(
                {"field": "productos", "arguments": {"page": 1, "pageSize": 10}}
            )
            assert False, "debía fallar"
        except handler.ResolverError as e:
            # El mensaje al cliente no filtra el detalle interno.
            assert "detalle sensible" not in str(e)
            assert "Error interno" in str(e)
