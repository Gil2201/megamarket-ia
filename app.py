"""Punto de entrada de MegaMarket IA.

Corre con:  streamlit run app.py
Define la navegación (SPEC §4.1), inicializa el estado compartido entre
páginas (SPEC §5.3) y pone el pie de página en todas las páginas.
"""

import streamlit as st

from megamarket_app import componentes, tema

st.set_page_config(
    page_title="MegaMarket IA",
    page_icon=":material/local_shipping:",
    layout="wide",
)


def inicializar_estado():
    """Estado compartido entre páginas, en un solo lugar (SPEC §5.3).

    Por ahora todo arranca vacío; en las fases 2 y 3 se carga con los
    datos originales cuando la lógica de megamarket/ esté portada.
    """
    claves = {
        "memoria_logistica": None,  # DataFrame editado (Clientes de la semana)
        "seleccion_semana": None,   # {ruta: {"incluidos": [...], "prioridad": {...}}}
        "candidatos": None,         # dict de candidatos editado (Qué lanzar)
        "resultado_ag": None,       # mejor portafolio, historial, empates
        "empates": None,            # portafolios empatados por criterio (Sprint 4)
    }
    for clave, valor in claves.items():
        st.session_state.setdefault(clave, valor)


inicializar_estado()
tema.aplicar_css()
st.logo("assets/logo-megamarket-blanco.png", size="large")

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
    ],
    "Próximamente": [
        st.Page(f"{RUTA}/desempate_difuso.py", title="6. Desempate difuso",
                icon=":material/blur_on:", url_path="desempate-difuso"),
        st.Page(f"{RUTA}/asistente.py", title="Asistente MegaMarket",
                icon=":material/smart_toy:", url_path="asistente"),
    ],
}

pagina = st.navigation(paginas)
pagina.run()
componentes.pie_de_pagina()
