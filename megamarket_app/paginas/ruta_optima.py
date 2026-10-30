"""Página 2 — Ruta óptima (Sprint 1 · búsqueda A*)."""

import copy

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from megamarket.busqueda import (
    REDES,
    a_estrella,
    a_estrella_con_traza,
    heuristica,
    recorrido_completo,
    tramos_del_recorrido,
)
from megamarket.datos import BODEGA, PLATAFORMA, clientes_poblado, clientes_valle_aburra
from megamarket.sistema_experto_logistica import (
    BASE_CONOCIMIENTO,
    construir_memoria_trabajo,
    decidir_clientes_de_la_ruta,
)
from megamarket_app import componentes, formato
from megamarket_app.mapas import construir_mapa
from megamarket_app.memoria_logistica import editor_a_csv, validar_memoria

CLIENTES = {"Poblado": clientes_poblado, "Valle de Aburrá": clientes_valle_aburra}
FUENTE_SE = "Sistema experto (Sprint 2)"
FUENTE_TODOS = "Todos los clientes (Sprint 1)"
FUENTE_MANUAL = "Selección manual"
ORDEN_TANDAS = ["ALTA", "MEDIA", "BAJA"]


def seleccion_del_sistema_experto():
    """Clientes y prioridades que dejó la página 1.

    Si todavía no se ha pasado por la página 1, se corre el sistema experto
    con la memoria de trabajo y los umbrales actuales (por defecto, los originales).
    """
    if st.session_state.get("seleccion_semana"):
        return st.session_state["seleccion_semana"]
    memoria_csv = editor_a_csv(st.session_state["memoria_logistica"])
    if validar_memoria(memoria_csv):
        return None
    base = copy.deepcopy(BASE_CONOCIMIENTO)
    base["umbrales"] = dict(st.session_state["umbrales_logistica"])
    memoria = construir_memoria_trabajo(memoria_csv)
    seleccion = {}
    for nombre_ruta in REDES:
        incluidos, prioridad, _ = decidir_clientes_de_la_ruta(nombre_ruta, base, memoria)
        seleccion[nombre_ruta] = {"incluidos": incluidos, "prioridad": prioridad}
    return seleccion


componentes.encabezado_pagina(
    "¿En qué orden visitamos a los clientes y cuántos km recorremos?",
    "Sprint 1 · Búsqueda A*",
    "El camión sale de la Bodega Olaya Herrera, visita a cada cliente y termina en la "
    "Plataforma Logística. A* encuentra el camino más corto de cada tramo y el vecino "
    "más cercano decide a quién se visita después. Si hay prioridades, se atiende primero "
    "toda la tanda ALTA, luego MEDIA y luego BAJA.",
)

# =============================================================================
# DATOS DE ENTRADA
# =============================================================================
viene_del_se = bool(st.session_state.get("seleccion_semana"))
opciones_fuente = [FUENTE_SE, FUENTE_TODOS, FUENTE_MANUAL]
if "fuente_ruta" not in st.session_state:
    st.session_state["fuente_ruta"] = FUENTE_SE if viene_del_se else FUENTE_TODOS

fuente = st.segmented_control("¿Qué clientes se visitan?", opciones_fuente,
                              default=st.session_state["fuente_ruta"], required=True)
st.session_state["fuente_ruta"] = fuente

ruta_inicial = st.session_state["ruta_elegida"] if st.session_state["ruta_elegida"] in REDES else "Poblado"
nombre_ruta = st.segmented_control("Ruta", list(REDES), default=ruta_inicial, required=True)
if st.session_state["ruta_elegida"] != "Ambas":
    st.session_state["ruta_elegida"] = nombre_ruta

red = REDES[nombre_ruta]
prioridad = None
if fuente == FUENTE_SE:
    seleccion = seleccion_del_sistema_experto()
    if seleccion is None:
        st.error("La memoria de trabajo de la página 1 tiene errores. Corrígela allá primero.",
                 icon=":material/error:")
        st.stop()
    clientes = seleccion[nombre_ruta]["incluidos"]
    prioridad = seleccion[nombre_ruta]["prioridad"]
    if viene_del_se:
        st.caption("Clientes y prioridades que decidió el sistema experto en la página 1.")
    else:
        st.caption("Aún no has pasado por la página 1: se usan los datos originales del sistema experto.")
    st.page_link("megamarket_app/paginas/clientes_semana.py",
                 label="Cambiar los datos de la semana", icon=":material/edit:")
elif fuente == FUENTE_TODOS:
    clientes = list(CLIENTES[nombre_ruta])
    st.caption("Los clientes fijos del Sprint 1, sin prioridades: una sola tanda.")
else:
    clave_manual = f"manual_{nombre_ruta}"
    elegidos = st.multiselect(
        f"Clientes de la ruta {nombre_ruta}", CLIENTES[nombre_ruta],
        default=st.session_state.get(clave_manual, CLIENTES[nombre_ruta]),
    )
    st.session_state[clave_manual] = elegidos
    clientes = [c for c in CLIENTES[nombre_ruta] if c in elegidos]

