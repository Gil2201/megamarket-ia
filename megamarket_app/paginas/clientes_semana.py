"""Página 1 — Clientes de la semana (Sprint 2 · sistema experto de logística)."""

import copy

import streamlit as st

from megamarket.sistema_experto_logistica import (
    BASE_CONOCIMIENTO,
    construir_memoria_trabajo,
    decidir_clientes_de_la_ruta,
    leer_memoria_logistica,
    motor_inferencia,
    prioridad_mas_alta,
)
from megamarket_app import componentes
from megamarket_app.memoria_logistica import (
    OPCIONES_STOCK,
    csv_a_editor,
    csv_para_descargar,
    editor_a_csv,
    validar_memoria,
)

RUTAS = ["Poblado", "Valle de Aburrá"]
CLAVE_EDITOR = "editor_memoria_logistica"


def reemplazar_memoria(df_editor):
    """Pone una memoria nueva en la tabla y descarta las ediciones pendientes."""
    st.session_state["memoria_logistica"] = df_editor
    st.session_state.pop(CLAVE_EDITOR, None)


componentes.encabezado_pagina(
    "¿A quién visitamos esta semana y con qué prioridad?",
    "Sprint 2 · Sistema experto",
    "No todos los clientes necesitan mercancía cada semana. Un sistema experto con "
    "reglas de inclusión (R1–R3), vetos (R4–R5) y una regla por defecto (R6) decide "
    "quién entra en la ruta, con qué prioridad y por qué.",
)

# =============================================================================
# DATOS DE ENTRADA
# =============================================================================
st.subheader("Datos de esta semana")
st.caption(
    "Esta es la **memoria de trabajo**: una fila por cliente con lo que pasó esta semana. "
    "Edita cualquier celda y la decisión se recalcula al instante."
)

ruta_elegida = st.segmented_control(
    "Ruta", RUTAS + ["Ambas"],
    default=st.session_state["ruta_elegida"], required=True,
)
st.session_state["ruta_elegida"] = ruta_elegida

umbrales = st.session_state["umbrales_logistica"]
col_dias, col_flete, _ = st.columns([1, 1, 2])
with col_dias:
    dias = st.number_input(
        "Días sin entrega (R2)", min_value=1, max_value=90, step=1,
        value=umbrales["dias_sin_entrega"],
        help="R2 incluye al cliente si pasaron MÁS de estos días sin entrega (y no hubo visita).",
    )
with col_flete:
    flete_pct = st.number_input(
        "Tope de flete (R4), %", min_value=0.5, max_value=20.0, step=0.5,
        value=umbrales["flete_sobre_factura"] * 100, format="%.1f",
        help="R4 veta al cliente si el flete supera este porcentaje de la factura.",
    )
st.session_state["umbrales_logistica"] = {"dias_sin_entrega": int(dias), "flete_sobre_factura": flete_pct / 100}

memoria_editada = st.data_editor(
    st.session_state["memoria_logistica"],
    key=CLAVE_EDITOR,
    num_rows="fixed",
    hide_index=True,
    height=(len(st.session_state["memoria_logistica"]) + 1) * 35 + 3,  # todas las filas, sin scroll
    width="stretch",
    disabled=["cliente", "ruta"],
    column_config={
        "cliente": st.column_config.TextColumn("Cliente", pinned=True),
        "ruta": st.column_config.TextColumn("Ruta"),
        "visita_mercaderista_disponible": st.column_config.CheckboxColumn(
            "Visita del mercaderista", help="¿Hubo visita reciente del mercaderista?"),
        "mercaderista_reporta_stock_bajo": st.column_config.SelectboxColumn(
            "Reporta stock bajo", options=OPCIONES_STOCK, required=True,
            help="«No hubo visita» activa el respaldo de R2."),
        "dias_desde_ultima_entrega": st.column_config.NumberColumn(
            "Días sin entrega", min_value=0, step=1, format="%d"),
        "queja_urgente": st.column_config.CheckboxColumn("Queja urgente"),
        "precio_actualizado_en_punto_de_venta": st.column_config.CheckboxColumn(
            "PVP actualizado", help="¿El punto de venta tiene el precio de la lista vigente?"),
        "valor_factura_pedido": st.column_config.NumberColumn(
            "Factura (COP)", min_value=1, step=1000, format="$%d"),
        "costo_flete_estimado": st.column_config.NumberColumn(
            "Flete (COP)", min_value=0, step=1000, format="$%d"),
    },
)
st.session_state["memoria_logistica"] = memoria_editada

