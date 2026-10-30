"""Sprint 1 — Ruta óptima para MegaMarket con A*.

Portado de `referencia/sprint1/MegaMarket_Sprint1_AEstrella.ipynb`.
`recorrido_completo` es la versión del Sprint 2 (Parte 0.1), que agrega el
parámetro opcional `prioridad`: sin prioridad da exactamente el resultado
del Sprint 1.

Adaptaciones permitidas (SPEC §5.2): se quitó el bloque de ejecución con
`print` y se agregó `a_estrella_con_traza` AL LADO de `a_estrella` para
mostrar en la app cómo explora el algoritmo.

## Notación (la misma vista en clase)

- `g(n)`: costo real acumulado desde el origen hasta el nodo `n`.
- `h(n)`: heurística, una estimación de lo que falta hasta el destino.
- `f(n) = g(n) + h(n)`: costo total estimado; ordena la cola de prioridad.

## ¿Cómo calculamos la heurística h(n)?

En el ejemplo de clase la heurística era un número fijo por nodo, porque solo
había un destino ("Cliente"). Acá cada ruta tiene **varios clientes distintos**
y ahora también un destino final compartido, así que en vez de escribir un
número a mano por cada combinación posible, calculamos h(n) como la
**distancia en línea recta** entre las coordenadas del nodo actual y las del
destino (fórmula de *haversine*).

Como la distancia en línea recta nunca puede ser mayor que la distancia real
por las calles, h(n) es **admisible** y A* garantiza la ruta óptima.
"""

from heapq import heappush, heappop
from math import radians, sin, cos, asin, sqrt

from megamarket.datos import COORDENADAS, clientes_poblado, clientes_valle_aburra


# =============================================================================
# 2. HEURÍSTICA h(n): distancia en línea recta (haversine)
# =============================================================================
def heuristica(nodo, destino):
    """Distancia en línea recta entre dos lugares, en kilómetros.

    Es el mismo concepto de "distancia en línea recta hasta el objetivo"
    que vimos en clase, calculado a partir de las coordenadas reales.
    """
    lat1, lon1 = COORDENADAS[nodo]
    lat2, lon2 = COORDENADAS[destino]
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    d_lat = lat2 - lat1
    d_lon = lon2 - lon1
    aux = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lon / 2) ** 2
    return 2 * 6371.0 * asin(sqrt(aux))  # 6371 km = radio de la Tierra


# =============================================================================
# 3. GRAFOS DE CADA RUTA
#    Igual que en clase: diccionario {nodo: [(vecino, costo_km), ...]}.
#    El camión primero llega al acceso vial de la zona y desde ahí reparte
#    a cada cliente. Las calles se recorren en los dos sentidos, así que
#    cada conexión se agrega también "de regreso" (por eso usamos la
#    función conectar() en vez de escribir cada arista dos veces a mano).
# =============================================================================
def conectar(red, a, b, costo):
    """Agrega una conexión en AMBOS sentidos (a->b y b->a), porque una calle
    se puede recorrer de ida y de vuelta."""
    red.setdefault(a, []).append((b, costo))
    red.setdefault(b, []).append((a, costo))


red_poblado = {}
conectar(red_poblado, "Bodega Olaya Herrera", "Acceso Poblado (Aguacatala)", 3.2)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Fruver del Río", 3.2)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Fruver Visitación", 2.3)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Five Sisters", 2.2)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Supermercado Merka 10", 2.1)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Hotel Four Points", 1.3)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Mercados Verona", 2.4)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "EAFIT La Bodeguita", 0.8)
conectar(red_poblado, "Acceso Poblado (Aguacatala)", "Redetrans", 2.7)

red_valle_aburra = {}
conectar(red_valle_aburra, "Bodega Olaya Herrera", "Acceso Sur (Itagüí Centro)", 5.8)
conectar(red_valle_aburra, "Acceso Sur (Itagüí Centro)", "CEDI Vaquita Itagüí", 0.4)
conectar(red_valle_aburra, "Acceso Sur (Itagüí Centro)", "CEDI Euro La Estrella", 3.2)
conectar(red_valle_aburra, "Acceso Sur (Itagüí Centro)", "CEDI Merkepaisa", 1.3)
conectar(red_valle_aburra, "Acceso Sur (Itagüí Centro)", "CEDI Supermú", 1.9)

