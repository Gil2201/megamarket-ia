"""Inicio: qué es MegaMarket y qué hace esta app (la versión completa llega en la Fase 4)."""

import base64
from pathlib import Path

import streamlit as st

LOGO = Path("assets/logo-megamarket-blanco.png")
logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()

st.markdown(
    f"""
    <div class="mm-hero">
        <img src="data:image/png;base64,{logo_b64}" alt="Megamarket">
        <p>Algoritmos de inteligencia artificial clásica aplicados a la logística
        y al portafolio de MegaMarket, en un solo lugar.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("### Dos cadenas de decisión")
col_log, col_port = st.columns(2, gap="large")

with col_log:
    with st.container(border=True):
        st.markdown("**Logística**")
        st.caption("Sprint 2 → Sprint 1")
        st.page_link("megamarket_app/paginas/clientes_semana.py",
                     label="1. ¿A quién visitamos esta semana?", icon=":material/fact_check:")
        st.page_link("megamarket_app/paginas/ruta_optima.py",
                     label="2. ¿En qué orden y cuántos km?", icon=":material/route:")

with col_port:
    with st.container(border=True):
        st.markdown("**Portafolio**")
        st.caption("Sprint 2 → Sprint 3A → Sprint 3B → Sprint 4")
        st.page_link("megamarket_app/paginas/viabilidad.py",
                     label="3. ¿La categoría cumple los criterios?", icon=":material/rule:")
        st.page_link("megamarket_app/paginas/que_lanzar.py",
                     label="4. ¿Qué referencias lanzamos?", icon=":material/inventory_2:")
        st.page_link("megamarket_app/paginas/competidor.py",
                     label="5. ¿Y si un rival reacciona?", icon=":material/swords:")

st.markdown(
    '<p class="mm-nota">Fundamentos de Inteligencia Artificial — Universidad EIA · '
    "Jacobo Argote, Andrés Cardona, Miguel Valencia y Juan José Gil · "
    "Código desarrollado con apoyo de Claude.</p>",
    unsafe_allow_html=True,
)
