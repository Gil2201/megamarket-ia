"""Inicio (landing): la primera página que ve cualquier visitante.

Estilo inspirado en stripe.com y puygroup.com, con la paleta de MegaMarket.
Las cifras se calculan en vivo con la lógica de megamarket/ y los datos
originales; la ilustración del hero es la ruta real del Sprint 1.
"""

import streamlit as st

from megamarket import competidor, difuso
from megamarket.busqueda import REDES, recorrido_completo
from megamarket.datos import BODEGA, COORDENADAS, PLATAFORMA, clientes_poblado
from megamarket.sistema_experto_logistica import (
    BASE_CONOCIMIENTO,
    construir_memoria_trabajo,
    decidir_clientes_de_la_ruta,
    leer_memoria_logistica,
)
from megamarket_app import formato
from megamarket_app.tema import DIFUSO, PALETA, SEMANTICOS, aplicar_css_inicio

PAGINAS = "megamarket_app/paginas"
P = PALETA


@st.cache_data(show_spinner=False)
def cifras_en_vivo():
    """Corre los algoritmos con los datos originales para la banda de cifras y el hero."""
    memoria = construir_memoria_trabajo(leer_memoria_logistica())
    incluidos_total, km_total, rutas = 0, 0.0, {}
    for nombre_ruta, red in REDES.items():
        incluidos, prioridad, _ = decidir_clientes_de_la_ruta(nombre_ruta, BASE_CONOCIMIENTO, memoria)
        paradas, km, orden = recorrido_completo(red, BODEGA, incluidos, PLATAFORMA, prioridad)
        incluidos_total += len(incluidos)
        km_total += km
        rutas[nombre_ruta] = {"paradas": paradas, "orden": orden, "km": km}
    utilidad_optima, _, _ = competidor.fuerza_bruta(competidor.utilidad_total)
    peor_caso_optimo, _, _ = competidor.fuerza_bruta(competidor.utilidad_peor_caso)
    notas = difuso.notas_de_productos(difuso.construir_productos_difusos(difuso.leer_memoria_difusa()))
    return {
        "incluidos": incluidos_total,
        "clientes": len(BASE_CONOCIMIENTO["clientes"]),
        "km_total": km_total,
        "rutas": rutas,
        "utilidad_optima": utilidad_optima,
        "peor_caso_optimo": peor_caso_optimo,
        "nota_bebidas": notas["Bebidas"],
    }


def svg_ruta(red, paradas, orden, ancho=520, alto=400, margen=46):
    """La ruta Poblado del sistema experto, proyectada desde las coordenadas reales."""
    nodos = list(red)
    lats = [COORDENADAS[n][0] for n in nodos]
    lons = [COORDENADAS[n][1] for n in nodos]

    def xy(nodo):
        lat, lon = COORDENADAS[nodo]
        x = margen + (lon - min(lons)) / (max(lons) - min(lons)) * (ancho - 2 * margen)
        y = margen + (max(lats) - lat) / (max(lats) - min(lats)) * (alto - 2 * margen)
        return x, y

    aristas = ""
    vistas = set()
    for a, vecinos in red.items():
        for b, _ in vecinos:
            if (b, a) in vistas:
                continue
            vistas.add((a, b))
            (x1, y1), (x2, y2) = xy(a), xy(b)
            aristas += (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{P["gris"]}" stroke-opacity=".25" stroke-width="1.3" stroke-dasharray="4 5"/>')

    puntos = " ".join(f"{xy(n)[0]:.1f},{xy(n)[1]:.1f}" for n in paradas)
    trazo = "M " + " L ".join(f"{xy(n)[0]:.1f} {xy(n)[1]:.1f}" for n in paradas)
    numero = {c: i + 1 for i, c in enumerate(orden)}

    marcas = ""
    for n in nodos:
        x, y = xy(n)
        if n in (BODEGA, PLATAFORMA):
            letra = "B" if n == BODEGA else "P"
            marcas += (f'<rect x="{x - 13:.1f}" y="{y - 13:.1f}" width="26" height="26" rx="7" fill="{P["azul_noche"]}"/>'
                       f'<text x="{x:.1f}" y="{y + 4.5:.1f}" text-anchor="middle" font-size="13" font-weight="700" fill="{P["blanco"]}">{letra}</text>')
        elif n in numero:
            marcas += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{P["azul_rey"]}" stroke="{P["blanco"]}" stroke-width="2.5"/>'
                       f'<text x="{x:.1f}" y="{y + 4.2:.1f}" text-anchor="middle" font-size="11.5" font-weight="700" fill="{P["blanco"]}">{numero[n]}</text>')
        elif n in clientes_poblado:
            marcas += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{P["blanco"]}" stroke="{P["gris"]}" stroke-opacity=".5" stroke-width="2"/>'
        else:
            marcas += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{P["azul_medio"]}"/>'

    return f"""
    <svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" font-family="Montserrat, sans-serif"
         role="img" aria-label="Ruta Poblado calculada con A*">
      {aristas}
      <polyline points="{puntos}" fill="none" stroke="{P["azul_rey"]}" stroke-opacity=".9" stroke-width="5"
                stroke-linecap="round" stroke-linejoin="round"/>
      <polyline class="mm-ruta-animada" points="{puntos}" pathLength="900" fill="none" stroke="{P["amarillo_globo"]}"
                stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
      {marcas}
      <circle r="7" fill="{P["amarillo_globo"]}" stroke="{P["azul_noche"]}" stroke-width="2.5">
        <animateMotion dur="7s" repeatCount="indefinite" path="{trazo}"/>
      </circle>
    </svg>
    """


