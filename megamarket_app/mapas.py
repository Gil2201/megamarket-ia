"""Construcción del mapa Folium de una ruta (página 2).

Se regenera desde Python con los datos del recorrido; la guía de estilo es
`referencia/sprint1/megamarket_mapa_rutas.html` (tiles CartoDB claros y capas
conmutables "Grafo completo" / "Ruta óptima").
"""

import folium

from megamarket.datos import BODEGA, COORDENADAS, PLATAFORMA
from megamarket_app.tema import PALETA, PRIORIDAD

GRIS_CLARO = "#B8C0CC"


def _icono_numero(texto, color, tamano=26):
    """Círculo con un número o letra (orden de visita, B, P)."""
    return folium.DivIcon(
        icon_size=(tamano, tamano),
        icon_anchor=(tamano // 2, tamano // 2),
        html=(
            f'<div style="width:{tamano}px;height:{tamano}px;border-radius:50%;'
            f"background:{color};color:#fff;border:2px solid #fff;"
            "box-shadow:0 1px 3px rgba(0,0,0,.35);display:flex;align-items:center;"
            "justify-content:center;font:700 12px Montserrat,sans-serif;\">"
            f"{texto}</div>"
        ),
    )


def construir_mapa(red, paradas, orden_clientes, prioridad, clientes_de_la_ruta):
    """Mapa de una ruta: grafo, ruta óptima, paradas numeradas y nodos de paso.

    - Paradas de entrega: número de orden de visita, color según prioridad.
    - Nodos de paso: clientes por los que el camión pasa sin entregar (gris).
    - Clientes que no se visitan esta semana: punto gris claro.
    """
    nodos = list(red)
    lats = [COORDENADAS[n][0] for n in nodos]
    lons = [COORDENADAS[n][1] for n in nodos]
    # OpenStreetMap (CARTO ahora exige API key). Se aclara con un filtro CSS
    # para conservar el estilo claro del mapa de referencia del Sprint 1.
    mapa = folium.Map(tiles=None, control_scale=True)
    folium.TileLayer("OpenStreetMap", control=False).add_to(mapa)
    mapa.get_root().header.add_child(folium.Element(
        "<style>.leaflet-tile-pane{filter:grayscale(.85) brightness(1.06) contrast(.9);}</style>"
    ))
    mapa.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(30, 30))

    # --- Capa 1: grafo completo (todas las conexiones con su costo en km) ---
    capa_grafo = folium.FeatureGroup(name="Grafo completo", show=True)
    vistas = set()
    for a, vecinos in red.items():
        for b, costo in vecinos:
            if (b, a) in vistas:
                continue
            vistas.add((a, b))
            folium.PolyLine(
                [COORDENADAS[a], COORDENADAS[b]],
                color=GRIS_CLARO, weight=2, dash_array="5 6",
                tooltip=f"{a} ↔ {b}: {costo} km",
            ).add_to(capa_grafo)
    capa_grafo.add_to(mapa)

    # --- Capa 2: ruta óptima (todas las paradas en orden) ---
    capa_ruta = folium.FeatureGroup(name="Ruta óptima", show=True)
    folium.PolyLine(
        [COORDENADAS[n] for n in paradas],
        color=PALETA["azul_rey"], weight=5, opacity=0.85,
        tooltip="Ruta óptima",
    ).add_to(capa_ruta)
    capa_ruta.add_to(mapa)

    # --- Puntos (siempre visibles) ---
    numero = {c: i + 1 for i, c in enumerate(orden_clientes)}
    for nodo in nodos:
        coordenada = COORDENADAS[nodo]
        if nodo == BODEGA:
            folium.Marker(coordenada, icon=_icono_numero("B", PALETA["azul_noche"], 30),
                          tooltip=f"{nodo} (salida)").add_to(mapa)
        elif nodo == PLATAFORMA:
            folium.Marker(coordenada, icon=_icono_numero("P", PALETA["azul_noche"], 30),
                          tooltip=f"{nodo} (llegada · coordenada estimada)").add_to(mapa)
        elif nodo in numero:
            nivel = prioridad.get(nodo, "NORMAL")
            etiqueta = f"{numero[nodo]}. {nodo}" + ("" if nivel == "NORMAL" else f" · prioridad {nivel}")
            folium.Marker(coordenada, icon=_icono_numero(numero[nodo], PRIORIDAD[nivel]),
                          tooltip=etiqueta).add_to(mapa)
        elif nodo in clientes_de_la_ruta:
            de_paso = nodo in paradas
            folium.CircleMarker(
                coordenada, radius=7 if de_paso else 5,
                color=PALETA["gris"] if de_paso else GRIS_CLARO,
                fill=True, fill_opacity=0.9 if de_paso else 0.6,
                tooltip=f"{nodo} · " + ("el camión pasa sin entregar" if de_paso else "no se visita esta semana"),
            ).add_to(mapa)
        else:  # accesos viales
            folium.CircleMarker(
                coordenada, radius=5, color=PALETA["azul_medio"], fill=True, fill_opacity=1,
                tooltip=f"{nodo} (acceso vial)",
            ).add_to(mapa)

    folium.LayerControl(collapsed=False).add_to(mapa)
    return mapa
