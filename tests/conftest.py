"""Configuración de pytest.

Los módulos de la Lambda viven en src/ y usan imports absolutos (config,
database, query_builder), tal como se ejecutan en Lambda (donde CodeUri=src/
es la raíz). Para reproducir ese entorno en los tests, se añade src/ al path.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
for p in (SRC, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)
