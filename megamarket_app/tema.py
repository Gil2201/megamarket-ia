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
    "amarillo_globo": "#EDC443",  # medido en el PNG del logo: acento puntual, nunca texto sobre blanco
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
        @media (max-width: 640px) {{
            .mm-titulo {{ font-size: 1.45rem; }}
            .mm-hero {{ padding: 1.4rem 1.2rem 1.2rem 1.2rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def aplicar_css_inicio():
    """CSS de la página de Inicio (landing): hero, banda de cifras, tarjetas bento.

    Referencias de estilo: stripe.com (titular en dos tonos, tarjetas con
    miniaturas) y puygroup.com (botones píldora, banda azul con cifras grandes,
    tarjetas divididas oscuro/claro). Único lugar con degradados: la
    decoración del hero.
    """
    p = PALETA
    st.markdown(
        f"""
        <style>
        .mm-pildora {{
            display: inline-flex; align-items: center; gap: .5rem;
            padding: .3rem .85rem; border-radius: 999px;
            background: {p["blanco"]}; border: 1px solid {p["borde"]};
            color: {p["gris"]}; font-size: .8rem; font-weight: 500;
        }}
        .mm-pildora b {{ color: {p["azul_noche"]}; font-weight: 600; }}
        .mm-pildora .punto {{ width: .5rem; height: .5rem; border-radius: 50%; background: {p["amarillo_globo"]}; }}
        .mm-titular {{
            font-size: clamp(2rem, 3.3vw, 3.05rem); line-height: 1.08; font-weight: 700;
            letter-spacing: -0.035em; color: {p["azul_noche"]}; margin: 1.1rem 0 1.1rem 0;
        }}
        .mm-titular span {{ color: {p["azul_rey"]}; }}
        .mm-bajada {{ font-size: 1.12rem; line-height: 1.6; color: {p["gris"]}; max-width: 34rem; }}
        .mm-bajada b {{ color: {p["texto"]}; font-weight: 600; }}

        /* Botones píldora (st.page_link dentro de contenedores con key) */
        .st-key-cta_primario a, .st-key-cta_secundario a {{
            border-radius: 999px !important; padding: .55rem 1.25rem !important;
            font-weight: 600 !important; justify-content: center;
            transition: transform .15s ease, box-shadow .15s ease;
        }}
        .st-key-cta_primario a {{ background: {p["azul_rey"]} !important; }}
        .st-key-cta_primario a, .st-key-cta_primario a * {{ color: {p["blanco"]} !important; }}
        .st-key-cta_primario a:hover {{ transform: translateY(-1px); box-shadow: 0 8px 20px rgba(46,68,141,.28); }}
        .st-key-cta_secundario a {{ border: 1.5px solid {p["azul_noche"]} !important; background: {p["blanco"]} !important; }}
        .st-key-cta_secundario a, .st-key-cta_secundario a * {{ color: {p["azul_noche"]} !important; }}
        .st-key-cta_secundario a:hover {{ transform: translateY(-1px); }}

        /* Ilustración del hero */
        .mm-escena {{
            position: relative; border-radius: 1.4rem; overflow: hidden; min-height: 380px;
            background:
              radial-gradient(60% 55% at 85% 15%, rgba(237,196,67,.38), transparent 70%),
              radial-gradient(55% 60% at 10% 90%, rgba(46,68,141,.30), transparent 70%),
              radial-gradient(70% 70% at 60% 60%, rgba(15,72,122,.16), transparent 75%),
              {p["fondo_suave"]};
            border: 1px solid {p["borde"]};
        }}
        .mm-escena svg {{ width: 100%; height: auto; display: block; }}
        .mm-flotante {{
            position: absolute; background: {p["blanco"]}; border-radius: .9rem;
            box-shadow: 0 14px 34px rgba(0,27,51,.14); padding: .7rem .9rem; font-size: .78rem;
            color: {p["gris"]}; border: 1px solid {p["borde"]};
            animation: mm-flotar 6s ease-in-out infinite;
        }}
        .mm-flotante b {{ display: block; color: {p["azul_noche"]}; font-size: 1.15rem; font-weight: 700; }}
        .mm-flotante .barra {{ height: .4rem; border-radius: 999px; background: {p["borde"]}; margin-top: .35rem; }}
        .mm-flotante .barra i {{ display: block; height: 100%; border-radius: 999px; background: {SEMANTICOS["incluir"]}; }}
        @keyframes mm-flotar {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
        .mm-ruta-animada {{ stroke-dasharray: 8 900; animation: mm-recorrer 7s linear infinite; }}
        @keyframes mm-recorrer {{ from {{ stroke-dashoffset: 0; }} to {{ stroke-dashoffset: -908; }} }}

        /* Banda azul con cifras (puygroup) */
        .mm-banda {{
            background: {p["azul_rey"]}; border-radius: 1.4rem; padding: 2.2rem 2rem; margin: 2.5rem 0 1rem 0;
            display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 1.6rem;
        }}
        .mm-cifra b {{
            display: block; color: {p["blanco"]}; font-size: clamp(2rem, 3.6vw, 3rem);
            font-weight: 600; letter-spacing: -0.03em; line-height: 1.05;
        }}
        .mm-cifra span {{ color: rgba(255,255,255,.78); font-size: .88rem; line-height: 1.4; display: block; margin-top: .5rem; }}
        .mm-cifra small {{ color: {p["amarillo_globo"]}; font-size: .72rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }}

        /* Secciones */
        .mm-seccion {{ font-size: clamp(1.6rem, 3vw, 2.3rem); font-weight: 700; letter-spacing: -0.03em;
                       color: {p["azul_noche"]}; line-height: 1.15; margin: 3rem 0 .4rem 0; }}
        .mm-seccion span {{ color: {p["gris"]}; font-weight: 500; }}

        /* Tarjetas bento (stripe) */
        div[class*="st-key-bento_"] {{
            background: {p["fondo_suave"]}; border-radius: 1.2rem; padding: 1.1rem 1.2rem 1rem 1.2rem;
            border: 1px solid {p["borde"]}; transition: transform .18s ease, box-shadow .18s ease;
        }}
        div[class*="st-key-bento_"]:hover {{ transform: translateY(-3px); box-shadow: 0 16px 34px rgba(0,27,51,.10); }}
        .mm-bento-visual {{ background: {p["blanco"]}; border-radius: .8rem; border: 1px solid {p["borde"]};
                            height: 150px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
        .mm-bento-visual svg {{ width: 92%; height: 92%; }}
        .mm-bento-chip {{ font-size: .72rem; font-weight: 600; color: {p["azul_rey"]}; letter-spacing: .03em;
                          text-transform: uppercase; margin-top: .9rem; }}
        .mm-bento-titulo {{ font-size: 1.12rem; font-weight: 700; color: {p["azul_noche"]}; margin: .15rem 0 .25rem 0; }}
        .mm-bento-texto {{ font-size: .9rem; color: {p["gris"]}; line-height: 1.5; }}

        /* Sección dividida oscuro / claro (puygroup) */
        .mm-dividida {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        border-radius: 1.4rem; overflow: hidden; margin-top: 3rem; }}
        .mm-dividida .oscuro {{ background: {p["azul_noche"]}; padding: 2.4rem 2.2rem; }}
        .mm-dividida .oscuro h3 {{ color: {p["blanco"]}; font-size: 1.9rem; line-height: 1.15; letter-spacing: -0.02em; margin: 0 0 1rem 0; }}
        .mm-dividida .oscuro p {{ color: rgba(255,255,255,.75); font-size: 1rem; line-height: 1.6; }}
        .mm-dividida .claro {{ background: {p["fondo_suave"]}; padding: 1.6rem; display: flex; align-items: center; }}
        .mm-dividida .claro svg {{ width: 100%; height: auto; }}

        /* Línea de tiempo de sprints */
        .mm-linea {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1rem; margin-top: 1.2rem; }}
        .mm-hito {{ border-top: 3px solid {p["azul_rey"]}; padding-top: .9rem; }}
        .mm-hito.propuesta {{ border-top-color: {p["amarillo_globo"]}; }}
        .mm-hito small {{ color: {p["gris"]}; font-weight: 600; font-size: .75rem; letter-spacing: .04em; text-transform: uppercase; }}
        .mm-hito b {{ display: block; color: {p["azul_noche"]}; font-size: 1.05rem; margin: .2rem 0; }}
        .mm-hito span {{ color: {p["gris"]}; font-size: .88rem; line-height: 1.45; }}

        .mm-cierre {{ background: {p["fondo_suave"]}; border-radius: 1.4rem; padding: 2rem; margin-top: 3rem;
                      display: flex; flex-wrap: wrap; gap: 1.5rem; justify-content: space-between; align-items: center; }}
        .mm-cierre b {{ color: {p["azul_noche"]}; font-size: 1.1rem; }}
        .mm-cierre span {{ color: {p["gris"]}; font-size: .9rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )
