"""Prueba manual local: ejecuta el handler tal cual lo haría AppSync,
contra el SQL Server real, e imprime el resultado formateado.

Uso:
    $env:AWS_REGION="us-east-2"
    .\.venv\Scripts\python.exe scripts\prueba_local.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

import handler  # noqa: E402


def mostrar(titulo, event):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
    res = handler.lambda_handler(event)
    pg = res["pagination"]
    print(f"paginacion: {json.dumps(pg, ensure_ascii=False)}")
    print(f"filas en esta pagina: {len(res['data'])}")
    for row in res["data"][:3]:
        print("  -", json.dumps(row, ensure_ascii=False))
    if len(res["data"]) > 3:
        print(f"  ... (+{len(res['data']) - 3} filas mas)")


if __name__ == "__main__":
    # 1) Primera pagina, 5 registros
    mostrar(
        "1) productos(page:1, pageSize:5)",
        {"field": "productos", "arguments": {"page": 1, "pageSize": 5}},
    )

    # 2) Segunda pagina (verifica que cambian los registros)
    mostrar(
        "2) productos(page:2, pageSize:5)",
        {"field": "productos", "arguments": {"page": 2, "pageSize": 5}},
    )

    # 3) Con filtro de estado ACTIVO
    mostrar(
        "3) productos(page:1, pageSize:5, filter:{estado:ACTIVO})",
        {"field": "productos", "arguments": {"page": 1, "pageSize": 5, "filter": {"estado": "ACTIVO"}}},
    )

    # 4) Solo TRABAJO, ordenado por nombre
    mostrar(
        "4) productos(filter:{trabajo_repuesto:TRABAJO}, orderBy:NOMBRE_PRODUCTO_ASC)",
        {"field": "productos", "arguments": {"page": 1, "pageSize": 5, "filter": {"trabajo_repuesto": "TRABAJO"}, "orderBy": "NOMBRE_PRODUCTO_ASC"}},
    )
    print("\nOK: handler ejecutado contra SQL Server real.")
