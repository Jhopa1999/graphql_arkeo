"""Prueba end-to-end contra el endpoint AppSync (igual que Postman).

Uso (PowerShell):
    $env:APPSYNC_API_KEY="da2-xxxx"
    .\.venv\Scripts\python.exe scripts\prueba_graphql.py
"""
import json
import os
import urllib.request

URL = os.environ.get(
    "APPSYNC_URL",
    "https://xetmcig7xzdvzey5boopm5ivaq.appsync-api.us-east-2.amazonaws.com/graphql",
)
API_KEY = os.environ.get("APPSYNC_API_KEY", "")
if not API_KEY:
    raise SystemExit(
        "Define la variable de entorno APPSYNC_API_KEY con el API key. "
        'Ej: $env:APPSYNC_API_KEY="da2-xxxx"'
    )


def gql(query, variables=None):
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        URL,
        data=body,
        headers={"Content-Type": "application/json", "x-api-key": API_KEY},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read())


def run(titulo, query, variables=None):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
    try:
        payload = gql(query, variables)
    except Exception as e:  # noqa: BLE001
        print("ERROR HTTP:", e)
        return
    if "errors" in payload:
        print("ERRORES GraphQL:", json.dumps(payload["errors"], ensure_ascii=False))
    data = payload.get("data", {}).get("productos")
    if data:
        print("pagination:", json.dumps(data["pagination"], ensure_ascii=False))
        print("filas:", len(data["data"]))
        for row in data["data"][:2]:
            print("  -", json.dumps(row, ensure_ascii=False))


Q_BASIC = """
query ($p:Int!, $s:Int!) {
  productos(page:$p, pageSize:$s) {
    data { codigo_producto nombre_producto estado trabajo_repuesto }
    pagination { page pageSize totalRegistros totalPaginas hasNextPage hasPreviousPage }
  }
}
"""

Q_FILTER = """
query ($p:Int!, $s:Int!, $f:ProductoFilter, $o:ProductoOrderBy) {
  productos(page:$p, pageSize:$s, filter:$f, orderBy:$o) {
    data { codigo_producto nombre_producto codigo_tipo nombre_unidad trabajo_repuesto estado }
    pagination { page pageSize totalRegistros totalPaginas hasNextPage hasPreviousPage }
  }
}
"""

if __name__ == "__main__":
    run("1) Basico page=1 size=5", Q_BASIC, {"p": 1, "s": 5})
    run("2) Pagina 2 size=5", Q_BASIC, {"p": 2, "s": 5})
    run("3) Filtro estado ACTIVO", Q_FILTER,
        {"p": 1, "s": 5, "f": {"estado": "ACTIVO"}, "o": "CODIGO_PRODUCTO_ASC"})
    run("4) Filtro trabajo_repuesto TRABAJO + orderBy nombre", Q_FILTER,
        {"p": 1, "s": 5, "f": {"trabajo_repuesto": "TRABAJO"}, "o": "NOMBRE_PRODUCTO_ASC"})
    run("5) Filtro nombre_producto_contains 'TURBO'", Q_FILTER,
        {"p": 1, "s": 5, "f": {"nombre_producto_contains": "TURBO"}})
    print("\nFIN")