# --- Miniaturas de las tarjetas bento (SVG simples con la paleta) ---
def mini_clientes():
    filas = [("Merka 10", True), ("Fruver del Río", False), ("Mercados Verona", True), ("Redetrans", False)]
    contenido = ""
    for i, (nombre, entra) in enumerate(filas):
        y = 18 + i * 30
        color = SEMANTICOS["incluir"] if entra else SEMANTICOS["excluir"]
        etiqueta = "Incluir" if entra else "Veto"
        contenido += (f'<rect x="10" y="{y}" width="280" height="24" rx="6" fill="{P["fondo_suave"]}"/>'
                      f'<text x="22" y="{y + 16}" font-size="11" fill="{P["texto"]}">{nombre}</text>'
                      f'<rect x="212" y="{y + 4}" width="66" height="16" rx="8" fill="{color}" fill-opacity=".15"/>'
                      f'<text x="245" y="{y + 15.5}" font-size="9.5" font-weight="700" text-anchor="middle" fill="{color}">{etiqueta}</text>')
    return f'<svg viewBox="0 0 300 140" font-family="Montserrat, sans-serif">{contenido}</svg>'


def mini_ruta():
    puntos = [(30, 110), (80, 70), (130, 90), (175, 40), (225, 60), (270, 25)]
    linea = " ".join(f"{x},{y}" for x, y in puntos)
    nodos = "".join(f'<circle cx="{x}" cy="{y}" r="7" fill="{P["azul_rey"] if 0 < i < 5 else P["azul_noche"]}"/>'
                    for i, (x, y) in enumerate(puntos))
    return (f'<svg viewBox="0 0 300 140"><polyline points="30,110 130,90 225,60 270,25" fill="none" '
            f'stroke="{P["gris"]}" stroke-opacity=".3" stroke-dasharray="4 5" stroke-width="1.5"/>'
            f'<polyline points="{linea}" fill="none" stroke="{P["azul_rey"]}" stroke-width="4" stroke-linecap="round" '
            f'stroke-linejoin="round"/>{nodos}<text x="150" y="132" font-size="11" text-anchor="middle" '
            f'font-family="Montserrat" fill="{P["gris"]}">f = g + h</text></svg>')


def mini_ag():
    valores = [52, 74, 70, 86, 82, 95, 95, 95]
    barras = "".join(f'<rect x="{24 + i * 33}" y="{120 - v}" width="22" height="{v}" rx="4" '
                     f'fill="{P["azul_rey"] if v == 95 else P["azul_medio"]}" fill-opacity="{1 if v == 95 else .35}"/>'
                     for i, v in enumerate(valores))
    return (f'<svg viewBox="0 0 300 140">{barras}<line x1="18" y1="25" x2="285" y2="25" stroke="{P["amarillo_globo"]}" '
            f'stroke-width="2" stroke-dasharray="5 4"/><text x="285" y="18" font-size="10" text-anchor="end" '
            f'font-family="Montserrat" fill="{P["gris"]}">óptimo · fuerza bruta</text></svg>')