# =============================================================================
# RECORRIDO
# =============================================================================
paradas, distancia_total, orden_clientes = recorrido_completo(
    red, BODEGA, clientes, destino_final=PLATAFORMA, prioridad=prioridad,
)
tramos = tramos_del_recorrido(red, BODEGA, orden_clientes, PLATAFORMA)
prioridad_mapa = prioridad or {}

st.subheader(f"Ruta {nombre_ruta}")
tandas = [nivel for nivel in ORDEN_TANDAS if nivel in prioridad_mapa.values()]
de_paso = [n for n in dict.fromkeys(paradas) if n in CLIENTES[nombre_ruta] and n not in orden_clientes]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Distancia total", formato.km(distancia_total))
m2.metric("Paradas de entrega", f"{len(orden_clientes)} de {len(CLIENTES[nombre_ruta])}")
m3.metric("Tandas de prioridad", len(tandas) or 1,
          help="Grupos de prioridad que se atienden uno tras otro (ALTA → MEDIA → BAJA).")
m4.metric("Nodos de paso", len(de_paso), help="Clientes por los que el camión pasa sin entregarles.")

if tandas:
    st.caption(f"Orden de las tandas: **{' → '.join(tandas)}**. Dentro de cada tanda manda el vecino más cercano.")
if not orden_clientes:
    st.info("No hay clientes para visitar: el camión va directo de la bodega a la plataforma.",
            icon=":material/info:")
if de_paso:
    st.caption(f"El camión pasa por **{', '.join(de_paso)}** sin entregar: A* lo usa como atajo "
               "entre dos paradas.")

mapa = construir_mapa(red, paradas, orden_clientes, prioridad_mapa, CLIENTES[nombre_ruta])
st_folium(mapa, height=480, use_container_width=True, returned_objects=[],
          key=f"mapa_{nombre_ruta}_{fuente}")
st.caption("B = bodega · P = plataforma · número = orden de entrega (color: azul ALTA, ámbar MEDIA, "
           "gris BAJA) · punto gris = paso sin entrega · punto claro = no se visita. "
           "Usa el control de capas para ocultar el grafo o la ruta.")

st.markdown("**Tramos del recorrido**")
tabla_tramos = pd.DataFrame([
    {
        "#": i + 1,
        "Desde": t["desde"],
        "Hasta": t["hasta"],
        "Prioridad": prioridad_mapa.get(t["hasta"], "—"),
        "Camino A*": " → ".join(t["camino"]),
        "km": round(t["km"], 2),
    }
    for i, t in enumerate(tramos)
])
st.dataframe(tabla_tramos, hide_index=True, width="stretch",
             column_config={"km": st.column_config.NumberColumn("km", format="%.2f")})

# =============================================================================
# CÓMO RAZONÓ EL ALGORITMO
# =============================================================================
st.subheader("Cómo razonó el algoritmo")
st.markdown(
    "A* saca de la cola, en cada paso, el camino con menor **f = g + h**: "
    "**g** son los km reales recorridos y **h** la distancia en línea recta (haversine) "
    "que falta hasta el destino. Como la línea recta nunca es más larga que el camino real, "
    "h es **admisible** y el primer camino que llega al destino es el más corto."
)
etiquetas = [f"{i + 1}. {t['desde']} → {t['hasta']}" for i, t in enumerate(tramos)]
elegido = st.selectbox("Tramo para inspeccionar", range(len(tramos)), format_func=lambda i: etiquetas[i])
tramo = tramos[elegido]
camino, costo, traza = a_estrella_con_traza(red, tramo["desde"], tramo["hasta"])

tabla_traza = pd.DataFrame([
    {
        "Paso": p["paso"],
        "Nodo extraído": p["nodo"],
        "g (km reales)": p["g"],
        "h (línea recta)": p["h"],
        "f = g + h": p["f"],
        "Qué hizo": {"expandir": "Expande sus vecinos",
                     "ya visitado": "Ya visitado: lo descarta",
                     "destino": "¡Llegó al destino!"}[p["accion"]],
        "Camino hasta aquí": " → ".join(p["camino"]),
    }
    for p in traza
])
formato_km = st.column_config.NumberColumn(format="%.2f")
st.dataframe(tabla_traza, hide_index=True, width="stretch",
             column_config={"g (km reales)": formato_km, "h (línea recta)": formato_km, "f = g + h": formato_km})
st.caption(f"A* sacó {len(traza)} nodos de la cola para encontrar el camino de {formato.km(costo, 2)}.")

componentes.ver_codigo([heuristica, a_estrella, recorrido_completo])
componentes.supuestos_y_limites([
    "La coordenada de la **Plataforma Logística** es una estimación por nomenclatura vial (±200–400 m).",
    "Las distancias entre el acceso vial y cada cliente son las del notebook; las conexiones "
    "directas entre clientes a menos de 1,5 km usan la línea recta. **No son calles reales.**",
    "El **vecino más cercano** no prueba todos los órdenes posibles, así que no garantiza el "
    "recorrido más corto de todos; A* sí garantiza el camino más corto de cada tramo.",
    "Con prioridades, el camión agota cada tanda (ALTA → MEDIA → BAJA) antes de la siguiente, "
    "aunque eso alargue el recorrido.",
])
