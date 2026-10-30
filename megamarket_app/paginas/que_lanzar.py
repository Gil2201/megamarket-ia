"""Página 4 — Qué lanzar (Sprint 3A · algoritmo genético)."""

import pandas as pd
import streamlit as st

from megamarket import genetico
from megamarket.datos import CANDIDATOS, ESPACIO_BODEGA_TOTAL, PRESUPUESTO_TOTAL, SEMILLA
from megamarket_app import componentes, formato, graficas
from megamarket_app.azar import CANDADO_AZAR
from megamarket_app.candidatos_ui import (
    MAX_CANDIDATOS,
    MIN_CANDIDATOS,
    candidatos_a_df,
    como_tupla,
    desde_tupla,
    df_a_candidatos,
    validar_candidatos,
)
from megamarket_app.tema import CRITERIO_AG

CLAVE_EDITOR = "editor_candidatos"


@st.cache_data(show_spinner="Revisando todas las combinaciones…")
def fuerza_bruta_cacheada(candidatos_tupla, presupuesto, espacio):
    return genetico.validar_con_fuerza_bruta(desde_tupla(candidatos_tupla), presupuesto, espacio)


def fila_portafolio(individuo, candidatos):
    return {
        "Productos": ", ".join(n.replace(" Riovalle", "") for n in genetico.nombre_incluidos(individuo, candidatos)),
        "Costo": formato.cop(genetico.costo_total(individuo, candidatos)),
        "Espacio": genetico.espacio_total(individuo, candidatos),
        "Utilidad anual": formato.cop(genetico.utilidad_total(individuo, candidatos)),
    }


if "candidatos_df" not in st.session_state:
    st.session_state["candidatos_df"] = candidatos_a_df(st.session_state["candidatos"])

componentes.encabezado_pagina(
    "¿Qué referencias lanzamos con el presupuesto y la bodega que tenemos?",
    "Sprint 3A · Algoritmo genético",
    "Hay 8 referencias Riovalle candidatas, pero el presupuesto y el espacio de bodega no "
    "alcanzan para todas. Con 2⁸ = 256 combinaciones posibles, un algoritmo genético busca "
    "la que deja más utilidad sin pasarse de los límites, y la fuerza bruta lo comprueba.",
)

# =============================================================================
# DATOS DE ENTRADA
# =============================================================================
st.subheader("Candidatos")
st.caption(f"Puedes editar, agregar o quitar candidatos (entre {MIN_CANDIDATOS} y {MAX_CANDIDATOS}). "
           "Cada fila es un gen del cromosoma, en este mismo orden.")

candidatos_editados = st.data_editor(
    st.session_state["candidatos_df"],
    key=CLAVE_EDITOR,
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_config={
        "producto": st.column_config.TextColumn("Producto", required=True),
        "costo_lanzamiento": st.column_config.NumberColumn(
            "Costo de lanzamiento (COP)", min_value=1, step=1_000_000, format="localized", required=True),
        "espacio_bodega": st.column_config.NumberColumn(
            "Espacio (posiciones)", min_value=0, step=1, format="%d", required=True),
        "utilidad_esperada_anual": st.column_config.NumberColumn(
            "Utilidad esperada anual (COP)", min_value=0, step=1_000_000, format="localized", required=True),
    },
)
st.session_state["candidatos_df"] = candidatos_editados

errores = validar_candidatos(candidatos_editados)
for error in errores:
    st.error(error, icon=":material/error:")
if not errores:
    st.session_state["candidatos"] = df_a_candidatos(candidatos_editados.dropna(how="all"))
candidatos = st.session_state["candidatos"]

col_restricciones, col_parametros = st.columns(2, gap="large")
with col_restricciones:
    st.markdown("**Restricciones del semestre**")
    restricciones = st.session_state["restricciones"]
    presupuesto = st.number_input("Presupuesto (COP)", min_value=1_000_000, step=5_000_000,
                                  value=restricciones["presupuesto"], format="%d")
    st.caption(f"= {formato.cop(presupuesto)}")
    espacio = st.number_input("Espacio de bodega (posiciones)", min_value=1, step=1,
                              value=restricciones["espacio"])
    st.session_state["restricciones"] = {"presupuesto": int(presupuesto), "espacio": int(espacio)}
