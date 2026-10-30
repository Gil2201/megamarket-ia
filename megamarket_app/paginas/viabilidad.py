"""Página 3 — Viabilidad de productos (Sprint 2 · sistema experto de portafolio)."""

import pandas as pd
import streamlit as st

from megamarket.sistema_experto_portafolio import (
    BASE_CONOCIMIENTO_PORTAFOLIO,
    CRITERIOS_DETALLE,
    CRITERIOS_NOMBRES,
    construir_memoria_trabajo_portafolio,
    evaluar_producto,
    leer_memoria_portafolio,
    motor_inferencia_portafolio,
)
from megamarket.sistema_experto_logistica import a_booleano
from megamarket_app import componentes

CLAVE_EDITOR = "editor_memoria_portafolio"
CRITERIOS = list(CRITERIOS_NOMBRES)


def csv_a_editor(df_csv):
    """CSV ("Sí"/"No") -> tabla con casillas."""
    df = df_csv[["producto"] + CRITERIOS].copy()
    for c in CRITERIOS:
        df[c] = df[c].map(a_booleano)
    return df.reset_index(drop=True)


def editor_a_csv(df_editor):
    """Tabla con casillas -> mismo formato del CSV, para el motor."""
    df = df_editor.copy()
    for c in CRITERIOS:
        df[c] = df[c].map(lambda v: "Sí" if bool(v) else "No")
    return df


if "memoria_portafolio" not in st.session_state:
    st.session_state["memoria_portafolio"] = csv_a_editor(leer_memoria_portafolio())

componentes.encabezado_pagina(
    "¿La nueva categoría cumple los criterios del gerente?",
    "Sprint 2 · Sistema experto",
    "Antes de distribuir una categoría nueva, MegaMarket revisa siete criterios (C1–C7). "
    "Es un chequeo de «todas las luces en verde»: basta con que falle uno para descartarla. "
    "No compara categorías entre sí ni mide qué tanto cumple cada una.",
)

tab_clasico, tab_difuso = st.tabs(["Sistema experto (Sprint 2)", "Versión difusa (Sprint 4)"])

with tab_difuso:
    componentes.proximamente(
        "Próximamente. Con lógica difusa cada categoría recibirá una nota de 0 a 100 en vez de "
        "un Sí/No, y no todos los criterios pesarán igual (docs/SPRINT4_LOGICA_DIFUSA.md)."
    )

with tab_clasico:
    # =========================================================================
    # DATOS DE ENTRADA
    # =========================================================================
    st.subheader("Memoria de trabajo: categorías candidatas")
    st.caption("Marca qué criterios cumple cada categoría. Pasa el cursor por el encabezado para ver el criterio completo.")

    memoria_editada = st.data_editor(
        st.session_state["memoria_portafolio"],
        key=CLAVE_EDITOR,
        num_rows="fixed",
        hide_index=True,
        width="stretch",
        disabled=["producto"],
        column_config={
            "producto": st.column_config.TextColumn("Categoría", pinned=True),
            **{c: st.column_config.CheckboxColumn(c, help=f"{CRITERIOS_NOMBRES[c]}: {CRITERIOS_DETALLE[c]}")
               for c in CRITERIOS},
        },
    )
    st.session_state["memoria_portafolio"] = memoria_editada

    if st.button("Restaurar datos originales", icon=":material/restart_alt:"):
        st.session_state["memoria_portafolio"] = csv_a_editor(leer_memoria_portafolio())
        st.session_state.pop(CLAVE_EDITOR, None)
        st.rerun()

    # =========================================================================
    # RESULTADO
    # =========================================================================
    MEMORIA_TRABAJO_PORTAFOLIO = construir_memoria_trabajo_portafolio(editor_a_csv(memoria_editada))
    resultados = {
        producto: evaluar_producto(producto, MEMORIA_TRABAJO_PORTAFOLIO, CRITERIOS_NOMBRES, CRITERIOS_DETALLE)
        for producto in MEMORIA_TRABAJO_PORTAFOLIO
    }

    st.subheader("Veredicto")
    viables = [p for p, r in resultados.items() if r["viable"]]
    m1, m2 = st.columns(2)
    m1.metric("Categorías viables", f"{len(viables)} de {len(resultados)}")
    m2.metric("Criterios incumplidos en total", sum(len(r["incumplidos"]) for r in resultados.values()))

    columnas = st.columns(len(resultados))
    for columna, (producto, resultado) in zip(columnas, resultados.items()):
        with columna.container(border=True, height="stretch"):
            st.markdown(f"**{producto}**")
            if resultado["viable"]:
                st.badge("Viable", icon=":material/check_circle:", color="green")
            else:
                st.badge("No viable", icon=":material/cancel:", color="red")
            for criterio, datos in resultado["evaluacion"].items():
                marca = ":green[●]" if datos["cumple"] else ":red[●]"
                texto = CRITERIOS_NOMBRES[criterio]
                st.markdown(f"{marca} **{criterio}** {texto if datos['cumple'] else f':red[{texto}]'}")

    st.markdown("**Resumen comparativo**")
    resumen = pd.DataFrame([
        {"Categoría": p, **{c: "✅" if r["evaluacion"][c]["cumple"] else "❌" for c in CRITERIOS},
         "Veredicto": "VIABLE" if r["viable"] else "NO VIABLE"}
        for p, r in resultados.items()
    ])
    st.dataframe(resumen, hide_index=True, width="stretch")

    # =========================================================================
    # CÓMO RAZONÓ EL ALGORITMO
    # =========================================================================
    st.subheader("Cómo razonó el algoritmo")
    st.markdown(
        "Aquí no hay jerarquía de vetos ni prioridades: los 7 criterios son requisitos conjuntos. "
        "Una categoría es **VIABLE** solo si cumple **C1 Y C2 Y … Y C7**. Si falla una sola, no entra, "
        "y el motor dice cuál falló para poder sustentar el «por qué»."
    )
    st.dataframe(
        pd.DataFrame([{"Criterio": c, "Nombre": CRITERIOS_NOMBRES[c], "SI … ENTONCES cumple": CRITERIOS_DETALLE[c]}
                      for c in CRITERIOS]),
        hide_index=True, width="stretch",
    )

    componentes.ver_codigo([motor_inferencia_portafolio, evaluar_producto])
    componentes.supuestos_y_limites([
        "Quien llena la memoria de trabajo ya compara el dato real contra el umbral y marca Sí/No "
        f"(vida útil ≥ {BASE_CONOCIMIENTO_PORTAFOLIO['umbrales']['vida_util_minima_meses']} meses, "
        f"margen ≥ {BASE_CONOCIMIENTO_PORTAFOLIO['umbrales']['margen_minimo_pct']} %).",
        "El margen mínimo de 12 % es un **supuesto de política interna**: el gerente pidió «buena rentabilidad» sin un número.",
        "Todos los criterios pesan lo mismo y basta uno para descartar. El Sprint 4 (lógica difusa) propone una nota graduada.",
        "**Hueco conocido:** este sistema evalúa 3 *categorías* (aseo, Alquería, bebidas), mientras que la "
        "página 4 parte de 8 *referencias Riovalle* que se suponen viables; esa evaluación no está en los datos.",
    ])