def mini_competidor():
    celdas = [(0, 0, "3,8 ; 6", True), (0, 1, "22 ; 0", False), (1, 0, "0 ; 18", False), (1, 1, "0 ; 0", False)]
    contenido = ""
    for f, c, texto, nash in celdas:
        x, y = 80 + c * 105, 18 + f * 55
        contenido += (f'<rect x="{x}" y="{y}" width="98" height="48" rx="8" fill="{P["fondo_suave"] if nash else P["blanco"]}" '
                      f'stroke="{P["azul_rey"] if nash else P["borde"]}" stroke-width="{2.5 if nash else 1}"/>'
                      f'<text x="{x + 49}" y="{y + 29}" font-size="12" font-weight="600" text-anchor="middle" fill="{P["azul_noche"]}">{texto}</text>')
    contenido += (f'<text x="70" y="47" font-size="10" text-anchor="end" fill="{P["gris"]}">Lanzar</text>'
                  f'<text x="70" y="102" font-size="10" text-anchor="end" fill="{P["gris"]}">No lanzar</text>')
    return f'<svg viewBox="0 0 300 140" font-family="Montserrat, sans-serif">{contenido}</svg>'


def mini_difusa():
    c = list(DIFUSO.values())
    return (f'<svg viewBox="0 0 300 140"><polyline points="15,25 70,25 120,115" fill="none" stroke="{c[0]}" stroke-width="3"/>'
            f'<polyline points="70,115 150,25 230,115" fill="none" stroke="{c[1]}" stroke-width="3"/>'
            f'<polyline points="180,115 230,25 285,25" fill="none" stroke="{c[2]}" stroke-width="3"/>'
            f'<line x1="250" y1="12" x2="250" y2="120" stroke="{P["azul_noche"]}" stroke-dasharray="4 4" stroke-width="2"/>'
            f'<text x="244" y="132" font-size="11" text-anchor="end" font-family="Montserrat" fill="{P["gris"]}">nota 80,6</text></svg>')


def mini_desempate():
    return (f'<svg viewBox="0 0 300 140" font-family="Montserrat, sans-serif">'
            f'<text x="12" y="38" font-size="11" fill="{P["texto"]}">Higo · Jugo · Café</text>'
            f'<rect x="12" y="46" width="270" height="16" rx="8" fill="{P["fondo_suave"]}"/>'
            f'<rect x="12" y="46" width="{270 * .604:.0f}" height="16" rx="8" fill="{P["azul_rey"]}"/>'
            f'<text x="12" y="92" font-size="11" fill="{P["texto"]}">Mix · Barra · Jugo</text>'
            f'<rect x="12" y="100" width="270" height="16" rx="8" fill="{P["fondo_suave"]}"/>'
            f'<rect x="12" y="100" width="{270 * .526:.0f}" height="16" rx="8" fill="{P["gris"]}" fill-opacity=".45"/>'
            f'<text x="282" y="38" font-size="11" font-weight="700" text-anchor="end" fill="{P["azul_rey"]}">60,4 ★</text>'
            f'<text x="282" y="92" font-size="11" text-anchor="end" fill="{P["gris"]}">52,6</text></svg>')


def tarjeta_bento(clave, svg, chip, titulo, texto, pagina, enlace):
    with st.container(key=f"bento_{clave}"):
        st.markdown(
            f'<div class="mm-bento-visual">{svg}</div>'
            f'<div class="mm-bento-chip">{chip}</div>'
            f'<div class="mm-bento-titulo">{titulo}</div>'
            f'<div class="mm-bento-texto">{texto}</div>',
            unsafe_allow_html=True,
        )
        st.page_link(f"{PAGINAS}/{pagina}", label=enlace, icon=":material/arrow_forward:")