with col_parametros:
    st.markdown("**Parámetros del algoritmo genético**")
    p1, p2 = st.columns(2)
    tamano_poblacion = p1.number_input("Población", min_value=2, max_value=200, value=10, step=1)
    generaciones = p2.number_input("Generaciones", min_value=1, max_value=300, value=15, step=1)
    probabilidad_mutacion = p1.number_input("Prob. de mutación", min_value=0.0, max_value=1.0,
                                            value=0.10, step=0.05, format="%.2f")
    elitismo = p2.number_input("Elitismo", min_value=0, max_value=int(tamano_poblacion) - 1, value=1, step=1)
    semilla = p1.number_input("Semilla", min_value=0, value=SEMILLA, step=1)

if st.button("Restaurar datos originales", icon=":material/restart_alt:"):
    st.session_state["candidatos"] = dict(CANDIDATOS)
    st.session_state["candidatos_df"] = candidatos_a_df(CANDIDATOS)
    st.session_state["restricciones"] = {"presupuesto": PRESUPUESTO_TOTAL, "espacio": ESPACIO_BODEGA_TOTAL}
    st.session_state.pop(CLAVE_EDITOR, None)
    st.session_state["resultado_ag"] = None
    st.rerun()

with st.expander("Mapa de candidatos: costo vs. utilidad", icon=":material/bubble_chart:", expanded=True):
    elegidos_previos = ()
    if st.session_state["resultado_ag"] and st.session_state["resultado_ag"]["candidatos"] == candidatos:
        elegidos_previos = genetico.nombre_incluidos(st.session_state["resultado_ag"]["mejor"], candidatos)
    st.plotly_chart(graficas.burbujas_candidatos(candidatos, elegidos_previos), width="stretch")
    st.caption("Tamaño de la burbuja = espacio de bodega. En azul rey, los elegidos por el AG.")

ejecutar = st.button("Ejecutar algoritmo genético", type="primary", icon=":material/play_arrow:",
                     disabled=bool(errores))

if ejecutar:
    with CANDADO_AZAR:
        mejor, historial = genetico.ejecutar_experimento(
            int(tamano_poblacion), int(generaciones), float(probabilidad_mutacion), int(elitismo),
            int(semilla), candidatos, int(presupuesto), int(espacio),
        )
    st.session_state["resultado_ag"] = {
        "mejor": mejor, "historial": historial, "candidatos": dict(candidatos),
        "presupuesto": int(presupuesto), "espacio": int(espacio),
    }
    st.rerun()

# =============================================================================
# RESULTADO
# =============================================================================
resultado = st.session_state["resultado_ag"]
if not resultado:
    st.info("Ajusta los datos si quieres y pulsa **Ejecutar algoritmo genético**.", icon=":material/info:")
