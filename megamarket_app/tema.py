"""Paleta de marca y CSS mínimo de la app (SPEC §4.4).

Junto con `.streamlit/config.toml`, este es el ÚNICO lugar donde se
definen colores. Cambiar la marca = editar esos dos archivos.
"""

import streamlit as st

# --- Colores de marca (leídos de megamarket.com.co) ---
PALETA = {
    "azul_noche": "#001B33",      # encabezado/hero, barra lateral, títulos
    "azul_rey": "#2E448D",        # primaryColor: botones, enlaces, activos
    "azul_medio": "#0F487A",      # series secundarias de gráficas, hover
    "amarillo_globo": "#F2B705",  # estimado del logo: acento puntual, nunca texto sobre blanco
    "texto": "#212529",
    "gris": "#636363",            # texto secundario, leyendas, notas
    "fondo_suave": "#F4F6F9",     # tarjetas
    "borde": "#E3E7EE",
    "blanco": "#FFFFFF",
}

# --- Colores semánticos (no son de marca: solo para significado) ---
SEMANTICOS = {
    "incluir": "#16A34A",     # incluir / viable / mejora
    "excluir": "#DC2626",     # excluir / veto / empeora
    "advertencia": "#F59E0B", # prioridad media / advertencia
}

# Sprint 3: un color por criterio del AG (consistente con los notebooks)
CRITERIO_AG = {
    "esperada": PALETA["azul_rey"],
    "peor_caso": "#EB6834",   # naranja Minimax
}

# Sprint 4: etiquetas difusas (los colores del notebook de clase)
DIFUSO = {
    "baja": "#64748B",
    "media": "#F59E0B",
    "alta": "#16A34A",
}

# Prioridad del sistema experto de logística (para el mapa y las tarjetas)
PRIORIDAD = {
    "ALTA": PALETA["azul_rey"],
    "MEDIA": SEMANTICOS["advertencia"],
    "BAJA": PALETA["gris"],
    "NORMAL": PALETA["azul_medio"],
}


def aplicar_css():
    """Inyecta el CSS mínimo de la app (chips, tarjetas, hero, pie).

    No pelea contra Streamlit: solo define clases propias que usan los
    componentes de `componentes.py`.
    """
    p = PALETA
    st.markdown(
        f"""
        <style>
        .mm-chip {{
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            background: {p["azul_noche"]};
            color: {p["blanco"]};
            font-size: 0.78rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            margin-bottom: 0.4rem;
        }}
        .mm-chip .mm-chip-punto {{
            display: inline-block;
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background: {p["amarillo_globo"]};
            margin-right: 0.45rem;
            vertical-align: middle;
        }}
        .mm-titulo {{
            color: {p["azul_noche"]};
            font-weight: 700;
            font-size: 2rem;
            line-height: 1.2;
            margin: 0.2rem 0 0.6rem 0;
        }}
        .mm-problema {{
            color: {p["texto"]};
            font-size: 1rem;
            max-width: 52rem;
            margin-bottom: 1rem;
        }}
        .mm-tarjeta {{
            background: {p["fondo_suave"]};
            border: 1px solid {p["borde"]};
            border-radius: 0.6rem;
            padding: 1rem 1.2rem;
        }}
        .mm-hero {{
            background: {p["azul_noche"]};
            color: {p["blanco"]};
            border-radius: 0.8rem;
            padding: 2rem 2rem 1.6rem 2rem;
            margin-bottom: 1.5rem;
        }}
        .mm-hero img {{
            max-width: 260px;
            width: 60%;
            margin-bottom: 1rem;
        }}
        .mm-hero p {{
            color: {p["blanco"]};
            font-size: 1.05rem;
            margin: 0;
        }}
        .mm-nota {{
            color: {p["gris"]};
            font-size: 0.85rem;
        }}
        .mm-pie {{
            border-top: 1px solid {p["borde"]};
            margin-top: 3rem;
            padding-top: 0.8rem;
            color: {p["gris"]};
            font-size: 0.8rem;
            text-align: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
