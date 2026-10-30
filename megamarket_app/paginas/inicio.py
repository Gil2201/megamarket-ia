"""Inicio: qué es MegaMarket, qué hace esta app y cómo se conectan los sprints."""

import base64
from pathlib import Path

import streamlit as st

from megamarket_app.tema import PALETA

LOGO = Path("assets/logo-megamarket-blanco.png")
logo_b64 = base64.b64encode(LOGO.read_bytes()).decode()
PAGINAS = "megamarket_app/paginas"

st.markdown(
    f"""
    <div class="mm-hero">
        <img src="data:image/png;base64,{logo_b64}" alt="Megamarket">
        <p><b>MegaMarket IA</b> — los algoritmos de inteligencia artificial clásica que
        construimos este semestre, aplicados a la logística y al portafolio de MegaMarket,
        en un solo lugar.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "MegaMarket es una empresa colombiana fundada en 1997 en Medellín que vende marcas propias "
    "como **Riovalle** y representa otras marcas de consumo masivo ante cadenas de supermercado. "
    "Esta app toma a MegaMarket como caso de estudio: puedes **usar** cada algoritmo con datos "
    "editables, ver **cómo razona** paso a paso y entender cómo se pasan resultados entre sí. "
    "Las cifras operativas son **ilustrativas**."
)

# =============================================================================
# LAS DOS CADENAS DE DECISIÓN
# =============================================================================
st.subheader("Dos cadenas de decisión")


def paso(columna, ruta, numero_titulo, pregunta, chip, icono):
    with columna.container(border=True, height="stretch"):
        st.caption(chip)
        st.page_link(f"{PAGINAS}/{ruta}", label=numero_titulo, icon=icono)
        st.markdown(pregunta)


def flecha(columna, texto):
    columna.markdown(
        f'<div style="text-align:center;color:{PALETA["gris"]};font-size:.75rem;padding-top:2.2rem">'
        f'<span style="font-size:1.5rem;color:{PALETA["azul_rey"]}">→</span><br>{texto}</div>',
        unsafe_allow_html=True,
    )


st.markdown("**Logística** — ¿a quién visitamos y en qué orden?")
c1, f1, c2, _ = st.columns([4, 1.2, 4, 5.2])
paso(c1, "clientes_semana.py", "1. Clientes de la semana", "¿A quién visitamos y con qué prioridad?",
     "Sprint 2 · Sistema experto", ":material/fact_check:")
flecha(f1, "clientes + prioridad")
paso(c2, "ruta_optima.py", "2. Ruta óptima", "¿En qué orden y cuántos km?",
     "Sprint 1 · Búsqueda A*", ":material/route:")

st.markdown("**Portafolio** — ¿qué lanzamos y qué pasa si el rival reacciona?")
p1, g1, p2, g2, p3, g3, p4 = st.columns([4, 0.6, 4, 0.6, 4, 0.6, 4])
paso(p1, "viabilidad.py", "3. Viabilidad", "¿La categoría cumple los 7 criterios?",
     "Sprint 2 · Sistema experto", ":material/rule:")
flecha(g1, "")
paso(p2, "que_lanzar.py", "4. Qué lanzar", "¿Qué referencias caben y dejan más utilidad?",
     "Sprint 3A · Algoritmo genético", ":material/inventory_2:")
flecha(g2, "")
paso(p3, "competidor.py", "5. Competidor", "¿Y si un rival entra con un producto parecido?",
     "Sprint 3B · Teoría de juegos", ":material/swords:")
flecha(g3, "")
paso(p4, "desempate_difuso.py", "6. Desempate difuso", "¿Cuál elegimos entre portafolios empatados?",
     "Sprint 4 · Lógica difusa", ":material/blur_on:")

st.caption(
    "Nota honesta: hoy la cadena de portafolio no está conectada del todo. El sistema experto evalúa "
    "3 *categorías* (aseo, Alquería, bebidas) y el algoritmo genético parte de 8 *referencias Riovalle* "
    "que se suponen viables. El Sprint 4 busca cerrar ese hueco con una nota difusa por referencia."
)

# =============================================================================
# LÍNEA DE TIEMPO
# =============================================================================
st.subheader("Los sprints del semestre")
SPRINTS = [
    ("Sprint 1", "Búsqueda A*", "Ruta óptima entre la bodega, los clientes y la plataforma.", "Completado", "green"),
    ("Sprint 2", "Sistemas expertos", "Quién entra en la ruta y si una categoría es viable.", "Completado", "green"),
    ("Sprint 3", "Algoritmo genético + teoría de juegos", "Qué lanzar y cómo protegerse de un rival.", "Completado", "green"),
    ("Sprint 4", "Lógica difusa", "Nota de viabilidad 0–100 y desempate de portafolios.", "En diseño", "orange"),
]
for columna, (nombre, tecnica, descripcion, estado, color) in zip(st.columns(4), SPRINTS):
    with columna.container(border=True, height="stretch"):
        st.badge(estado, color=color)
        st.markdown(f"**{nombre}** · {tecnica}")
        st.caption(descripcion)

# =============================================================================
# EQUIPO
# =============================================================================
st.subheader("Equipo")
st.markdown(
    "**Jacobo Argote, Andrés Cardona, Miguel Valencia y Juan José Gil**  \n"
    "Fundamentos de Inteligencia Artificial — Universidad EIA"
)
st.markdown(
    '<p class="mm-nota">Código desarrollado con apoyo de Claude. La lógica de cada algoritmo es la '
    "de los notebooks de clase del equipo, portada sin cambios; las pruebas automáticas verifican que "
    "los resultados sean idénticos.</p>",
    unsafe_allow_html=True,
)
