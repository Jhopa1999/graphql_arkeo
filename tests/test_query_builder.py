"""Pruebas unitarias del constructor de SQL: reglas de negocio, filtros,
paginación, ordenamiento y parametrización (anti-inyección)."""
import query_builder as qb


def test_base_rules_siempre_presentes_en_count():
    sql, params = qb.build_count_query(None)
    assert "IN_PRODU.EMP_CODI = %(emp_codi)s" in sql
    assert "LEFT(PRO_CO01, 1) = %(co01_prefix)s" in sql
    assert "LEN(PRO_CO02) = %(co02_len)s" in sql
    assert "LEN(PRO_CODI) >= %(codi_min_len)s" in sql
    assert params["emp_codi"] == 409
    assert params["co01_prefix"] == "7"
    assert params["co02_len"] == 5
    assert params["codi_min_len"] == 10


def test_paginacion_offset_fetch_calculo():
    # page 3, pageSize 50 -> OFFSET 100
    sql, params = qb.build_page_query(None, None, page=3, page_size=50)
    assert "OFFSET %(offset)s ROWS FETCH NEXT %(limit)s ROWS ONLY" in sql
    assert params["offset"] == 100
    assert params["limit"] == 50


def test_ordenamiento_determinista_por_defecto():
    sql, _ = qb.build_page_query(None, None, page=1, page_size=10)
    assert "ORDER BY PRO_CODI ASC" in sql


def test_ordenamiento_nombre_desempata_por_codigo():
    sql, _ = qb.build_page_query(None, "NOMBRE_PRODUCTO_ASC", page=1, page_size=10)
    assert "ORDER BY PRO_NOMB ASC, PRO_CODI ASC" in sql


def test_orderby_invalido_cae_en_default_sin_interpolar():
    # Un valor arbitrario (potencial inyección) nunca llega al SQL.
    sql, _ = qb.build_page_query(None, "DROP TABLE; --", page=1, page_size=10)
    assert "DROP TABLE" not in sql
    assert "ORDER BY PRO_CODI ASC" in sql


def test_filtro_estado_activo():
    sql, _ = qb.build_count_query({"estado": "ACTIVO"})
    assert "PRO_ACTI = 'A'" in sql


def test_filtro_estado_inactivo():
    sql, _ = qb.build_count_query({"estado": "INACTIVO"})
    assert "PRO_ACTI <> 'A'" in sql


def test_filtro_trabajo_repuesto():
    sql_t, params_t = qb.build_count_query({"trabajo_repuesto": "TRABAJO"})
    sql_r, params_r = qb.build_count_query({"trabajo_repuesto": "REPUESTO"})
    # El patrón viaja parametrizado, no como literal en el SQL.
    assert "PRO_CO02 LIKE %(f_trabajo_like)s" in sql_t
    assert "PRO_CO02 NOT LIKE %(f_trabajo_like)s" in sql_r
    assert params_t["f_trabajo_like"] == "%M%"
    assert params_r["f_trabajo_like"] == "%M%"


def test_filtro_contains_usa_parametro_like():
    sql, params = qb.build_count_query({"nombre_producto_contains": "aceite"})
    assert "PRO_NOMB LIKE %(f_nombre_producto_like)s" in sql
    assert params["f_nombre_producto_like"] == "%aceite%"


def test_filtro_valor_malicioso_viaja_como_parametro():
    # El valor no se concatena: no aparece en el texto del SQL.
    payload = "'; DROP TABLE IN_PRODU; --"
    sql, params = qb.build_count_query({"codigo_producto": payload})
    assert payload not in sql
    assert params["f_codigo_producto"] == payload
    assert "PRO_CODI = %(f_codigo_producto)s" in sql


def test_filtros_se_combinan_con_and_sin_romper_reglas_base():
    sql, params = qb.build_count_query(
        {"codigo_tipo": "T1", "codigo_unidad": "U1"}
    )
    # Reglas base intactas + ambos filtros añadidos con AND.
    assert "IN_PRODU.EMP_CODI = %(emp_codi)s" in sql
    assert "IN_PRODU.TIP_CODI = %(f_codigo_tipo)s" in sql
    assert "IN_UNIME.UNI_CODI = %(f_codigo_unidad)s" in sql
    assert params["f_codigo_tipo"] == "T1"
    assert params["f_codigo_unidad"] == "U1"


def test_sin_filtros_no_agrega_and_extra():
    sql, _ = qb.build_count_query(None)
    # El WHERE base termina en la regla de longitud mínima.
    assert sql.rstrip().endswith("LEN(PRO_CODI) >= %(codi_min_len)s")