# --- Conectamos la Plataforma Logística a cada ruta ---
# En vez de escribir el km a mano, usamos heuristica() (línea recta entre
# coordenadas) para calcular la distancia al punto de la ruta más cercano.
# Poblado: se conecta por su acceso vial (Aguacatala). Valle de Aburrá: se
# conecta por su acceso vial (Itagüí Centro).
conectar(
    red_poblado, "Acceso Poblado (Aguacatala)", "Plataforma Logística",
    round(heuristica("Acceso Poblado (Aguacatala)", "Plataforma Logística"), 1),
)
conectar(
    red_valle_aburra, "Acceso Sur (Itagüí Centro)", "Plataforma Logística",
    round(heuristica("Acceso Sur (Itagüí Centro)", "Plataforma Logística"), 1),
)

# --- Conexiones directas entre tiendas cercanas de la misma ruta ---
# Hasta acá, el único camino entre dos tiendas es pasando por el acceso
# vial de la zona. En la práctica, si dos tiendas quedan muy cerca, el
# camión va de una a la otra directo, sin devolverse a la vía principal.
# Igual que en el proyecto original: conectamos los pares que quedan a
# menos de UMBRAL_CERCANIA_KM en línea recta.
UMBRAL_CERCANIA_KM = 1.5


def conectar_clientes_cercanos(red, clientes, umbral=UMBRAL_CERCANIA_KM):
    """Conecta directo los pares de clientes a menos de `umbral` km en línea recta."""
    for i in range(len(clientes)):
        for j in range(i + 1, len(clientes)):
            a, b = clientes[i], clientes[j]
            distancia = heuristica(a, b)
            if distancia < umbral:
                conectar(red, a, b, round(distancia, 2))


conectar_clientes_cercanos(red_poblado, clientes_poblado)
conectar_clientes_cercanos(red_valle_aburra, clientes_valle_aburra)

# Grafo de cada ruta, por nombre (Sprint 2, sección 9)
REDES = {"Poblado": red_poblado, "Valle de Aburrá": red_valle_aburra}


# =============================================================================
# 4. A* (A-Star) — misma estructura vista en clase
# =============================================================================
def a_estrella(red, origen, destino):
    """Camino más corto de `origen` a `destino` en la red.

    Devuelve (camino, costo_km), o (None, None) si no hay camino.
    """
    # Inicializamos la cola de prioridad con: (f(n), g(n), camino)
    # f(n) = g(n) + h(n) -> Costo Total Proyectado
    cola = [(heuristica(origen, destino), 0, [origen])]
    visitados = set()

    while cola:
        # Extraemos el nodo con el menor f(n) (el más prometedor)
        f, g, camino = heappop(cola)
        nodo_actual = camino[-1]

        # Si el nodo actual es el destino, hemos terminado con éxito
        if nodo_actual == destino:
            return camino, g

        if nodo_actual not in visitados:
            visitados.add(nodo_actual)

            # Exploramos las conexiones del nodo actual
            for vecino, costo in red[nodo_actual]:
                # g(n) es el costo acumulado real desde el origen
                nuevo_g = g + costo
                # f(n) = g acumulado + estimación h del vecino
                nuevo_f = nuevo_g + heuristica(vecino, destino)

                heappush(cola, (nuevo_f, nuevo_g, camino + [vecino]))

    return None, None