def svg_cadena():
    """Las dos cadenas de decisión como un diagrama de flujo."""
    def caja(x, y, sprint, texto, w=150):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="12" fill="{P["blanco"]}" stroke="{P["borde"]}"/>'
                f'<text x="{x + 12}" y="{y + 23}" font-size="12" font-weight="700" fill="{P["azul_rey"]}">{sprint}</text>'
                f'<text x="{x + 12}" y="{y + 45}" font-size="15" font-weight="600" fill="{P["azul_noche"]}">{texto}</text>')

    def flecha(x1, x2, y):
        return (f'<line x1="{x1}" y1="{y}" x2="{x2 - 6}" y2="{y}" stroke="{P["azul_rey"]}" stroke-width="2"/>'
                f'<polygon points="{x2},{y} {x2 - 8},{y - 5} {x2 - 8},{y + 5}" fill="{P["azul_rey"]}"/>')

    return f"""
    <svg viewBox="0 0 560 245" font-family="Montserrat, sans-serif" role="img" aria-label="Cadenas de decisión">
      <text x="0" y="14" font-size="13" font-weight="700" fill="{P["gris"]}" letter-spacing="1">LOGÍSTICA</text>
      {caja(0, 26, "SPRINT 2", "¿A quién visito?", 160)}{flecha(160, 200, 55)}
      {caja(200, 26, "SPRINT 1", "¿En qué orden?", 160)}
      <text x="0" y="128" font-size="13" font-weight="700" fill="{P["gris"]}" letter-spacing="1">PORTAFOLIO</text>
      {caja(0, 140, "SPRINT 2 + 4", "¿Es viable?", 126)}{flecha(126, 146, 169)}
      {caja(146, 140, "SPRINT 3A", "¿Qué lanzo?", 126)}{flecha(272, 292, 169)}
      {caja(292, 140, "SPRINT 3B", "¿Y el rival?", 126)}{flecha(418, 438, 169)}
      {caja(438, 140, "SPRINT 4", "Desempate", 122)}
      <text x="0" y="235" font-size="13" fill="{P["gris"]}">Cada flecha es un resultado que pasa a la página siguiente.</text>
    </svg>
    """


# =============================================================================
# PÁGINA
# =============================================================================
aplicar_css_inicio()
cifras = cifras_en_vivo()
poblado = cifras["rutas"]["Poblado"]

# --- Hero ---
col_texto, col_visual = st.columns([1.05, 1], gap="large", vertical_alignment="center")
with col_texto:
    st.markdown(
        '<span class="mm-pildora"><span class="punto"></span><b>Proyecto académico</b> · Universidad EIA</span>'
        '<div class="mm-titular">Decisiones de logística y portafolio, '
        "<span>resueltas con inteligencia artificial clásica.</span></div>"
        '<p class="mm-bajada">El caso <b>MegaMarket</b>: a quién visitar esta semana, en qué orden, qué productos '
        "lanzar y qué pasa si un competidor reacciona. Cada algoritmo se puede <b>usar</b>, ver "
        "<b>cómo razona</b> paso a paso y leer su <b>código</b>.</p>",
        unsafe_allow_html=True,
    )
    b1, b2, _ = st.columns([1.45, 1.1, 0.25])
    with b1, st.container(key="cta_primario"):
        st.page_link(f"{PAGINAS}/clientes_semana.py", label="Explorar la logística", icon=":material/arrow_forward:")
    with b2, st.container(key="cta_secundario"):
        st.page_link(f"{PAGINAS}/que_lanzar.py", label="Ver el portafolio")
with col_visual:
    st.markdown(
        f'<div class="mm-escena">{svg_ruta(REDES["Poblado"], poblado["paradas"], poblado["orden"])}'
        f'<div class="mm-flotante" style="bottom:18px;left:18px">Ruta Poblado · esta semana'
        f'<b>{formato.km(poblado["km"])}</b>{len(poblado["orden"])} paradas · A*</div>'
        f'<div class="mm-flotante" style="top:18px;right:18px;animation-delay:-3s;min-width:150px">Nota difusa · Bebidas'
        f'<b>{formato.decimal(cifras["nota_bebidas"])} / 100</b>'
        f'<div class="barra"><i style="width:{cifras["nota_bebidas"]:.0f}%"></i></div></div>'
        "</div>",
        unsafe_allow_html=True,
    )

