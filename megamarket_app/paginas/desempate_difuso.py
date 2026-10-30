"""Página 6 — Desempate difuso (Sprint 4 · lógica difusa). Reservada.

Todavía no hay lógica difusa (docs/SPRINT4_LOGICA_DIFUSA.md §6 sin cerrar).
La página muestra los empates que dejaron las páginas 4 y 5, que serán la
entrada del desempate.
"""

import pandas as pd
import streamlit as st

from megamarket import competidor
from megamarket_app import componentes, formato
from megamarket_app.candidatos_ui import erosion_para

componentes.encabezado_pagina(
    "¿Cuál portafolio elegimos cuando hay empate?",
    "Sprint 4 · Lógica difusa",
    "El algoritmo genético encuentra varios portafolios con la misma utilidad y hoy se queda con "
    "el primero que aparece. La lógica difusa los comparará con criterios que no son de «sí o no», "
    "como la nota de viabilidad de cada producto y la exposición al competidor.",
)
componentes.proximamente(
    "Próximamente. El diseño está en discusión con el profesor (docs/SPRINT4_LOGICA_DIFUSA.md): "
    "sistemas Mamdani de 2 entradas y 9 reglas, hechos a mano con numpy como en clase."
)

st.subheader("Empates que hoy quedan sin resolver")
candidatos = st.session_state["candidatos"]
erosion = erosion_para(candidatos, st.session_state["erosion"])
empates = st.session_state.get("empates") or {}

TITULOS = {
    "esperada": "Empatados en utilidad esperada (página 4)",
    "peor_caso": "Empatados en el peor caso con Minimax (página 5)",
}
hay_empates = False
for criterio, titulo in TITULOS.items():
    portafolios = empates.get(criterio)
    if not portafolios:
        continue
    hay_empates = True
    st.markdown(f"**{titulo}**")
    filas = []
    for productos in portafolios:
        ind = tuple(1 if n in productos else 0 for n in candidatos)
        utilidad = competidor.utilidad_total(ind, candidatos)
        exposicion = sum(competidor.perdidas_por_ataque(ind, erosion, candidatos).values())
        filas.append({
            "Productos": ", ".join(competidor.nombre_incluidos(ind, candidatos)),
            "Utilidad esperada": formato.cop_millones(utilidad),
            "Costo": formato.cop_millones(competidor.costo_total(ind, candidatos)),
            "Espacio": competidor.espacio_total(ind, candidatos),
            "Peor caso": formato.cop_millones(competidor.utilidad_peor_caso(ind, erosion, None, candidatos)),
            "Exposición al rival (Σ utilidad × erosión)": formato.cop_millones(exposicion),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")

if not hay_empates:
    st.info("Corre el algoritmo genético en la página 4 (y el Minimax en la página 5) para ver aquí los "
            "portafolios empatados.", icon=":material/info:")
    st.page_link("megamarket_app/paginas/que_lanzar.py", label="Ir a Qué lanzar", icon=":material/inventory_2:")
else:
    st.caption(
        "Los dos portafolios empatados en $122 M son idénticos en utilidad, costo, espacio y peor caso: "
        "con las variables que ya usa el AG no se desempata nada. La diferencia aparece en la exposición "
        "al competidor, y por eso el Sprint 4 necesita información nueva (la nota de viabilidad)."
    )
