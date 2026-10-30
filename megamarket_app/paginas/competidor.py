"""Página 5 — Competidor (Sprint 3B · teoría de juegos + Minimax)."""

import pandas as pd
import streamlit as st

from megamarket import competidor
from megamarket.competidor import COLS, FILAS, PARAMS_AG, TAMANO_POBLACION
from megamarket.datos import CANDIDATOS, K_ATAQUES, SEMILLA
from megamarket_app import componentes, formato, graficas
from megamarket_app.azar import CANDADO_AZAR
from megamarket_app.candidatos_ui import como_tupla, desde_tupla, erosion_para
from megamarket_app.tema import CRITERIO_AG, PALETA

candidatos = st.session_state["candidatos"]
restricciones = st.session_state["restricciones"]
presupuesto, espacio = restricciones["presupuesto"], restricciones["espacio"]


@st.cache_data(show_spinner="Revisando todas las combinaciones…")
def fuerza_bruta_cacheada(candidatos_tupla, presupuesto, espacio, erosion_tupla, k, criterio):
    cand, ero = desde_tupla(candidatos_tupla), dict(erosion_tupla)
    if criterio == "esperada":
        valor = lambda ind: competidor.utilidad_total(ind, cand)
    else:
        valor = lambda ind: competidor.utilidad_peor_caso(ind, ero, k, cand)
    return competidor.fuerza_bruta(valor, cand, presupuesto, espacio)


@st.cache_data(show_spinner="Calculando la sensibilidad…")
def sensibilidad_cacheada(candidatos_tupla, presupuesto, espacio, erosion_tupla, referencia):
    return competidor.analisis_sensibilidad(candidatos=desde_tupla(candidatos_tupla), presupuesto=presupuesto,
                                            espacio=espacio, erosion=dict(erosion_tupla),
                                            portafolio_referencia=referencia)


def productos_de(ind):
    return ", ".join(competidor.nombre_incluidos(ind, candidatos))


componentes.encabezado_pagina(
    "¿Qué pasa con el portafolio si un competidor reacciona?",
    "Sprint 3B · Teoría de juegos y Minimax",
    "El portafolio óptimo supone que nadie reacciona. Si un rival entra con un producto "
    "parecido, nos quita parte de la utilidad (la erosión). La teoría de juegos **evalúa** "
    "cada decisión frente al rival y el algoritmo genético **busca** el portafolio que mejor aguanta.",
)

# =============================================================================
# DATOS DE ENTRADA: EROSIÓN
# =============================================================================
with st.expander("Erosión por producto (supuesto editable)", icon=":material/tune:"):
    st.caption("Fracción de la utilidad que se pierde si el rival entra en ese producto. "
               "Un producto fácil de copiar (el Jugo) tiene erosión alta; uno difícil (la Compota), baja.")
    erosion_actual = erosion_para(candidatos, st.session_state["erosion"])
    tabla_erosion = pd.DataFrame([
        {"producto": n, "erosion": e, "equilibrio": competidor.erosion_de_equilibrio(n, candidatos)}
        for n, e in erosion_actual.items()
    ])
    editada = st.data_editor(
        tabla_erosion, key="editor_erosion", hide_index=True, num_rows="fixed", width="stretch",
        disabled=["producto", "equilibrio"],
        column_config={
            "producto": st.column_config.TextColumn("Producto"),
            "erosion": st.column_config.NumberColumn("Erosión supuesta", min_value=0.0, max_value=0.95,
                                                     step=0.05, format="percent"),
            "equilibrio": st.column_config.NumberColumn(
                "Erosión de equilibrio", format="percent",
                help="1 − costo/utilidad: si la erosión supuesta la supera, el producto pierde dinero el primer año."),
        },
    )
    st.session_state["erosion"] = {**st.session_state["erosion"],
                                   **dict(zip(editada["producto"], editada["erosion"].astype(float)))}
    if st.button("Restaurar erosión del notebook"):
        st.session_state["erosion"] = dict(competidor.EROSION)
        st.session_state.pop("editor_erosion", None)
        st.rerun()

erosion = erosion_para(candidatos, st.session_state["erosion"])
erosion_tupla = tuple(sorted(erosion.items()))
candidatos_tupla = como_tupla(candidatos)

tab_juego, tab_portafolio, tab_sensibilidad = st.tabs(
    ["A · Juego de un producto", "B · Portafolio vs. rival", "C · Sensibilidad"]
)

