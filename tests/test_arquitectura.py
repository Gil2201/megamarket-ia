"""Reglas de arquitectura (CLAUDE.md, regla 2): la lógica no depende de la interfaz."""

import ast
from pathlib import Path

CARPETA_LOGICA = Path(__file__).resolve().parent.parent / "megamarket"


def test_megamarket_no_importa_streamlit():
    for archivo in CARPETA_LOGICA.glob("*.py"):
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                modulos = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                modulos = [nodo.module or ""]
            else:
                continue
            assert not any(m.split(".")[0] == "streamlit" for m in modulos), archivo.name
