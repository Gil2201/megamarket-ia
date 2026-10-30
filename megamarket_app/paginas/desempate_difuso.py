"""Página 6 — Desempate difuso (Sprint 4 · 4B)."""

import pandas as pd
import streamlit as st

from megamarket import competidor, difuso
from megamarket.datos import K_ATAQUES
from megamarket_app import componentes, difuso_ui, formato
from megamarket_app.candidatos_ui import como_tupla, desde_tupla, erosion_para

CRITERIOS = {
    "esperada": "Utilidad esperada (página 4 · AG)",
    "peor_caso": "Peor caso con Minimax (página 5)",
}


@st.cache_data(show_spinner="Revisando todas las combinaciones…")
def validas_cacheadas(candidatos_tupla, presupuesto, espacio):
    cand = desde_tupla(candidatos_tupla)
    _, _, validas = competidor.fuerza_bruta(lambda ind: competidor.utilidad_total(ind, cand), cand, presupuesto, espacio)
    return validas


componentes.encabezado_pagina(
    "¿Cuál portafolio elegimos cuando hay empate?",
    "Sprint 4 · Lógica difusa",
    "El algoritmo genético encuentra varios portafolios con la misma utilidad y se queda con el primero "
    "que aparece. Con las variables que ya usa (utilidad, costo, espacio) no se desempata nada: hace "
    "falta información nueva. Un sistema difuso compara la **nota de viabilidad** de los productos "
    "(página 3) con su **exposición al competidor** (página 5).",
)

candidatos = st.session_state["candidatos"]
restricciones = st.session_state["restricciones"]
presupuesto, espacio = restricciones["presupuesto"], restricciones["espacio"]
erosion = erosion_para(candidatos, st.session_state["erosion"])
productos = st.session_state.get("productos_difusos") or difuso.construir_productos_difusos(difuso.leer_memoria_difusa())
notas = difuso.notas_de_productos(productos)

# =============================================================================
# DATOS DE ENTRADA
# =============================================================================
c1, c2 = st.columns([2, 1])
criterio = c1.segmented_control("¿Qué empate resolver?", list(CRITERIOS), default="esperada", required=True,
                                format_func=CRITERIOS.get)
tolerancia = c2.slider("Tolerancia de empate (%)", 0.0, 5.0, 0.0, 0.5, format="%.1f %%",
                       help="0 = solo empates exactos. 2 = portafolios a menos del 2 % del mejor valor.") / 100

if criterio == "esperada":
    valor = lambda ind: competidor.utilidad_total(ind, candidatos)
else:
    valor = lambda ind: competidor.utilidad_peor_caso(ind, erosion, K_ATAQUES, candidatos)

validas = validas_cacheadas(como_tupla(candidatos), presupuesto, espacio)
empatados = difuso.empates_con_tolerancia(validas, valor, tolerancia)
empatados.sort(key=lambda ind: -valor(ind))
nombres_empatados = [[n for n, g in zip(candidatos, ind) if g == 1] for ind in empatados]

sin_nota = sorted({p for ps in nombres_empatados for p in ps if notas.get(p) is None})
if sin_nota:
    st.warning(f"Estos productos no tienen nota difusa (no están en la página 3 o no tienen registro sanitario): "
               f"{', '.join(sin_nota)}. Los portafolios que los incluyen quedan fuera del desempate.",
               icon=":material/warning:")
comparables = [ps for ps in nombres_empatados if all(notas.get(p) is not None for p in ps)]

st.markdown(f"**{len(empatados)} portafolio(s)** a menos del {formato.pct(tolerancia)} del mejor valor "
            f"({formato.cop_millones(valor(empatados[0]))}).")

if len(comparables) < 2:
    st.info("No hay empate que resolver con estos datos. Sube la tolerancia o cambia el criterio.",
            icon=":material/info:")
    st.stop()

# =============================================================================
# RESULTADO
# =============================================================================
ranking = difuso.desempatar_portafolios(comparables, candidatos, erosion, notas, espacio)
st.session_state["desempate"] = {"criterio": criterio, "ganador": ranking[0]["productos"]}
ganador = ranking[0]