# =============================================================================
# PESTAÑA A — JUEGO 2x2 DE UN PRODUCTO
# =============================================================================
with tab_juego:
    st.markdown(
        "**Jugadores:** Riovalle y un competidor. **Estrategias:** Riovalle lanza o no; el rival entra o no. "
        "**Pago de Riovalle:** `utilidad × (1 − erosión) − costo` si el rival entra, `utilidad − costo` si no, "
        "y 0 si no lanza. **Pago del rival:** supuesto ilustrativo. El juego es **secuencial**: "
        "Riovalle lanza primero y el rival responde."
    )
    nombres = list(candidatos)
    producto_defecto = competidor.JUGO if competidor.JUGO in candidatos else nombres[0]
    st.session_state.setdefault("juego_producto", producto_defecto)
    if st.session_state["juego_producto"] not in candidatos:
        st.session_state["juego_producto"] = producto_defecto
    st.session_state.setdefault("juego_erosion", 0.35)
    st.session_state.setdefault("juego_rival_lanza", 6.0)
    st.session_state.setdefault("juego_rival_no_lanza", 18.0)

    def precargar(caso):
        _, nombre, ero, r_lanza, r_no_lanza = competidor.CASOS_JUGO[caso]
        st.session_state["juego_producto"] = nombre
        st.session_state["juego_erosion"] = ero
        st.session_state["juego_rival_lanza"] = r_lanza / 1e6
        st.session_state["juego_rival_no_lanza"] = r_no_lanza / 1e6

    if competidor.JUGO in candidatos:
        st.markdown("**Casos del notebook (Jugo Natural)**")
        c1, c2, c3 = st.columns(3)
        c1.button("Caso A · erosión 35 %", on_click=precargar, args=("A",), width="stretch")
        c2.button("Caso B · erosión 50 %", on_click=precargar, args=("B",), width="stretch")
        c3.button("Caso C · entrar le da pérdida", on_click=precargar, args=("C",), width="stretch")

    e1, e2 = st.columns(2)
    with e1:
        nombre = st.selectbox("Producto", nombres, key="juego_producto")
        ero = st.slider("Erosión si el rival entra", 0.0, 0.95, step=0.05, key="juego_erosion", format="%.2f")
    with e2:
        r_lanza = st.slider("Pago del rival si entra y Riovalle lanzó (M COP)", -20.0, 30.0, step=1.0,
                            key="juego_rival_lanza")
        r_no_lanza = st.slider("Pago del rival si entra y Riovalle NO lanzó (M COP)", 0.0, 40.0, step=1.0,
                               key="juego_rival_no_lanza")

    caso = competidor.mostrar_caso("Juego elegido", nombre, ero, r_lanza * 1e6, r_no_lanza * 1e6, candidatos)
    A, B = caso["A"], caso["B"]
    sec_i, sec_j = caso["secuencial"]

    celdas = ""
    for i in range(2):
        celdas += f'<tr><th style="text-align:left;padding:.6rem">Riovalle: {FILAS[i]}</th>'
        for j in range(2):
            es_nash = (i, j) in caso["nash"]
            es_sec = (i, j) == (sec_i, sec_j)
            borde = f"3px solid {PALETA['azul_rey']}" if es_nash else f"1px solid {PALETA['borde']}"
            fondo = PALETA["fondo_suave"] if es_nash else PALETA["blanco"]
            marcas = (" · <b>Nash</b>" if es_nash else "") + (" · ★ secuencial" if es_sec else "")
            celdas += (f'<td style="border:{borde};background:{fondo};padding:.6rem;text-align:center">'
                       f'<b>{A[i][j] / 1e6:.1f}</b> ; {B[i][j] / 1e6:.1f}'
                       f'<div style="font-size:.75rem;color:{PALETA["gris"]}">{marcas[3:] if marcas else "&nbsp;"}</div></td>')
        celdas += "</tr>"
    st.markdown(
        f'<table style="border-collapse:collapse;width:100%;max-width:640px">'
        f'<tr><th></th><th style="padding:.6rem">Rival: {COLS[0]}</th><th style="padding:.6rem">Rival: {COLS[1]}</th></tr>'
        f"{celdas}</table>", unsafe_allow_html=True,
    )
    st.caption("Millones COP; cada celda = Riovalle ; Rival. Borde azul = equilibrio de Nash puro; "
               "★ = resultado si Riovalle mueve primero (inducción hacia atrás).")

    nash_texto = " y ".join(f"({FILAS[i]}, {COLS[j]})" for i, j in caso["nash"]) or "ninguno"
    n1, n2, n3 = st.columns(3)
    n1.metric("Equilibrios de Nash puros", len(caso["nash"]), help=nash_texto)
    n2.metric("Si Riovalle mueve primero", f"{FILAS[sec_i]}, {COLS[sec_j]}")
    n3.metric("Riovalle gana", formato.cop_millones(caso["pago_riovalle"]))
    st.markdown(f"**Equilibrios de Nash:** {nash_texto}. "
                f"**Erosión de equilibrio de {nombre.replace(' Riovalle', '')}:** "
                f"{formato.pct(competidor.erosion_de_equilibrio(nombre, candidatos))}.")
    st.markdown(
        "**Cómo razonó:** para cada jugada de Riovalle se mira la mejor respuesta del rival (el máximo de su "
        "fila) y Riovalle escoge la jugada que mejor le va *sabiendo eso*. Es la misma idea de Minimax: "
        "se resuelve de abajo hacia arriba."
    )
    componentes.ver_codigo([competidor.matriz_producto, competidor.nash_puro, competidor.solucion_secuencial])