col_restaurar, col_descargar, col_subir = st.columns([1, 1, 2], vertical_alignment="bottom")
with col_restaurar:
    if st.button("Restaurar datos originales", icon=":material/restart_alt:", width="stretch"):
        reemplazar_memoria(csv_a_editor(leer_memoria_logistica()))
        st.session_state["umbrales_logistica"] = dict(BASE_CONOCIMIENTO["umbrales"])
        st.rerun()
with col_descargar:
    st.download_button(
        "Descargar CSV", csv_para_descargar(memoria_editada),
        file_name="memoria_trabajo_logistica.csv", mime="text/csv",
        icon=":material/download:", width="stretch",
    )
with col_subir:
    archivo = st.file_uploader(
        "Subir un CSV propio (mismo formato)", type="csv", key="csv_logistica",
        help="Separado por ; o por , — puede venir de Excel (CSV UTF-8).",
    )
    if archivo is not None and st.session_state.get("csv_logistica_cargado") != archivo.file_id:
        try:
            df_subido = leer_memoria_logistica(archivo)
            errores = validar_memoria(df_subido)
        except Exception as error:  # CSV ilegible
            errores = [f"No se pudo leer el archivo: {error}"]
        st.session_state["csv_logistica_cargado"] = archivo.file_id
        if errores:
            st.session_state["errores_csv_logistica"] = errores
        else:
            st.session_state.pop("errores_csv_logistica", None)
            reemplazar_memoria(csv_a_editor(df_subido))
            st.rerun()
    for error in st.session_state.get("errores_csv_logistica", []):
        st.error(error, icon=":material/error:")

# =============================================================================
# MOTOR DE INFERENCIA
# =============================================================================
memoria_csv = editor_a_csv(memoria_editada)
errores = validar_memoria(memoria_csv)
if errores:
    for error in errores:
        st.error(error, icon=":material/error:")
    st.stop()

base_conocimiento = copy.deepcopy(BASE_CONOCIMIENTO)
base_conocimiento["umbrales"] = dict(st.session_state["umbrales_logistica"])
MEMORIA_TRABAJO = construir_memoria_trabajo(memoria_csv)

resultados = {}
for nombre_ruta in RUTAS:
    incluidos, prioridad_por_cliente, traza = decidir_clientes_de_la_ruta(
        nombre_ruta, base_conocimiento, MEMORIA_TRABAJO
    )
    resultados[nombre_ruta] = {"incluidos": incluidos, "prioridad": prioridad_por_cliente, "traza": traza}

rutas_vista = RUTAS if ruta_elegida == "Ambas" else [ruta_elegida]

# =============================================================================
# RESULTADO
# =============================================================================
st.subheader("Decisión del sistema experto")

trazas_vista = [t for r in rutas_vista for t in resultados[r]["traza"]]
n_incluidos = sum(t["incluir_en_ruta"] for t in trazas_vista)
n_vetados = sum(any("VETO" in razon for razon in t["razones"]) for t in trazas_vista)
n_defecto = sum(t["razones"][0].startswith("R6") for t in trazas_vista)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Clientes en la ruta", f"{n_incluidos} de {len(trazas_vista)}")
m2.metric("Prioridad ALTA", sum(t["prioridad"] == "ALTA" for t in trazas_vista))
m3.metric("Vetados (R4/R5)", n_vetados)
m4.metric("Sin motivo (R6)", n_defecto)

COLOR_PRIORIDAD = {"ALTA": "blue", "MEDIA": "orange", "BAJA": "gray"}