def a_estrella_con_traza(red, origen, destino):
    """Igual a `a_estrella`, pero además devuelve la traza de la exploración.

    Variante instrumentada (SPEC §5.2): la lógica es idéntica; solo se
    anota cada nodo que sale de la cola con sus valores g, h y f.
    Devuelve (camino, costo_km, traza), donde traza es una lista de dicts
    {"paso", "nodo", "g", "h", "f", "camino", "accion"}.
    """
    cola = [(heuristica(origen, destino), 0, [origen])]
    visitados = set()
    traza = []

    while cola:
        f, g, camino = heappop(cola)
        nodo_actual = camino[-1]

        paso = {
            "paso": len(traza) + 1,
            "nodo": nodo_actual,
            "g": g,
            "h": f - g,
            "f": f,
            "camino": list(camino),
        }
        traza.append(paso)

        if nodo_actual == destino:
            paso["accion"] = "destino"
            return camino, g, traza

        if nodo_actual not in visitados:
            visitados.add(nodo_actual)
            paso["accion"] = "expandir"

            for vecino, costo in red[nodo_actual]:
                nuevo_g = g + costo
                nuevo_f = nuevo_g + heuristica(vecino, destino)

                heappush(cola, (nuevo_f, nuevo_g, camino + [vecino]))
        else:
            paso["accion"] = "ya visitado"

    return None, None, traza


# =============================================================================
# 5. RECORRIDO COMPLETO DE REPARTO (Sprint 1 + tandas de prioridad del Sprint 2)
#    El camión sale UNA sola vez de la bodega, visita a todos los clientes
#    de la ruta y termina en destino_final. En cada paso usamos A* para ir
#    del punto donde estamos hasta el cliente sin visitar más cercano
#    ("vecino más cercano"): es una estrategia sencilla, no prueba todas
#    las combinaciones posibles, así que no garantiza el orden más corto de
#    TODOS los órdenes posibles.
# =============================================================================
def recorrido_completo(red, origen, clientes, destino_final=None, prioridad=None):
    """Recorrido de reparto: sale de 'origen', visita cada cliente una sola
    vez y termina en 'destino_final'.

    'prioridad' es un diccionario opcional {cliente: "ALTA"/"MEDIA"/"BAJA"}
    que viene del sistema experto. Los clientes se atienden en tandas: se
    agota TODA la tanda de mayor prioridad (con vecino más cercano dentro
    de la tanda) antes de pasar a la siguiente. Si no se indica prioridad,
    todos quedan en una sola tanda ("NORMAL") y el resultado es idéntico
    al del Sprint 1.

    Devuelve (paradas, distancia_total, orden_clientes): todos los nodos
    por los que pasa el camión, los km totales y el orden de entrega.
    """
    if destino_final is None:
        destino_final = origen
    if prioridad is None:
        prioridad = {c: "NORMAL" for c in clientes}

    orden_tandas = ["ALTA", "MEDIA", "BAJA", "NORMAL"]
    tandas = {
        nivel: [c for c in clientes if prioridad.get(c, "NORMAL") == nivel]
        for nivel in orden_tandas
    }

    paradas = [origen]
    orden_clientes = []
    posicion_actual = origen
    distancia_total = 0

    # Recorremos cada tanda en orden de prioridad (ALTA -> MEDIA -> BAJA/NORMAL)
    for nivel in orden_tandas:
        pendientes = tandas[nivel]

        # Dentro de cada tanda, exactamente el mismo "vecino más cercano" del Sprint 1
        while pendientes:
            # Entre los clientes que faltan, buscamos el más cercano desde
            # donde estamos parados ahora mismo (no siempre desde la bodega)
            mejor_cliente, mejor_camino, mejor_costo = None, None, float("inf")
            for cliente in pendientes:
                camino, costo = a_estrella(red, posicion_actual, cliente)
                if costo < mejor_costo:
                    mejor_cliente, mejor_camino, mejor_costo = cliente, camino, costo

            paradas.extend(mejor_camino[1:])  # evitamos repetir el nodo de partida
            orden_clientes.append(mejor_cliente)
            distancia_total += mejor_costo
            posicion_actual = mejor_cliente
            pendientes.remove(mejor_cliente)

    # Último tramo: hacia destino_final (la bodega, por defecto, o el
    # punto final que se haya indicado)
    camino_final, costo_final = a_estrella(red, posicion_actual, destino_final)
    paradas.extend(camino_final[1:])
    distancia_total += costo_final

    return paradas, distancia_total, orden_clientes