# =============================================================================
# PESTAÑA B — PORTAFOLIO VS. RIVAL (MINIMAX + AG)
# =============================================================================
with tab_portafolio:
    st.markdown(
        "**MAX (Riovalle)** escoge el portafolio. **MIN (el rival)** ataca el producto que más daño hace "
        "(daño = utilidad × erosión). Valor del portafolio en el **peor caso** = utilidad esperada − pérdida "
        "máxima. El árbol tiene dos niveles, así que no hace falta poda Alfa-Beta."
    )

    # --- Portafolio a evaluar ---
    opciones = {}
    resultado_ag = st.session_state.get("resultado_ag")
    if resultado_ag and resultado_ag["candidatos"] == candidatos:
        opciones["El que eligió el AG en la página 4"] = resultado_ag["mejor"]
    if list(candidatos) == list(CANDIDATOS):
        opciones["Portafolio del Sprint 3 (Higo, Jugo, Café)"] = competidor.PORTAFOLIO_SPRINT3
    if not opciones:
        _, optimos_esp, _ = fuerza_bruta_cacheada(candidatos_tupla, presupuesto, espacio, erosion_tupla, 1, "esperada")
        opciones["Óptimo de utilidad esperada (fuerza bruta)"] = optimos_esp[0]
    etiqueta_base = st.selectbox("Portafolio a evaluar", list(opciones))
    base = opciones[etiqueta_base]
    k = st.slider("¿Cuántos productos puede atacar el rival a la vez? (k)", 1, 3, K_ATAQUES)

    arbol = competidor.mostrar_arbol(base, etiqueta_base, erosion, candidatos)
    peor_k = competidor.utilidad_peor_caso(base, erosion, k, candidatos)
    a1, a2, a3 = st.columns(3)
    a1.metric("Utilidad esperada (MAX)", formato.cop_millones(arbol["utilidad_esperada"]))
    a2.metric(f"Peor caso con k = {k}", formato.cop_millones(peor_k),
              delta=formato.cop_millones(peor_k - arbol["utilidad_esperada"]), delta_color="normal")
    a3.metric("El rival ataca (k = 1)", arbol["rival_ataca"])
    st.markdown(f"**Árbol Minimax** de *{productos_de(base)}*: lo que queda si el rival ataca cada producto (nivel MIN).")
    st.plotly_chart(graficas.ataques_minimax(arbol["ataques"], arbol["utilidad_esperada"]), width="stretch")

    # --- AG con criterio configurable ---
    st.markdown("#### Algoritmo genético con fitness Minimax")
    st.markdown(
        "Es el AG del Sprint 3 con tres ajustes: el fitness es la utilidad en el **peor caso** (con un "
        "desempate de 0,001 × utilidad esperada), la reparación mira la utilidad **después de la erosión** y "
        "la ruleta usa **fitness escalado**. Se corre también con el criterio de utilidad esperada para comparar."
    )
    with st.expander("Parámetros del AG", icon=":material/tune:"):
        q1, q2, q3, q4 = st.columns(4)
        tam = q1.number_input("Población", 2, 200, TAMANO_POBLACION, key="mm_poblacion")
        gens = q2.number_input("Generaciones", 1, 300, PARAMS_AG["generaciones"], key="mm_generaciones")
        pm = q3.number_input("Prob. de mutación", 0.0, 1.0, PARAMS_AG["probabilidad_mutacion"], 0.05,
                             format="%.2f", key="mm_mutacion")
        sem = q4.number_input("Semilla", 0, value=SEMILLA, key="mm_semilla")
    params = dict(semilla=int(sem), tamano_poblacion=int(tam), generaciones=int(gens),
                  probabilidad_mutacion=float(pm), elitismo=PARAMS_AG["elitismo"],
                  candidatos=candidatos, presupuesto=presupuesto, espacio=espacio, erosion=erosion, k=k)

    if st.button("Ejecutar AG con Minimax", type="primary", icon=":material/play_arrow:"):
        with CANDADO_AZAR:
            mejor_esperada, hist_esperada = competidor.ejecutar_ag("esperada", **params)
            mejor_minimax, hist_minimax = competidor.ejecutar_ag("peor_caso", **params)
        st.session_state["resultado_minimax"] = {
            "firma": (candidatos_tupla, presupuesto, espacio, erosion_tupla, k),
            "mejor_esperada": mejor_esperada, "mejor_minimax": mejor_minimax, "hist_minimax": hist_minimax,
        }

    mm = st.session_state.get("resultado_minimax")
    if not mm:
        st.info("Pulsa **Ejecutar AG con Minimax** para buscar el portafolio que mejor aguanta al rival.",
                icon=":material/info:")
    elif mm["firma"] != (candidatos_tupla, presupuesto, espacio, erosion_tupla, k):
        st.warning("Cambiaste los datos o k: vuelve a ejecutar el AG para ver resultados actualizados.",
                   icon=":material/history:")
    else:
        valor_pc = lambda ind: competidor.utilidad_peor_caso(ind, erosion, k, candidatos)
        opt_esp, optimos_esp, validas = fuerza_bruta_cacheada(candidatos_tupla, presupuesto, espacio,
                                                              erosion_tupla, k, "esperada")
        opt_mm, optimos_mm, _ = fuerza_bruta_cacheada(candidatos_tupla, presupuesto, espacio,
                                                      erosion_tupla, k, "peor_caso")

        def fila(criterio, metodo, inds):
            inds = inds if isinstance(inds, list) else [inds]
            return {"Criterio": criterio, "Método": metodo,
                    "Productos": " | ".join(productos_de(i) for i in inds),
                    "Costo": formato.cop_millones(competidor.costo_total(inds[0], candidatos)),
                    "Espacio": competidor.espacio_total(inds[0], candidatos),
                    "Utilidad esperada": formato.cop_millones(competidor.utilidad_total(inds[0], candidatos)),
                    "Peor caso": formato.cop_millones(valor_pc(inds[0]))}

        mejor_minimax = mm["mejor_minimax"]
        r1, r2, r3 = st.columns(3)
        r1.metric("Peor caso con Minimax", formato.cop_millones(valor_pc(mejor_minimax)),
                  delta=formato.cop_millones(valor_pc(mejor_minimax) - valor_pc(base)),
                  help=f"Comparado con «{etiqueta_base}»")
        r2.metric("Utilidad esperada con Minimax", formato.cop_millones(competidor.utilidad_total(mejor_minimax, candidatos)),
                  delta=formato.cop_millones(competidor.utilidad_total(mejor_minimax, candidatos)
                                             - competidor.utilidad_total(base, candidatos)))
        r3.metric("¿Llegó al óptimo de la fuerza bruta?", "Sí" if abs(valor_pc(mejor_minimax) - opt_mm) < 1e-6 else "No")
        st.markdown(f"**El AG con Minimax elige:** {productos_de(mejor_minimax)}")

        st.dataframe(pd.DataFrame([
            fila("Utilidad esperada", "AG", mm["mejor_esperada"]),
            fila("Utilidad esperada", "Fuerza bruta", optimos_esp),
            fila("Peor caso (Minimax)", "AG", mejor_minimax),
            fila("Peor caso (Minimax)", "Fuerza bruta", optimos_mm),
        ]), hide_index=True, width="stretch")
        if len(optimos_mm) > 1:
            st.caption(f"Hay {len(optimos_mm)} portafolios empatados en el mejor peor caso; el AG se queda con el de "
                       "mayor utilidad esperada gracias al desempate de 0,001 × utilidad.")
        st.session_state["empates"] = {
            **(st.session_state.get("empates") or {}),
            "peor_caso": [competidor.nombre_incluidos(o, candidatos) for o in optimos_mm],
        }

        g1, g2 = st.columns([3, 2])
        with g1:
            st.markdown("**Costo de protegerse:** todos los portafolios válidos")
            puntos = [(competidor.utilidad_total(c, candidatos), valor_pc(c), productos_de(c)) for c in validas]
            destacados = [
                (competidor.utilidad_total(base, candidatos), valor_pc(base), etiqueta_base, CRITERIO_AG["esperada"]),
                (competidor.utilidad_total(mejor_minimax, candidatos), valor_pc(mejor_minimax),
                 "Elegido con Minimax", CRITERIO_AG["peor_caso"]),
            ]
            st.plotly_chart(graficas.costo_de_protegerse(puntos, destacados), width="stretch")
        with g2:
            st.markdown("**Evolución del AG con fitness Minimax**")
            st.plotly_chart(graficas.evolucion_ag(mm["hist_minimax"], "Mejor peor caso", "Peor caso promedio",
                                                  CRITERIO_AG["peor_caso"], "Mejor peor caso", "Peor caso promedio"),
                            width="stretch")

        st.markdown("#### Robustez")
        st.caption("Un solo resultado no demuestra que el AG sea confiable: se repite con 20 semillas distintas "
                   "y se cuenta cuántas veces llega al óptimo. Tarda unos segundos.")
        if st.button("Probar con 20 semillas", icon=":material/repeat:"):
            with st.spinner("Corriendo 40 algoritmos genéticos…"), CANDADO_AZAR:
                aciertos = competidor.analisis_robustez(
                    tamano_poblacion=int(tam),
                    params_ag=dict(generaciones=int(gens), probabilidad_mutacion=float(pm), elitismo=PARAMS_AG["elitismo"]),
                    candidatos=candidatos, presupuesto=presupuesto, espacio=espacio, erosion=erosion, k=k,
                )
            b1, b2 = st.columns(2)
            b1.metric("Criterio utilidad esperada", f"{aciertos['esperada']} de 20")
            b2.metric("Criterio peor caso", f"{aciertos['peor_caso']} de 20")

    componentes.ver_codigo([competidor.perdidas_por_ataque, competidor.perdida_maxima,
                            competidor.utilidad_peor_caso, competidor.fitness, competidor.razon,
                            competidor.seleccionar_por_ruleta, competidor.ag_portafolio])

