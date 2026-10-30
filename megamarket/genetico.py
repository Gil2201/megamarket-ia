"""Sprint 3A — ¿Qué referencias nuevas lanzamos con el presupuesto que tenemos?

Portado de `referencia/sprint3/MegaMarket_Sprint3A_AG_Portafolio.ipynb`.
Es la versión "mochila" (knapsack) del algoritmo genético del cuaderno del
profesor: en vez de escoger el orden de una ruta, escogemos *cuáles*
productos entran.

Un individuo es una cadena de bits, un gen por candidato, en el mismo
orden que los nombres de `candidatos`:  (1, 0, 1, 1, 0, 0, 0, 1)
El gen en la posición i vale 1 si el candidato i se lanza, y 0 si no.

Adaptación permitida (SPEC §5.2, regla 2): en el notebook las funciones
leen las globales CANDIDATOS, NOMBRES, N_GENES, PRESUPUESTO_TOTAL y
ESPACIO_BODEGA_TOTAL. Aquí las reciben como parámetros (`candidatos`,
`presupuesto`, `espacio`) con esos mismos valores por defecto, para que la
app pueda editarlos. Dentro de cada función, `nombres = list(candidatos)`
y `n_genes = len(nombres)` cumplen el papel de NOMBRES y N_GENES.
Con los valores por defecto el resultado es idéntico al del notebook.

OJO: este AG es DISTINTO al de competidor.py (Sprint 3B). Aquí el fitness
es utilidad + 1 y la ruleta es simple. No se unifican (SPEC §5.2).

> Nota: los montos de costo, espacio y utilidad son ficticios.
"""

import itertools
import random

import pandas as pd

from megamarket.datos import CANDIDATOS, ESPACIO_BODEGA_TOTAL, PRESUPUESTO_TOTAL, SEMILLA


# =============================================================================
# 3. FUNCIONES BÁSICAS SOBRE UN INDIVIDUO (portafolio candidato)
# =============================================================================
def costo_total(individuo, candidatos=CANDIDATOS):
    """Suma el costo de lanzamiento de los productos incluidos (gen = 1)."""
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["costo_lanzamiento"] for i in range(len(nombres)) if individuo[i] == 1)


def espacio_total(individuo, candidatos=CANDIDATOS):
    """Suma el espacio de bodega de los productos incluidos."""
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["espacio_bodega"] for i in range(len(nombres)) if individuo[i] == 1)


def utilidad_total(individuo, candidatos=CANDIDATOS):
    """Suma la utilidad esperada de los productos incluidos."""
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["utilidad_esperada_anual"] for i in range(len(nombres)) if individuo[i] == 1)


