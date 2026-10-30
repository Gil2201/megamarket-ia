"""Piezas de la plantilla común de página (SPEC §4.2).

Orden de cada página:
  1. encabezado_pagina()  -> chip del sprint + pregunta de negocio + "El problema"
  2. datos de entrada, botón principal, resultado y "Cómo razonó" (propios de cada página)
  3. ver_codigo()          -> código real de las funciones clave
  4. supuestos_y_limites() -> notas de honestidad
El pie de página lo pone app.py en todas las páginas.
"""

import inspect
from html import escape

import streamlit as st


def encabezado_pagina(pregunta, chip, problema):
    """Título = pregunta de negocio; chip con sprint y técnica; 2-4 líneas del problema."""
    st.markdown(
        f'<span class="mm-chip"><span class="mm-chip-punto"></span>{escape(chip)}</span>'
        f'<div class="mm-titulo">{escape(pregunta)}</div>'
        f'<div class="mm-problema">{escape(problema)}</div>',
        unsafe_allow_html=True,
    )


def ver_codigo(funciones):
    """Expander con el código fuente real de las funciones (para la sustentación)."""
    with st.expander("Ver el código", icon=":material/code:"):
        if not funciones:
            st.caption("El código se mostrará aquí cuando la lógica esté portada.")
        for funcion in funciones:
            st.code(inspect.getsource(funcion), language="python")


def supuestos_y_limites(notas):
    """Expander con las notas de honestidad de los notebooks."""
    with st.expander("Supuestos y límites", icon=":material/info:"):
        for nota in notas:
            st.markdown(f"- {nota}")


def proximamente(texto):
    """Aviso para páginas o secciones que todavía no se construyen."""
    st.info(texto, icon=":material/construction:")


def pie_de_pagina():
    """Aviso obligatorio: Megamarket es una empresa real."""
    st.markdown(
        '<div class="mm-pie">Proyecto académico — Universidad EIA. '
        "No es un sitio oficial de Megamarket.</div>",
        unsafe_allow_html=True,
    )
