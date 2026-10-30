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
from megamarket import difuso
from megamarket.sistema_experto_logistica import a_booleano
from megamarket_app import componentes, difuso_ui, formato, graficas

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
    "Sprint 2 · Sistema experto  →  Sprint 4 · Lógica difusa",
    "Antes de distribuir una categoría nueva, MegaMarket revisa siete criterios (C1–C7). "
    "El sistema experto es un chequeo de «todas las luces en verde»: basta con que falle uno "
    "para descartarla. La versión difusa mide **qué tanto** cumple cada producto, con una nota de 0 a 100.",
)

tab_clasico, tab_difuso = st.tabs(["Sistema experto (Sprint 2)", "Versión difusa (Sprint 4)"])

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


# =============================================================================
# VERSIÓN DIFUSA (SPRINT 4 · 4A)
# =============================================================================
CLAVE_EDITOR_DIFUSO = "editor_memoria_difusa"
NOMBRES_CRITERIOS = {
    "margen_pct": ("Margen (%)", 40, "C7"),
    "complementariedad": ("Complementariedad (0–10)", 10, "C5"),
    "vida_util_meses": ("Vida útil (meses)", 24, "C6"),
    "facilidad_operativa": ("Facilidad operativa (0–10)", 10, "C3"),
    "afinidad": ("Afinidad (0–10)", 10, "C1"),
    "calidad_presentacion": ("Calidad y presentación (0–10)", 10, "C4"),
}


def difusa_a_editor(df_csv):
    df = df_csv.copy()
    df["C2"] = df["C2"].map(a_booleano)
    return df.reset_index(drop=True)


def editor_a_difusa(df_editor):
    df = df_editor.copy()
    df["C2"] = df["C2"].map(lambda v: "Sí" if bool(v) else "No")
    return df


if "memoria_difusa" not in st.session_state:
    st.session_state["memoria_difusa"] = difusa_a_editor(difuso.leer_memoria_difusa())