st.subheader("Portafolio elegido")
with st.container(border=True):
    st.markdown("**" + ", ".join(p.replace(" Riovalle", "") for p in ganador["productos"]) + "**")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Preferencia difusa", f"{formato.decimal(ganador['preferencia'])} / 100")
    g2.metric("Nota promedio", formato.decimal(ganador["nota_promedio"]))
    g3.metric("Exposición al rival", formato.pct(ganador["exposicion"] / 100))
    g4.metric("Holgura de bodega", f"{ganador['holgura']} pos.")
    st.caption(f"Decidió: **{ganador['criterio']}**.")

def fila(r):
    ind = tuple(1 if n in r["productos"] else 0 for n in candidatos)
    return {
        "Portafolio": ", ".join(p.replace(" Riovalle", "") for p in r["productos"]),
        "Utilidad esperada": formato.cop_millones(competidor.utilidad_total(ind, candidatos)),
        "Peor caso": formato.cop_millones(competidor.utilidad_peor_caso(ind, erosion, K_ATAQUES, candidatos)),
        "Nota promedio": round(r["nota_promedio"], 1),
        "Exposición %": round(r["exposicion"], 1),
        "Holgura": r["holgura"],
        "Preferencia": round(r["preferencia"], 1),
    }

st.dataframe(pd.DataFrame([fila(r) for r in ranking]), hide_index=True, width="stretch",
             column_config={"Preferencia": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f")})
if criterio == "peor_caso":
    st.caption("El notebook 3B desempataba con + 0,001 × utilidad esperada (gana la de mayor utilidad). "
               "Aquí el criterio es explícito y explicable.")

# =============================================================================
# CÓMO RAZONÓ
# =============================================================================
st.subheader("Cómo razonó el algoritmo")
st.markdown(
    "**Entradas.** `nota promedio` = Σ(nota × utilidad) / Σ utilidad de los productos del portafolio. "
    "`exposición` = Σ(utilidad × erosión) / Σ utilidad × 100: qué parte de la utilidad está en productos "
    "fáciles de copiar. **Regla general:** se prefiere nota alta y exposición baja. Si dos preferencias "
    f"quedan a menos de {str(difuso.DIFERENCIA_MINIMA).replace('.', ',')} puntos (el ruido propio del método), "
    "se consideran empatadas y gana la mayor holgura de bodega."
)
etiquetas = [", ".join(p.replace(" Riovalle", "") for p in r["productos"]) for r in ranking]
elegido = st.selectbox("Portafolio a inspeccionar", range(len(ranking)), format_func=lambda i: etiquetas[i])
r = ranking[elegido]
difuso_ui.detalle_sistema(difuso.SISTEMA_DESEMPATE, r["inferencia"], r["nota_promedio"], r["exposicion"])

with st.expander("Notas de los productos de este portafolio"):
    st.dataframe(pd.DataFrame([
        {"Producto": p, "Nota": round(notas[p], 1), "Utilidad": formato.cop_millones(candidatos[p]["utilidad_esperada_anual"]),
         "Erosión": formato.pct(erosion[p], 0)}
        for p in r["productos"]
    ]), hide_index=True, width="stretch")

componentes.ver_codigo([difuso.entradas_desempate, difuso.desempatar_portafolios, difuso.empates_con_tolerancia])
componentes.supuestos_y_limites([
    "Las tablas de reglas, los cortes y las notas son una **propuesta ilustrativa** (docs/SPRINT4_DECISIONES.md).",
    "La exposición usa la erosión de la página 5, que es un supuesto.",
    "El umbral de 1,5 puntos viene de medir el ruido de Mamdani con centroide: subir una entrada puede mover "
    "la salida hasta ~1,3 puntos en sentido contrario. Diferencias menores no se interpretan.",
    "Con los datos actuales, los dos portafolios de $122 M son idénticos en utilidad, costo, espacio y peor "
    "caso: la exposición al competidor es lo que los separa.",
])
