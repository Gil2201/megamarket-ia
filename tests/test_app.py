"""Prueba de humo de la interfaz: cada página carga sin excepciones.

No revisa cifras (eso lo hacen test_sprint*.py); solo que la app no se rompa.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent
APP = str(RAIZ / "app.py")


@pytest.fixture(autouse=True)
def en_la_raiz(monkeypatch):
    """La app abre assets/ y data/ con rutas relativas a la raíz del repo."""
    monkeypatch.chdir(RAIZ)

PAGINAS = [
    "megamarket_app/paginas/inicio.py",
    "megamarket_app/paginas/clientes_semana.py",
    "megamarket_app/paginas/ruta_optima.py",
    "megamarket_app/paginas/viabilidad.py",
    "megamarket_app/paginas/que_lanzar.py",
    "megamarket_app/paginas/competidor.py",
    "megamarket_app/paginas/desempate_difuso.py",
    "megamarket_app/paginas/asistente.py",
]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_carga_sin_errores(pagina):
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.switch_page(pagina).run()
    assert not app.exception, app.exception


def test_flujo_que_lanzar_y_competidor():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.switch_page("megamarket_app/paginas/que_lanzar.py").run()
    next(b for b in app.button if b.label == "Ejecutar algoritmo genético").click().run()
    assert not app.exception, app.exception
    assert len(app.session_state["empates"]["esperada"]) == 2
    app.switch_page("megamarket_app/paginas/competidor.py").run()
    next(b for b in app.button if b.label == "Ejecutar AG con Minimax").click().run()
    assert not app.exception, app.exception
    assert len(app.session_state["empates"]["peor_caso"]) == 2
