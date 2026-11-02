"""Punto de entrada de MegaMarket IA.

Corre con:  streamlit run app.py
Define la navegación (SPEC §4.1), inicializa el estado compartido entre
páginas (SPEC §5.3) y pone el pie de página en todas las páginas.
"""

import copy

import streamlit as st

from megamarket import difuso
from megamarket.datos import CANDIDATOS, EROSION, ESPACIO_BODEGA_TOTAL, PRESUPUESTO_TOTAL
from megamarket.sistema_experto_logistica import BASE_CONOCIMIENTO, leer_memoria_logistica
from megamarket_app import componentes, tema
from megamarket_app.memoria_logistica import csv_a_editor

st.set_page_config(
    page_title="MegaMarket IA",
    page_icon="assets/icono-megamarket.png",
    layout="wide",
)


def inicializar_estado():
    """Estado compartido entre páginas, en un solo lugar (SPEC §5.3).

    Todo arranca con los datos originales de los notebooks.
    """
    if "productos_difusos" not in st.session_state:
        # datos de la nota difusa (página 3): {producto: {"tipo", "C2", criterios numéricos}}
        st.session_state["productos_difusos"] = difuso.construir_productos_difusos(difuso.leer_memoria_difusa())
    if "memoria_logistica" not in st.session_state:
        # DataFrame editado (Clientes de la semana), arranca con el CSV original
        st.session_state["memoria_logistica"] = csv_a_editor(leer_memoria_logistica())
    claves = {
        "umbrales_logistica": dict(BASE_CONOCIMIENTO["umbrales"]),  # umbrales editados (R2 y R4)
        "seleccion_semana": None,   # {ruta: {"incluidos": [...], "prioridad": {...}}}
        "ruta_elegida": "Ambas",    # ruta que se estaba mirando en la página 1
        "candidatos": copy.deepcopy(CANDIDATOS),  # dict de candidatos editado (Qué lanzar)
        "restricciones": {"presupuesto": PRESUPUESTO_TOTAL, "espacio": ESPACIO_BODEGA_TOTAL},
        "erosion": dict(EROSION),   # erosión editada (Competidor)
        "resultado_ag": None,       # mejor portafolio, historial, empates
        "empates": None,            # portafolios empatados por criterio (Sprint 4)
        "desempate": None,          # ganador del desempate difuso (página 6)
    }
    for clave, valor in claves.items():
        st.session_state.setdefault(clave, valor)


inicializar_estado()
tema.aplicar_css()
st.logo("assets/logo-megamarket-blanco.png", size="large", icon_image="assets/icono-megamarket.png")

RUTA = "megamarket_app/paginas"
paginas = {
    "": [
        st.Page(f"{RUTA}/inicio.py", title="Inicio", icon=":material/home:", default=True),
    ],
    "Logística": [
        st.Page(f"{RUTA}/clientes_semana.py", title="1. Clientes de la semana",
                icon=":material/fact_check:", url_path="clientes-de-la-semana"),
        st.Page(f"{RUTA}/ruta_optima.py", title="2. Ruta óptima",
                icon=":material/route:", url_path="ruta-optima"),
    ],
    "Portafolio": [
        st.Page(f"{RUTA}/viabilidad.py", title="3. Viabilidad de productos",
                icon=":material/rule:", url_path="viabilidad"),
        st.Page(f"{RUTA}/que_lanzar.py", title="4. Qué lanzar",
                icon=":material/inventory_2:", url_path="que-lanzar"),
        st.Page(f"{RUTA}/competidor.py", title="5. Competidor",
                icon=":material/swords:", url_path="competidor"),
        st.Page(f"{RUTA}/desempate_difuso.py", title="6. Desempate difuso",
                icon=":material/blur_on:", url_path="desempate-difuso"),
    ],
    "Asistente": [
        st.Page(f"{RUTA}/asistente.py", title="Asistente MegaMarket",
                icon=":material/smart_toy:", url_path="asistente"),
    ],
}

pagina = st.navigation(paginas)
pagina.run()
componentes.pie_de_pagina()
