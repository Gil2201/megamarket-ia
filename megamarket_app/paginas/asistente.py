"""Asistente MegaMarket (Fase 6): un agente que responde con los algoritmos de los sprints."""

import json

import openai
import streamlit as st

from agente import bucle
from agente.herramientas import ejecutar_herramienta
from agente.proveedor import PROVEEDORES, crear_cliente
from megamarket_app import componentes

MAX_PREGUNTAS = 20  # por sesión, para cuidar la cuota gratuita
TURNOS_DE_CONTEXTO = 6
PROVEEDOR = "gemini"
SUGERENCIAS = [
    "¿Cuántos km recorre esta semana la ruta Poblado?",
    "¿Por qué Fruver del Río no entra en la ruta?",
    "Si el flete de Fruver del Río baja a $30.000, ¿cambia la ruta?",
    "¿Qué referencias lanzamos y qué pasa si entra un rival?",
    "¿Qué nota de viabilidad tiene el Jugo Natural?",
    "Si el presupuesto sube a 80 millones, ¿qué lanzamos?",
]
ICONOS = {"user": ":material/person:", "assistant": ":material/smart_toy:"}


def leer_secreto(nombre):
    try:
        return st.secrets.get(nombre)
    except Exception:  # sin archivo de secretos
        return None


@st.cache_resource(show_spinner=False)
def cliente_llm(clave):
    return crear_cliente(clave, PROVEEDOR)


def escapar(texto):
    return texto.replace("$", "\\$")  # "$" se mostraría como fórmula


def mostrar_traza(traza):
    if not traza:
        return
    with st.expander(f"Herramientas usadas ({len(traza)})", icon=":material/build:"):
        st.caption("Lo que el modelo pidió y lo que respondió cada algoritmo. Las cifras de la respuesta salen de aquí.")
        for i, paso in enumerate(traza, 1):
            st.markdown(f"**{i}. `{paso['herramienta']}`**")
            st.code(json.dumps(paso["argumentos"], ensure_ascii=False, indent=2), language="json")
            st.json(paso["resultado"], expanded=False)


componentes.encabezado_pagina(
    "Asistente MegaMarket",
    "Fase 6 · Agente con herramientas",
    "Pregunta en lenguaje natural sobre rutas, clientes, portafolio o el competidor. El asistente no "
    "calcula nada por su cuenta: elige cuál algoritmo de los sprints correr, con qué datos, y explica lo "
    "que ese algoritmo respondió.",
)

clave = leer_secreto(PROVEEDORES[PROVEEDOR]["secreto"])
if not clave or clave == "pega-aqui-tu-clave":
    st.warning("El asistente no está configurado: falta `GEMINI_API_KEY` en los secretos de la app "
               "(`.streamlit/secrets.toml` en local, o *Settings → Secrets* en Streamlit Cloud).",
               icon=":material/key_off:")
    st.stop()

contrasena = leer_secreto("APP_PASSWORD")
if contrasena and not st.session_state.get("asistente_autorizado"):
    with st.form("acceso_asistente"):
        intento = st.text_input("Contraseña del asistente", type="password")
        if st.form_submit_button("Entrar"):
            if intento == contrasena:
                st.session_state["asistente_autorizado"] = True
                st.rerun()
            st.error("Contraseña incorrecta.")
    st.stop()

historial = st.session_state.setdefault("chat_asistente", [])
usadas = st.session_state.setdefault("preguntas_asistente", 0)

c1, c2 = st.columns([3, 1], vertical_alignment="center")
c1.caption(
    f"Usa **{PROVEEDORES[PROVEEDOR]['modelo']}** (Google) en su capa gratuita: Google puede usar las preguntas para "
    "mejorar sus productos, así que no escribas datos personales. Los datos del caso son ilustrativos. "
    f"Preguntas en esta sesión: **{usadas} de {MAX_PREGUNTAS}**."
)
if c2.button("Nueva conversación", icon=":material/refresh:", width="stretch", disabled=not historial):
    st.session_state["chat_asistente"] = []
    st.rerun()

# --- Conversación ---
for mensaje in historial:
    with st.chat_message(mensaje["rol"], avatar=ICONOS[mensaje["rol"]]):
        st.markdown(escapar(mensaje["texto"]))
        mostrar_traza(mensaje.get("traza"))

if not historial:
    st.markdown("**Prueba con una de estas preguntas:**")
    columnas = st.columns(2)
    for i, sugerencia in enumerate(SUGERENCIAS):
        if columnas[i % 2].button(sugerencia, key=f"sugerencia_{i}", width="stretch"):
            st.session_state["pregunta_pendiente"] = sugerencia
            st.rerun()

agotadas = usadas >= MAX_PREGUNTAS
pregunta = st.chat_input("Pregunta sobre rutas, clientes, portafolio o el competidor…", disabled=agotadas)
pregunta = pregunta or st.session_state.pop("pregunta_pendiente", None)
if agotadas:
    st.info(f"Llegaste al límite de {MAX_PREGUNTAS} preguntas de esta sesión. Recarga la página más tarde.",
            icon=":material/hourglass_empty:")

if pregunta and not agotadas:
    contexto = [{"role": m["rol"], "content": m["texto"]} for m in historial[-TURNOS_DE_CONTEXTO:]]
    historial.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user", avatar=ICONOS["user"]):
        st.markdown(escapar(pregunta))
    with st.chat_message("assistant", avatar=ICONOS["assistant"]):
        with st.spinner("Consultando los algoritmos…"):
            cliente = cliente_llm(clave)
            config = PROVEEDORES[PROVEEDOR]
            try:
                try:
                    r = bucle.responder(pregunta, cliente, config["modelo"], historial=contexto)
                except (openai.NotFoundError, openai.PermissionDeniedError):
                    r = bucle.responder(pregunta, cliente, config["modelo_respaldo"], historial=contexto)
            except openai.RateLimitError:
                r = {"texto": "Se agotó por ahora la cuota gratuita de Gemini. Intenta de nuevo en un minuto.", "traza": []}
            except openai.APIError as error:
                r = {"texto": f"No pude consultar el modelo ({type(error).__name__}). Intenta de nuevo.", "traza": []}
    historial.append({"rol": "assistant", "texto": r["texto"], "traza": r["traza"]})
    st.session_state["preguntas_asistente"] = usadas + 1
    st.rerun()

componentes.ver_codigo([bucle.responder, ejecutar_herramienta])
componentes.supuestos_y_limites([
    "El modelo de lenguaje **solo interpreta la pregunta y redacta la respuesta**: las decisiones las toman los "
    "algoritmos simbólicos de los sprints (A*, sistemas expertos, AG, Minimax, lógica difusa). Cada respuesta "
    "muestra qué herramientas usó.",
    "El prompt le prohíbe dar cifras que no vengan de una herramienta; aun así puede equivocarse al redactar. "
    "Compara con el panel de herramientas.",
    "Se evaluó con 19 preguntas de prueba (docs/AGENTE_PREGUNTAS_PRUEBA.md): 99,3 % en el calificador automático "
    "y ninguna cifra inventada en 38 respuestas.",
    "Capa gratuita de Gemini: límites de uso diarios y uso de las preguntas por parte de Google. Por eso hay un "
    f"tope de {MAX_PREGUNTAS} preguntas por sesión.",
    "Los cambios que pidas en el chat (fletes, presupuesto…) son hipotéticos: no modifican los datos de las demás páginas.",
])