else:
    cand_r, pres_r, esp_r = resultado["candidatos"], resultado["presupuesto"], resultado["espacio"]
    if (cand_r, pres_r, esp_r) != (candidatos, int(presupuesto), int(espacio)):
        st.warning("Cambiaste los datos después de ejecutar: el resultado de abajo es de la corrida anterior.",
                   icon=":material/history:")
    mejor = resultado["mejor"]
    st.subheader("Portafolio elegido por el AG")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Utilidad anual", formato.cop_millones(genetico.utilidad_total(mejor, cand_r)))
    m2.metric("Costo usado", formato.cop_millones(genetico.costo_total(mejor, cand_r)),
              help=f"Presupuesto: {formato.cop(pres_r)}")
    m3.metric("Espacio usado", f"{genetico.espacio_total(mejor, cand_r)} de {esp_r}")
    m4.metric("Productos", len(genetico.nombre_incluidos(mejor, cand_r)))
    for nombre in genetico.nombre_incluidos(mejor, cand_r):
        st.badge(nombre, icon=":material/inventory_2:", color="blue")

    # --- Validación con fuerza bruta ---
    st.subheader("Validación con fuerza bruta")
    fb = fuerza_bruta_cacheada(como_tupla(cand_r), pres_r, esp_r)
    optimos = fb["optimos"]
    llega = genetico.utilidad_total(mejor, cand_r) == fb["mejor_utilidad_fb"]
    f1, f2, f3 = st.columns(3)
    f1.metric("Combinaciones revisadas", f"{2 ** len(cand_r):,}".replace(",", "."))
    f2.metric("Portafolios válidos", len(fb["validas"]))
    f3.metric("Utilidad óptima", formato.cop_millones(fb["mejor_utilidad_fb"]))
    if llega:
        st.success("El AG llegó a la utilidad óptima que confirma la fuerza bruta.", icon=":material/check_circle:")
    else:
        st.warning("El AG no llegó al óptimo en esta corrida. Prueba más generaciones, más población u otra semilla.",
                   icon=":material/warning:")
    st.dataframe(pd.DataFrame([fila_portafolio(o, cand_r) for o in optimos]), hide_index=True, width="stretch")

    st.session_state["empates"] = {
        **(st.session_state.get("empates") or {}),
        "esperada": [genetico.nombre_incluidos(o, cand_r) for o in optimos],
    }
    if len(optimos) > 1:
        st.warning(f"Hay **{len(optimos)} portafolios con la misma utilidad**: el AG se queda con el primero "
                   "que encuentra. Elegir entre ellos con un criterio explicable es el objetivo del Sprint 4.",
                   icon=":material/balance:")
        st.page_link("megamarket_app/paginas/desempate_difuso.py", label="Ver desempate difuso (Sprint 4)",
                     icon=":material/blur_on:")
    st.page_link("megamarket_app/paginas/competidor.py", label="¿Y si un competidor reacciona? →",
                 icon=":material/swords:")

    # =========================================================================
    # CÓMO RAZONÓ EL ALGORITMO
    # =========================================================================
    st.subheader("Cómo razonó el algoritmo")
    st.markdown(
        "Cada portafolio es un **cromosoma de bits** (1 = se lanza). En cada generación: se ordena la "
        "población por **fitness = utilidad + 1**, se conserva la élite, se eligen padres por **ruleta**, "
        "se cruzan en **un punto**, se **mutan** (voltear un gen) y, si el hijo no cabe, se **repara** "
        "retirando el producto con peor utilidad por peso invertido."
    )
    historial = resultado["historial"]
    g1, g2 = st.columns([3, 2])
    with g1:
        st.markdown("**Calidad de la población**")
        st.plotly_chart(graficas.evolucion_ag(historial, "Mejor utilidad", "Utilidad promedio",
                                              CRITERIO_AG["esperada"], "Mejor utilidad", "Utilidad promedio"),
                        width="stretch")
    with g2:
        st.markdown("**Diversidad**")
        st.plotly_chart(graficas.diversidad(historial), width="stretch")
    with st.expander("Tabla generación por generación"):
        st.dataframe(historial, hide_index=True, width="stretch",
                     column_config={"Mejor utilidad": st.column_config.NumberColumn(format="localized"),
                                    "Utilidad promedio": st.column_config.NumberColumn(format="localized")})

componentes.ver_codigo([
    genetico.reparar_portafolio, genetico.calcular_fitness, genetico.seleccionar_por_ruleta,
    genetico.cruzar, genetico.mutar, genetico.algoritmo_genetico_portafolio,
])
componentes.supuestos_y_limites([
    "Los costos, espacios y utilidades son **ficticios**: muestran la lógica de selección, no cifras reales de MegaMarket.",
    "Se asume que los 8 candidatos ya pasaron los 7 criterios del Sprint 2; esa evaluación no está en los datos.",
    "El AG no garantiza el óptimo: por eso se valida con fuerza bruta. Con 8 candidatos la fuerza bruta basta; "
    "el valor del AG es el método, que sigue funcionando cuando los candidatos son decenas.",
    "Con semilla 42, población 10 y 15 generaciones el resultado es idéntico al del notebook.",
])
