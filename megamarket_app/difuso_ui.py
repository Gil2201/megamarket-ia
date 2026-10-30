"""Piezas de interfaz para mostrar cómo razona un sistema difuso (páginas 3 y 6)."""

from html import escape

import streamlit as st

from megamarket import difuso
from megamarket_app import formato, graficas
from megamarket_app.tema import DIFUSO, PALETA


def color_nota(valor):
    """Color de la etiqueta dominante de una nota 0–100 (baja / media / alta)."""
    return DIFUSO[difuso.etiqueta_dominante(valor)]


def diagrama_jerarquia(resultado, valores_entrada):
    """Grafo (DOT) de la jerarquía de 5 sistemas con el valor de cada nodo."""
    nodos = resultado["nodos"]
    p = PALETA

    def caja(nombre, valor, destacar=False):
        fondo = p["azul_noche"] if destacar else p["fondo_suave"]
        texto = p["blanco"] if destacar else p["texto"]
        borde = color_nota(valor)
        return (f'[label="{nombre}\\n{formato.decimal(valor)}", style="filled,rounded", shape=box, fillcolor="{fondo}", '
                f'fontcolor="{texto}", color="{borde}", penwidth=3, fontname="Montserrat"]')

    def entrada(nombre, valor):
        return (f'[label="{nombre}\\n{valor:g}", shape=plaintext, fontcolor="{p["gris"]}", '
                f'fontname="Montserrat", fontsize=11]')

    v = valores_entrada
    return f"""
    digraph {{
        rankdir=LR; bgcolor="transparent"; nodesep=0.25; ranksep=0.45;
        edge [color="{p['gris']}", arrowsize=0.7];
        margen {entrada("Margen %", v["margen_pct"])};
        comp {entrada("Complementariedad", v["complementariedad"])};
        vida {entrada("Vida útil (meses)", v["vida_util_meses"])};
        facil {entrada("Facilidad operativa", v["facilidad_operativa"])};
        afin {entrada("Afinidad", v["afinidad"])};
        cal {entrada("Calidad", v["calidad_presentacion"])};
        S1 {caja("S1 · Atractivo comercial", nodos["S1"]["valor"])};
        S2 {caja("S2 · Solidez operativa", nodos["S2"]["valor"])};
        S3 {caja("S3 · Encaje con la marca", nodos["S3"]["valor"])};
        S4 {caja("S4 · Fortaleza del negocio", nodos["S4"]["valor"])};
        S5 {caja("S5 · NOTA DE VIABILIDAD", nodos["S5"]["valor"], True)};
        margen -> S1; comp -> S1; vida -> S2; facil -> S2; afin -> S3; cal -> S3;
        S1 -> S4; S2 -> S4; S4 -> S5; S3 -> S5;
    }}
    """


def tabla_reglas(sistema, detalle):
    """Tabla 3x3 de reglas: salida de cada celda y su grado de activación (0 = apagada)."""
    etiquetas_1 = list(sistema["entrada_1"]["conjuntos"])
    etiquetas_2 = list(sistema["entrada_2"]["conjuntos"])
    activacion = {(d["entrada_1"], d["entrada_2"]): d for d in detalle}
    p = PALETA
    filas = ""
    for e1 in etiquetas_1:
        filas += f'<tr><th style="text-align:left;padding:.45rem .6rem;color:{p["gris"]}">{escape(e1)}</th>'
        for e2 in etiquetas_2:
            d = activacion[(e1, e2)]
            activa = d["activación"] > 0
            color = DIFUSO[d["salida"]]
            fondo = p["fondo_suave"] if activa else p["blanco"]
            borde = f"2px solid {p['azul_rey']}" if activa else f"1px solid {p['borde']}"
            opacidad = "1" if activa else ".45"
            filas += (f'<td style="border:{borde};background:{fondo};padding:.45rem .6rem;text-align:center;opacity:{opacidad}">'
                      f'<span style="color:{color};font-weight:700">{escape(d["salida"])}</span>'
                      f'<div style="font-size:.75rem;color:{p["gris"]}">μ = {formato.decimal(d["activación"], 2)}</div></td>')
        filas += "</tr>"
    encabezado = "".join(f'<th style="padding:.45rem .6rem;color:{p["gris"]}">{escape(e)}</th>' for e in etiquetas_2)
    titulo_1 = escape(sistema["entrada_1"]["nombre"])
    titulo_2 = escape(sistema["entrada_2"]["nombre"])
    st.markdown(
        f'<div style="font-size:.8rem;color:{p["gris"]};margin-bottom:.2rem">Filas: {titulo_1} · Columnas: {titulo_2}</div>'
        f'<table style="border-collapse:collapse;width:100%;max-width:520px">'
        f"<tr><th></th>{encabezado}</tr>{filas}</table>",
        unsafe_allow_html=True,
    )


def detalle_sistema(sistema, resultado, x1, x2):
    """Las cuatro etapas Mamdani de un sistema: fuzzificación, reglas, agregación y centroide."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**1. Fuzzificación: {sistema['entrada_1']['nombre']}**")
        st.plotly_chart(graficas.funciones_pertenencia(sistema["entrada_1"], x1), width="stretch")
        st.caption("μ: " + " · ".join(f"{k} {formato.decimal(v, 2)}" for k, v in resultado["grados_1"].items()))
    with c2:
        st.markdown(f"**1. Fuzzificación: {sistema['entrada_2']['nombre']}**")
        st.plotly_chart(graficas.funciones_pertenencia(sistema["entrada_2"], x2), width="stretch")
        st.caption("μ: " + " · ".join(f"{k} {formato.decimal(v, 2)}" for k, v in resultado["grados_2"].items()))
    c3, c4 = st.columns([1, 1.3])
    with c3:
        activas = sum(d["activación"] > 0 for d in resultado["detalle"])
        st.markdown(f"**2. Reglas** — {activas} de 9 activas (Y = mínimo)")
        tabla_reglas(sistema, resultado["detalle"])
    with c4:
        st.markdown("**3–4. Agregación (máximo) y centroide**")
        st.plotly_chart(graficas.salida_agregada(sistema["salida"], resultado["agregado"], resultado["valor"]),
                        width="stretch")