# --- Banda de cifras (calculadas ahora mismo) ---
st.markdown(
    f"""
    <div class="mm-banda">
      <div class="mm-cifra"><small>Sistema experto</small><b>{cifras["incluidos"]} de {cifras["clientes"]}</b>
        <span>clientes necesitan entrega esta semana</span></div>
      <div class="mm-cifra"><small>Búsqueda A*</small><b>{formato.km(cifras["km_total"])}</b>
        <span>recorrido total de las dos rutas</span></div>
      <div class="mm-cifra"><small>Algoritmo genético</small><b>{formato.cop_millones(cifras["utilidad_optima"], 0)}</b>
        <span>utilidad anual del mejor portafolio</span></div>
      <div class="mm-cifra"><small>Minimax</small><b>{formato.cop_millones(cifras["peor_caso_optimo"], 0)}</b>
        <span>utilidad protegida si un rival ataca</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("Cifras calculadas en vivo por el código de la app con los datos originales del caso. Los datos son ilustrativos.")

# --- Bento ---
st.markdown('<div class="mm-seccion">Seis algoritmos, un mismo negocio. '
            "<span>Edita los datos y mira cómo cambia la decisión.</span></div>", unsafe_allow_html=True)
fila_1 = st.columns(3, gap="medium")
fila_2 = st.columns(3, gap="medium")
with fila_1[0]:
    tarjeta_bento("clientes", mini_clientes(), "Sprint 2 · Sistema experto", "Clientes de la semana",
                  "Reglas de inclusión, vetos y prioridades deciden quién entra en la ruta y por qué.",
                  "clientes_semana.py", "Decidir clientes")
with fila_1[1]:
    tarjeta_bento("ruta", mini_ruta(), "Sprint 1 · Búsqueda A*", "Ruta óptima",
                  "El camino más corto de cada tramo sobre el mapa, con la traza de g, h y f.",
                  "ruta_optima.py", "Ver la ruta")
with fila_1[2]:
    tarjeta_bento("viabilidad", mini_difusa(), "Sprint 2 + 4 · Lógica difusa", "Viabilidad de productos",
                  "De «todas las luces en verde» a una nota de 0 a 100 con 45 reglas Mamdani.",
                  "viabilidad.py", "Calificar productos")
with fila_2[0]:
    tarjeta_bento("lanzar", mini_ag(), "Sprint 3A · Algoritmo genético", "Qué lanzar",
                  "Cromosomas, cruce y mutación eligen el portafolio que cabe en presupuesto y bodega.",
                  "que_lanzar.py", "Optimizar el portafolio")
with fila_2[1]:
    tarjeta_bento("competidor", mini_competidor(), "Sprint 3B · Teoría de juegos", "Competidor",
                  "Matriz de pagos, equilibrio de Nash y Minimax: el portafolio que mejor aguanta a un rival.",
                  "competidor.py", "Simular al rival")
with fila_2[2]:
    tarjeta_bento("desempate", mini_desempate(), "Sprint 4 · Lógica difusa", "Desempate difuso",
                  "Cuando dos portafolios dejan la misma utilidad, la nota y la exposición deciden.",
                  "desempate_difuso.py", "Resolver empates")

# --- Sección dividida: cómo se conectan ---
st.markdown(
    f"""
    <div class="mm-dividida">
      <div class="oscuro">
        <h3>Los sprints no son ejercicios sueltos: son un sistema.</h3>
        <p>El sistema experto le entrega sus clientes y prioridades a A*. El algoritmo genético le pasa su
        portafolio al análisis del competidor, y la lógica difusa califica los productos y desempata los
        portafolios que quedan iguales. La navegación sigue esas dos cadenas de decisión.</p>
      </div>
      <div class="claro">{svg_cadena()}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Línea de tiempo ---
st.markdown('<div class="mm-seccion">Un semestre, cuatro sprints. <span>IA simbólica, sin machine learning.</span></div>',
            unsafe_allow_html=True)
st.markdown(
    """
    <div class="mm-linea">
      <div class="mm-hito"><small>Sprint 1 · Completado</small><b>Búsqueda A*</b>
        <span>Ruta más corta entre la bodega, los clientes y la plataforma logística.</span></div>
      <div class="mm-hito"><small>Sprint 2 · Completado</small><b>Sistemas expertos</b>
        <span>Quién entra en la ruta y si una categoría es viable.</span></div>
      <div class="mm-hito"><small>Sprint 3 · Completado</small><b>Genético + teoría de juegos</b>
        <span>Qué lanzar con recursos limitados y cómo protegerse de un rival.</span></div>
      <div class="mm-hito propuesta"><small>Sprint 4 · Propuesta lista</small><b>Lógica difusa</b>
        <span>Nota de viabilidad 0–100 y desempate de portafolios.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Cierre: equipo ---
st.markdown(
    """
    <div class="mm-cierre">
      <div><b>Jacobo Argote · Andrés Cardona · Miguel Valencia · Juan José Gil</b><br>
        <span>Fundamentos de Inteligencia Artificial — Universidad EIA</span></div>
      <div style="max-width:30rem"><span>Código desarrollado con apoyo de Claude. La lógica es la de los
        notebooks del equipo, y las pruebas automáticas verifican que los resultados sean idénticos.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)