def es_portafolio_valido(individuo, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Un portafolio es válido si respeta el presupuesto Y el espacio a la vez."""
    return costo_total(individuo, candidatos) <= presupuesto and espacio_total(individuo, candidatos) <= espacio


def nombre_incluidos(individuo, candidatos=CANDIDATOS):
    """Lista los nombres de los productos incluidos en este individuo."""
    nombres = list(candidatos)
    return [nombres[i] for i in range(len(nombres)) if individuo[i] == 1]


# =============================================================================
# 4. REPARACIÓN
#    Mientras el portafolio no sea válido, se retira el producto incluido con
#    la peor relación utilidad/costo (el que peor retorno da por cada peso
#    invertido), uno a la vez. Retirar un producto libera presupuesto y
#    espacio simultáneamente, así que basta con mirar un solo criterio.
# =============================================================================
def reparar_portafolio(individuo, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Retira, uno a uno, el producto incluido con peor utilidad por peso
    invertido, hasta que el portafolio vuelva a caber en presupuesto y
    espacio a la vez."""
    nombres = list(candidatos)
    n_genes = len(nombres)
    individuo = list(individuo)

    while not es_portafolio_valido(individuo, candidatos, presupuesto, espacio):
        incluidos = [i for i in range(n_genes) if individuo[i] == 1]

        peor = min(
            incluidos,
            key=lambda i: candidatos[nombres[i]]["utilidad_esperada_anual"]
                          / candidatos[nombres[i]]["costo_lanzamiento"],
        )
        individuo[peor] = 0

    return tuple(individuo)


# =============================================================================
# 5. FITNESS, POBLACIÓN Y SELECCIÓN
#    El fitness es la utilidad esperada total; se le suma 1 para que ningún
#    portafolio (ni siquiera uno vacío) tenga fitness cero, lo que rompería
#    la selección por ruleta (necesita pesos positivos).
# =============================================================================
def calcular_fitness(individuo, candidatos=CANDIDATOS):
    """La utilidad total es el fitness. El +1 evita pesos en cero."""
    return utilidad_total(individuo, candidatos) + 1


def crear_individuo(candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Cada gen se decide al azar (lanzar o no ese producto); si el
    resultado no cabe en presupuesto/espacio, se repara."""
    n_genes = len(candidatos)
    candidato = tuple(random.choice([0, 1]) for _ in range(n_genes))
    return reparar_portafolio(candidato, candidatos, presupuesto, espacio)


def crear_poblacion(tamano, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Crea una lista con la cantidad solicitada de portafolios (todos válidos)."""
    return [crear_individuo(candidatos, presupuesto, espacio) for _ in range(tamano)]


def seleccionar_por_ruleta(poblacion, candidatos=CANDIDATOS):
    """Selecciona un individuo con probabilidad proporcional a su fitness."""
    pesos = [calcular_fitness(individuo, candidatos) for individuo in poblacion]
    return random.choices(poblacion, weights=pesos, k=1)[0]


# =============================================================================
# 6. CRUCE Y MUTACIÓN
# =============================================================================
def cruzar(padre_1, padre_2, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Cruce de un punto sobre la cadena de bits; repara si es necesario."""
    n_genes = len(candidatos)
    punto_corte = random.randint(1, n_genes - 1)
    candidato = padre_1[:punto_corte] + padre_2[punto_corte:]
    hijo = reparar_portafolio(candidato, candidatos, presupuesto, espacio)

    assert es_portafolio_valido(hijo, candidatos, presupuesto, espacio)
    return hijo


def mutar(individuo, probabilidad=0.10, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Voltea un gen al azar (incluir <-> excluir un producto) y repara."""
    if random.random() >= probabilidad:
        return individuo

    n_genes = len(candidatos)
    posicion = random.randrange(n_genes)
    mutado = list(individuo)
    mutado[posicion] = 1 - mutado[posicion]
    mutado = reparar_portafolio(mutado, candidatos, presupuesto, espacio)

    assert es_portafolio_valido(mutado, candidatos, presupuesto, espacio)
    return mutado


# =============================================================================
# 7. ALGORITMO GENÉTICO — PORTAFOLIO
#    Mismo ciclo del cuaderno del profesor, con "ruta" cambiado por
#    "portafolio": evaluar, elitismo, seleccionar padres, cruzar y reparar,
#    mutar, repetir.
# =============================================================================
def algoritmo_genetico_portafolio(
    poblacion_inicial,
    generaciones=15,
    probabilidad_mutacion=0.10,
    elitismo=1,
    candidatos=CANDIDATOS,
    presupuesto=PRESUPUESTO_TOTAL,
    espacio=ESPACIO_BODEGA_TOTAL,
):
    """Ejecuta el algoritmo genético sobre portafolios y registra su evolución.

    Responde: ¿qué referencias lanzamos para maximizar la utilidad sin
    pasarnos del presupuesto ni del espacio de bodega?
    Devuelve (mejor_portafolio, historial) — historial es un DataFrame con
    "Generación", "Mejor utilidad", "Utilidad promedio" y "Diversidad".
    """
    poblacion = list(poblacion_inicial)
    tamano_poblacion = len(poblacion)
    historial = []

    for generacion in range(generaciones + 1):

        # 1. EVALUACIÓN
        poblacion.sort(key=lambda individuo: calcular_fitness(individuo, candidatos), reverse=True)

        historial.append({
            "Generación": generacion,
            "Mejor utilidad": utilidad_total(poblacion[0], candidatos),
            "Utilidad promedio": sum(utilidad_total(ind, candidatos) for ind in poblacion) / tamano_poblacion,
            "Diversidad": len(set(poblacion)),
        })

        if generacion == generaciones:
            break

        # 2. ELITISMO
        nueva_poblacion = poblacion[:elitismo]

        # 3. REPRODUCCIÓN
        while len(nueva_poblacion) < tamano_poblacion:
            padre_1 = seleccionar_por_ruleta(poblacion, candidatos)
            padre_2 = seleccionar_por_ruleta(poblacion, candidatos)

            hijo = cruzar(padre_1, padre_2, candidatos, presupuesto, espacio)
            hijo = mutar(hijo, probabilidad_mutacion, candidatos, presupuesto, espacio)

            nueva_poblacion.append(hijo)

        poblacion = nueva_poblacion

    mejor_portafolio = poblacion[0]
    return mejor_portafolio, pd.DataFrame(historial)


def ejecutar_experimento(
    tamano_poblacion=10,
    generaciones=15,
    probabilidad_mutacion=0.10,
    elitismo=1,
    semilla=SEMILLA,
    candidatos=CANDIDATOS,
    presupuesto=PRESUPUESTO_TOTAL,
    espacio=ESPACIO_BODEGA_TOTAL,
):
    """Experimento reproducible (sección 8 del notebook): reinicia la
    semilla, crea la población inicial y corre el AG.

    Devuelve (mejor_portafolio, historial), igual que algoritmo_genetico_portafolio.
    """
    random.seed(semilla)
    POBLACION_INICIAL = crear_poblacion(tamano_poblacion, candidatos, presupuesto, espacio)

    return algoritmo_genetico_portafolio(
        poblacion_inicial=POBLACION_INICIAL,
        generaciones=generaciones,
        probabilidad_mutacion=probabilidad_mutacion,
        elitismo=elitismo,
        candidatos=candidatos,
        presupuesto=presupuesto,
        espacio=espacio,
    )


# =============================================================================
# Parte 7 — VALIDACIÓN CON FUERZA BRUTA
#    La búsqueda exhaustiva comprueba el resultado; no forma parte del AG.
# =============================================================================
def validar_con_fuerza_bruta(candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Revisa las 2^n combinaciones posibles y devuelve el control del AG.

    El ciclo es el mismo del notebook (se queda con la PRIMERA combinación
    que alcanza la mejor utilidad). Además devuelve todos los portafolios
    empatados en esa utilidad y la lista de portafolios válidos, igual que
    la `fuerza_bruta` del notebook 3B, para poder mostrar los empates.

    Devuelve {"mejor_fuerza_bruta", "mejor_utilidad_fb", "optimos", "validas"}.
    """
    n_genes = len(candidatos)

    mejor_fuerza_bruta, mejor_utilidad_fb = None, -1
    validas = []
    for combinacion in itertools.product([0, 1], repeat=n_genes):
        if es_portafolio_valido(combinacion, candidatos, presupuesto, espacio):
            validas.append(combinacion)
            if utilidad_total(combinacion, candidatos) > mejor_utilidad_fb:
                mejor_fuerza_bruta = combinacion
                mejor_utilidad_fb = utilidad_total(combinacion, candidatos)

    optimos = [c for c in validas if utilidad_total(c, candidatos) == mejor_utilidad_fb]

    return {
        "mejor_fuerza_bruta": mejor_fuerza_bruta,
        "mejor_utilidad_fb": mejor_utilidad_fb,
        "optimos": optimos,
        "validas": validas,
    }