# =============================================================================
# PESTAÑA C — SENSIBILIDAD
# =============================================================================
with tab_sensibilidad:
    st.markdown(
        "La erosión es un supuesto, así que se multiplica por un factor (0,5 = rivales mucho más débiles, "
        "1,5 = más fuertes; tope de 95 %) y se busca con fuerza bruta el portafolio con mejor peor caso. "
        "También se prueba un rival que puede atacar 2 productos a la vez."
    )
    referencia = base  # el portafolio elegido en la pestaña B (las pestañas se ejecutan en orden)
    filas = sensibilidad_cacheada(candidatos_tupla, presupuesto, espacio, erosion_tupla, referencia)
    tabla = pd.DataFrame([
        {"Ataques del rival": f["Ataques del rival"],
         "Factor de erosión": f"× {str(f['Factor de erosión']).replace('.', ',')}",
         "Portafolio óptimo": f["Portafolio óptimo"],
         "Peor caso óptimo": formato.cop_millones(f["Peor caso"], 2),
         "Peor caso del portafolio evaluado": formato.cop_millones(f["Peor caso del portafolio Sprint 3"], 2),
         "Diferencia": formato.cop_millones(f["Peor caso"] - f["Peor caso del portafolio Sprint 3"], 2)}
        for f in filas
    ])
    st.dataframe(tabla, hide_index=True, width="stretch")
    st.caption(f"«Portafolio evaluado» = {productos_de(referencia)}. Escogerlo cuesta casi nada si el rival es "
               "débil y bastante si es fuerte.")
    componentes.ver_codigo([competidor.analisis_sensibilidad, competidor.fuerza_bruta])

componentes.supuestos_y_limites([
    "La **erosión** y los **pagos del rival** son supuestos ilustrativos; la erosión real se estimaría con "
    "datos de lanzamientos parecidos de la competencia.",
    "**Minimax es pesimista por diseño:** supone que el rival minimiza nuestra utilidad, cuando un competidor "
    "real maximiza la suya. Por eso se complementa con la matriz de pagos (pestaña A).",
    "Es un **Minimax simplificado**: un solo movimiento del rival, sin poda Alfa-Beta (el árbol tiene dos niveles).",
    "El análisis usa **el primer año**: el costo de lanzamiento se paga una vez.",
    "Los candidatos nuevos (agregados en la página 4) reciben una erosión de 40 % por defecto, editable arriba.",
])