with tab_difuso:
    st.markdown(
        "Seis criterios pasan de Sí/No a **números**, y cinco sistemas difusos de 2 entradas y 9 reglas "
        "(Mamdani, como en clase) los combinan en una jerarquía. El peso de cada criterio no es un "
        "número que multiplica: está en **la estructura y en las tablas de reglas**. C2 (registro "
        "sanitario) sigue siendo un filtro duro: sin registro el producto no se puede vender."
    )

    st.subheader("Datos de los productos")
    st.caption("Las 3 categorías del Sprint 2 y las 8 referencias Riovalle del Sprint 3. Valores ilustrativos, editables.")
    memoria_difusa = st.data_editor(
        st.session_state["memoria_difusa"],
        key=CLAVE_EDITOR_DIFUSO, num_rows="fixed", hide_index=True, width="stretch",
        height=(len(st.session_state["memoria_difusa"]) + 1) * 35 + 3,
        disabled=["producto", "tipo"],
        column_config={
            "producto": st.column_config.TextColumn("Producto", pinned=True),
            "tipo": st.column_config.TextColumn("Tipo"),
            "C2": st.column_config.CheckboxColumn("C2 · Registro", help="Filtro duro: sin registro sanitario no es viable."),
            **{c: st.column_config.NumberColumn(f"{nombre} · {crit}", min_value=0, max_value=maximo, step=0.5)
               for c, (nombre, maximo, crit) in NOMBRES_CRITERIOS.items()},
        },
    )
    st.session_state["memoria_difusa"] = memoria_difusa
    if st.button("Restaurar datos originales", icon=":material/restart_alt:", key="restaurar_difusa"):
        st.session_state["memoria_difusa"] = difusa_a_editor(difuso.leer_memoria_difusa())
        st.session_state.pop(CLAVE_EDITOR_DIFUSO, None)
        st.rerun()

    productos = difuso.construir_productos_difusos(editor_a_difusa(memoria_difusa))
    st.session_state["productos_difusos"] = productos
    evaluaciones = {nombre: difuso.nota_viabilidad(datos) for nombre, datos in productos.items()}

    # --- Resultado ---
    st.subheader("Nota de viabilidad")
    con_nota = {n: r for n, r in evaluaciones.items() if r["nota"] is not None}
    orden = sorted(con_nota, key=lambda n: -con_nota[n]["nota"])
    st.plotly_chart(
        graficas.notas_viabilidad([n.replace(" Riovalle", "") for n in orden],
                                  [con_nota[n]["nota"] for n in orden],
                                  [difuso_ui.color_nota(con_nota[n]["nota"]) for n in orden]),
        width="stretch",
    )
    sin_registro = [n for n, r in evaluaciones.items() if r["nota"] is None]
    if sin_registro:
        st.error(f"Sin registro sanitario (C2 = No), no viables sin pasar por el sistema difuso: {', '.join(sin_registro)}.",
                 icon=":material/gavel:")

    def veredicto_sprint2(nombre):
        if nombre in resultados:
            return "✅ VIABLE" if resultados[nombre]["viable"] else "❌ NO VIABLE (" + ", ".join(resultados[nombre]["incumplidos"]) + ")"
        return "✅ Viable (supuesto del Sprint 3)"

    st.markdown("**Sí/No del Sprint 2 frente a la nota difusa**")
    st.dataframe(pd.DataFrame([
        {"Producto": n, "Tipo": productos[n]["tipo"], "Sprint 2 (Sí/No)": veredicto_sprint2(n),
         "Nota difusa": round(r["nota"], 1) if r["nota"] is not None else None,
         "Etiqueta": r["etiqueta"]}
        for n, r in evaluaciones.items()
    ]), hide_index=True, width="stretch",
        column_config={"Nota difusa": st.column_config.ProgressColumn("Nota difusa", min_value=0, max_value=100, format="%.1f")})
    st.caption("El Sprint 2 solo dice Sí o No. La nota distingue, por ejemplo, entre referencias que cumplen "
               "los criterios con holgura (Higo, Mix) y las que apenas los cumplen (Jugo, Snack).")
    st.page_link("megamarket_app/paginas/que_lanzar.py",
                 label="Usar estas notas para filtrar candidatos en «Qué lanzar» →", icon=":material/inventory_2:")

    # --- Cómo razonó ---
    st.subheader("Cómo razonó el algoritmo")
    elegible = [n for n in productos if evaluaciones[n]["nota"] is not None]
    if elegible:
        nombre = st.selectbox("Producto a inspeccionar", elegible,
                              index=elegible.index("Bebidas") if "Bebidas" in elegible else 0)
        resultado = evaluaciones[nombre]
        st.markdown(f"**{nombre}** — nota **{formato.decimal(resultado['nota'])}** ({resultado['etiqueta']}). "
                    "Cada caja es un sistema Mamdani; el borde indica su etiqueta (gris baja, ámbar media, verde alta).")
        st.graphviz_chart(difuso_ui.diagrama_jerarquia(resultado, productos[nombre]), width="stretch")

        sistemas = difuso.SISTEMAS_VIABILIDAD
        clave = st.segmented_control(
            "Sistema", list(sistemas), default="S5", required=True,
            format_func=lambda k: f"{k} · {sistemas[k]['nombre']}",
        )
        entradas = {
            "S1": (productos[nombre]["margen_pct"], productos[nombre]["complementariedad"]),
            "S2": (productos[nombre]["vida_util_meses"], productos[nombre]["facilidad_operativa"]),
            "S3": (productos[nombre]["afinidad"], productos[nombre]["calidad_presentacion"]),
            "S4": (resultado["nodos"]["S1"]["valor"], resultado["nodos"]["S2"]["valor"]),
            "S5": (resultado["nodos"]["S4"]["valor"], resultado["nodos"]["S3"]["valor"]),
        }
        difuso_ui.detalle_sistema(sistemas[clave], resultado["nodos"][clave], *entradas[clave])
        st.caption("Por qué no pesan igual: en S1 el margen domina (margen bajo → atractivo bajo siempre), "
                   "en S2 la vida útil domina, en S3 la afinidad domina, S4 es el eslabón más débil y en S5 "
                   "la fortaleza del negocio manda sobre el encaje con la marca.")

    componentes.ver_codigo([difuso.trimf, difuso.trapmf, difuso.pertenencia_en, difuso.centroide,
                            difuso.inferencia_mamdani, difuso.nota_viabilidad])
    componentes.supuestos_y_limites([
        "Los **datos numéricos**, los **puntos de corte** y las **tablas de reglas** son una propuesta ilustrativa "
        "(docs/SPRINT4_DECISIONES.md) que debe validarse con el profesor y con datos reales.",
        "Los umbrales del Sprint 2 (margen 12 %, vida útil 6 meses) quedan justo en el cruce de etiquetas: "
        "pertenencia 0,5 a cada una. Ya no son fronteras duras.",
        "Mamdani con recorte por mínimo y centroide no es estrictamente monótono: subir un criterio puede bajar "
        "la nota hasta ~1,3 puntos en tramos cortos. Pasa también con el sistema visto en clase.",
        "Por el centroide, la nota nunca llega a 0 ni a 100: con estos conjuntos va de ~19 a ~81.",
        "La implementación es la del notebook de clase (numpy a mano); la paridad se prueba con el pedido "
        "ML-2048 (70,17).",
    ])
