"""Reglas de arquitectura (CLAUDE.md, regla 2): la lógica no depende de la interfaz."""

import ast
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETAS_LOGICA = [RAIZ / "megamarket", RAIZ / "agente"]


def test_logica_y_agente_no_importan_streamlit():
    for archivo in [a for carpeta in CARPETAS_LOGICA for a in carpeta.glob("*.py")]:
        arbol = ast.parse(archivo.read_text(encoding="utf-8"))
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                modulos = [alias.name for alias in nodo.names]
            elif isinstance(nodo, ast.ImportFrom):
                modulos = [nodo.module or ""]
            else:
                continue
            assert not any(m.split(".")[0] == "streamlit" for m in modulos), archivo.name