def tarjeta_cliente(conclusion):
    """Tarjeta con la conclusión del motor para un cliente y sus razones."""
    st.markdown(f"**{conclusion['cliente']}**")
    if conclusion["incluir_en_ruta"]:
        st.badge("Incluir", icon=":material/check_circle:", color="green")
        st.badge(f"Prioridad {conclusion['prioridad']}", color=COLOR_PRIORIDAD[conclusion["prioridad"]])
    else:
        st.badge("Excluir", icon=":material/cancel:", color="red")
    for razon in conclusion["razones"]:
        razon = razon.replace("$", "\\$")  # "$" se mostraría como fórmula
        if "VETO" in razon:
            st.markdown(f":red[**{razon}**]")
        else:
            st.caption(razon)


for nombre_ruta in rutas_vista:
    if len(rutas_vista) > 1:
        st.markdown(f"#### Ruta {nombre_ruta}")
    traza = resultados[nombre_ruta]["traza"]
    for inicio in range(0, len(traza), 4):
        columnas = st.columns(4)
        for columna, conclusion in zip(columnas, traza[inicio:inicio + 4]):
            with columna.container(border=True, height="stretch"):
                tarjeta_cliente(conclusion)

st.markdown("")
if st.button("Calcular la ruta con estos clientes →", type="primary", icon=":material/route:"):
    st.session_state["seleccion_semana"] = {
        r: {"incluidos": resultados[r]["incluidos"], "prioridad": resultados[r]["prioridad"]}
        for r in RUTAS
    }
    st.session_state.pop("fuente_ruta", None)  # la página 2 abre con los clientes del sistema experto
    st.switch_page("megamarket_app/paginas/ruta_optima.py")

# =============================================================================
# CÓMO RAZONÓ EL ALGORITMO
# =============================================================================
st.subheader("Cómo razonó el algoritmo")
st.markdown(
    "El motor hace **encadenamiento hacia adelante** en una sola pasada por cliente: "
    "junta los hechos fijos de la base de conocimiento (ruta, rotación del producto) con "
    "los de esta semana, evalúa R1–R3, aplica R6 si ninguna se cumple y, si el cliente es "
    "candidato, revisa los vetos R4 y R5."
)
st.markdown(f"""
| # | Regla | Efecto |
|---|-------|--------|
| **R1** | SI el mercaderista reporta stock bajo, ENTONCES incluir. La prioridad sale de la rotación del producto en ese punto (alta → ALTA, media → MEDIA, baja → BAJA). | Inclusión |
| **R2** | SI NO hubo visita reciente Y pasaron más de **{base_conocimiento['umbrales']['dias_sin_entrega']} días** sin entrega Y la rotación es media o alta, ENTONCES incluir preventivamente. | Inclusión, prioridad **BAJA** |
| **R3** | SI el cliente reportó una queja urgente, ENTONCES incluirlo y darle prioridad. | Inclusión, prioridad **ALTA** |
| **R4** | SI el flete es mayor al **{base_conocimiento['umbrales']['flete_sobre_factura']:.1%}** de la factura, ENTONCES NO se despacha. | Veto |
| **R5** | SI el punto de venta NO ha actualizado el PVP según la lista vigente, ENTONCES NO se despacha. | Veto |
| **R6** | SI ninguna de R1, R2 o R3 se cumple, ENTONCES el cliente no entra esta semana. | Exclusión por defecto |

**H1 — Política de entrega:** todo pedido incluido debe entregarse entre
{BASE_CONOCIMIENTO['politicas']['ventana_entrega_horas'][0]} y {BASE_CONOCIMIENTO['politicas']['ventana_entrega_horas'][1]} horas
después de generada la orden. Es un hecho de la base de conocimiento, no una regla que decide quién entra.

**Resolución de conflictos:** si varias reglas de inclusión se cumplen, se queda la prioridad más alta.
Los vetos R4 y R5 anulan la inclusión aunque venga de una queja urgente (R3).
""")

componentes.ver_codigo([motor_inferencia, prioridad_mas_alta, decidir_clientes_de_la_ruta])
componentes.supuestos_y_limites([
    "Los datos de la memoria de trabajo (visitas, quejas, facturas, fletes) son **ilustrativos**.",
    "La política H1 (entrega en 48–72 h) se documenta, pero no se verifica: el recorrido no modela tiempos.",
    "La rotación del producto en cada punto es un atributo fijo de la base de conocimiento; no se edita semana a semana.",
    "El motor evalúa cada cliente por separado (una sola pasada): no hay dependencias entre clientes.",
])
