"""Sprint 3B — ¿Qué pasa con el portafolio óptimo si un competidor reacciona?

Portado de `referencia/sprint3/MegaMarket_Sprint3B_AG_Minimax_Competidor.ipynb`.

| Herramienta | Qué hace |
|---|---|
| Teoría de juegos (matriz de pagos, Nash, Minimax) | EVALÚA una decisión cuando el rival reacciona |
| Algoritmo genético | BUSCA entre las combinaciones y usa esa calificación como fitness |

Adaptaciones permitidas (SPEC §5.2):
- Las globales CANDIDATOS, NOMBRES, N_GENES, PRESUPUESTO_TOTAL,
  ESPACIO_BODEGA_TOTAL, EROSION y K_ATAQUES se reciben como parámetros
  (`candidatos`, `presupuesto`, `espacio`, `erosion`, `k`) con esos mismos
  valores por defecto. `nombres = list(candidatos)` hace el papel de NOMBRES.
- `mostrar_caso` y `mostrar_arbol` conservan su nombre pero DEVUELVEN los
  datos que antes imprimían.
- El código suelto de las celdas (experimento, robustez, sensibilidad,
  tabla de erosión de equilibrio) quedó en funciones que devuelven datos.

OJO: este AG es DISTINTO al de genetico.py (Sprint 3A): aquí la ruleta usa
fitness escalado, la reparación mira la utilidad después de la erosión y el
criterio es configurable. No se unifican (SPEC §5.2).

> Nota: los costos, espacios y utilidades son ficticios. La erosión y los
> pagos del rival son SUPUESTOS ILUSTRATIVOS.
"""

import itertools
import random

import numpy as np
import pandas as pd

from megamarket.datos import (
    CANDIDATOS,
    EROSION,
    ESPACIO_BODEGA_TOTAL,
    K_ATAQUES,
    PRESUPUESTO_TOTAL,
    SEMILLA,
)


def corto(n):
    """Nombre corto del producto (sin " Riovalle")."""
    return n.replace(" Riovalle", "")


# =============================================================================
# 2. EROSIÓN DE EQUILIBRIO — hasta dónde aguanta cada producto
#    Es el porcentaje de utilidad que el rival nos puede quitar antes de que
#    lanzar deje de pagarse en el primer año: 1 − costo/utilidad.
# =============================================================================
def erosion_de_equilibrio(nombre, candidatos=CANDIDATOS):
    c = candidatos[nombre]
    return 1 - c["costo_lanzamiento"] / c["utilidad_esperada_anual"]


def tabla_erosion_de_equilibrio(candidatos=CANDIDATOS, erosion=EROSION):
    """Tabla de la sección 2 del notebook. Si la erosión supuesta supera la
    de equilibrio, el producto pierde dinero en el primer año."""
    filas = [{"Producto": corto(n),
              "Utilidad": c["utilidad_esperada_anual"],
              "Costo": c["costo_lanzamiento"],
              "Utilidad neta": c["utilidad_esperada_anual"] - c["costo_lanzamiento"],
              "Erosión de equilibrio": erosion_de_equilibrio(n, candidatos),
              "Erosión supuesta": erosion[n]}
             for n, c in candidatos.items()]
    return filas


# =============================================================================
# 3. MATRIZ DE PAGOS 2x2, NASH E INDUCCIÓN HACIA ATRÁS
# =============================================================================
def matriz_producto(nombre, erosion, rival_entra_vs_lanza, rival_entra_vs_no_lanza, candidatos=CANDIDATOS):
    """Filas: Riovalle (Lanzar, No lanzar). Columnas: Rival (Entrar, No entrar). Pagos en COP."""
    c = candidatos[nombre]
    u, costo = c["utilidad_esperada_anual"], c["costo_lanzamiento"]
    A = np.array([[u * (1 - erosion) - costo, u - costo],     # pago de Riovalle
                  [0.0,                       0.0]])
    B = np.array([[rival_entra_vs_lanza,      0.0],            # pago del rival
                  [rival_entra_vs_no_lanza,   0.0]])
    return A, B


def nash_puro(A, B):
    """Celdas donde ninguno mejora cambiando solo (el subrayado de la clase)."""
    nash = []
    for i in range(2):
        for j in range(2):
            if A[i, j] >= A[:, j].max() - 1e-9 and B[i, j] >= B[i, :].max() - 1e-9:
        # ¿Es A[i,j] el máximo de su columna? (mejor respuesta de Riovalle)
        # ¿Es B[i,j] el máximo de su fila? (mejor respuesta del rival)
                nash.append((i, j))
    return nash


def solucion_secuencial(A, B):
    """Riovalle mueve primero; el rival responde con su mejor respuesta (inducción hacia atrás)."""
    respuesta = [int(np.argmax(B[i, :])) for i in range(2)]          # mejor respuesta del rival a cada jugada
    i = int(np.argmax([A[i, respuesta[i]] for i in range(2)]))        # Riovalle escoge sabiendo eso
    return i, respuesta[i]


FILAS, COLS = ["Lanzar", "No lanzar"], ["Entrar", "No entrar"]


def mostrar_caso(titulo, nombre, erosion, rival_entra_vs_lanza, rival_entra_vs_no_lanza, candidatos=CANDIDATOS):
    """Resuelve el juego 2x2 de un producto.

    Responde: si el rival puede entrar con un producto parecido, ¿nos
    conviene lanzar? Devuelve {"titulo", "producto", "A", "B", "nash",
    "secuencial", "pago_riovalle", "pago_rival"}; A y B son listas 2x2 en
    COP, nash y secuencial son pares (fila, columna) sobre FILAS y COLS.
    """
    A, B = matriz_producto(nombre, erosion, rival_entra_vs_lanza, rival_entra_vs_no_lanza, candidatos)
    nash = nash_puro(A, B)
    i, j = solucion_secuencial(A, B)
    return {
        "titulo": titulo,
        "producto": nombre,
        "A": A.tolist(),
        "B": B.tolist(),
        "nash": nash,
        "secuencial": (i, j),
        "pago_riovalle": float(A[i, j]),
        "pago_rival": float(B[i, j]),
    }


JUGO = "Jugo Natural Riovalle"

# Los tres casos del notebook: (titulo, nombre, erosion, rival_entra_vs_lanza, rival_entra_vs_no_lanza)
CASOS_JUGO = {
    "A": ("Caso A: el rival le quita 35% y entrar le conviene siempre", JUGO, 0.35, 6e6, 18e6),
    "B": ("Caso B: el rival le quita 50% y entrar le conviene siempre", JUGO, 0.50, 6e6, 18e6),
    "C": ("Caso C: el rival le quita 50% pero entrar contra un producto ya lanzado le da pérdida", JUGO, 0.50, -3e6, 18e6),
}


# =============================================================================
# 4. FUNCIONES SOBRE UN PORTAFOLIO Y MINIMAX
#    MAX (Riovalle) escoge el portafolio. MIN (el rival) escoge el producto
#    que más daño nos haga. Daño = utilidad × erosión.
#    Valor del portafolio en el peor caso = utilidad esperada total − pérdida
#    máxima que el rival puede causar. El árbol es de solo dos niveles, por
#    lo que no hace falta poda Alfa-Beta: basta calcular el máximo de las pérdidas.
# =============================================================================
def costo_total(ind, candidatos=CANDIDATOS):
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["costo_lanzamiento"] for i in range(len(nombres)) if ind[i] == 1)

def espacio_total(ind, candidatos=CANDIDATOS):
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["espacio_bodega"] for i in range(len(nombres)) if ind[i] == 1)

def utilidad_total(ind, candidatos=CANDIDATOS):
    nombres = list(candidatos)
    return sum(candidatos[nombres[i]]["utilidad_esperada_anual"] for i in range(len(nombres)) if ind[i] == 1)

def es_portafolio_valido(ind, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    return costo_total(ind, candidatos) <= presupuesto and espacio_total(ind, candidatos) <= espacio

def nombre_incluidos(ind, candidatos=CANDIDATOS):
    nombres = list(candidatos)
    return [corto(nombres[i]) for i in range(len(nombres)) if ind[i] == 1]


def perdidas_por_ataque(ind, erosion=None, candidatos=CANDIDATOS):
    """Pérdida de utilidad si el rival ataca cada producto incluido (nivel MIN del árbol)."""
    erosion = erosion or EROSION
    nombres = list(candidatos)
    return {nombres[i]: candidatos[nombres[i]]["utilidad_esperada_anual"] * erosion[nombres[i]]
            for i in range(len(nombres)) if ind[i] == 1}


def perdida_maxima(ind, erosion=None, k=None, candidatos=CANDIDATOS):
    k = K_ATAQUES if k is None else k
    perdidas = sorted(perdidas_por_ataque(ind, erosion, candidatos).values(), reverse=True)
    return sum(perdidas[:k])


def utilidad_peor_caso(ind, erosion=None, k=None, candidatos=CANDIDATOS):
    """Valor Minimax: lo que nos queda cuando el rival hace el máximo daño.

    Responde: ¿cuánta utilidad deja este portafolio si el rival ataca
    los k productos donde más daño hace?
    """
    return utilidad_total(ind, candidatos) - perdida_maxima(ind, erosion, k, candidatos)


def mostrar_arbol(ind, etiqueta, erosion=None, candidatos=CANDIDATOS):
    """Árbol de dos niveles: Riovalle escoge el portafolio y el rival escoge a qué producto atacar.

    Devuelve {"etiqueta", "productos", "utilidad_esperada", "ataques",
    "rival_ataca", "valor_minimax"}; "ataques" es la lista de
    (producto, utilidad que queda) ordenada de peor a mejor para Riovalle.
    """
    resultados = {n: utilidad_total(ind, candidatos) - p for n, p in perdidas_por_ataque(ind, erosion, candidatos).items()}
    ataques = [(corto(n), v) for n, v in sorted(resultados.items(), key=lambda kv: kv[1])]
    peor = min(resultados, key=resultados.get)
    return {
        "etiqueta": etiqueta,
        "productos": nombre_incluidos(ind, candidatos),
        "utilidad_esperada": utilidad_total(ind, candidatos),
        "ataques": ataques,
        "rival_ataca": corto(peor),
        "valor_minimax": resultados[peor],
    }


# El portafolio que escogió el AG del Sprint 3
PORTAFOLIO_SPRINT3 = tuple(1 if n in ("Higo Deshidratado Riovalle", "Jugo Natural Riovalle", "Café Molido Riovalle") else 0 for n in CANDIDATOS)


# =============================================================================
# 5. ALGORITMO GENÉTICO — fitness configurable (utilidad esperada o Minimax)
#    | Criterio      | Fitness                              |
#    | "esperada"    | utilidad esperada total (Sprint 3)   |
#    | "peor_caso"   | utilidad en el peor caso (Minimax)   |
#    Tres ajustes menores respecto al Sprint 3:
#    1. En "peor_caso" se desempata por utilidad esperada (un peso muy pequeño).
#    2. La reparación retira el producto con peor utilidad DESPUÉS de la
#       erosión por peso invertido.
#    3. La ruleta usa fitness escalado (diferencia con el peor de la población).
# =============================================================================
def fitness(ind, criterio, erosion=None, k=None, candidatos=CANDIDATOS):
    if criterio == "esperada":
        return utilidad_total(ind, candidatos)
    return utilidad_peor_caso(ind, erosion, k, candidatos) + 0.001 * utilidad_total(ind, candidatos)     # desempate por utilidad esperada


def razon(i, criterio, erosion=None, candidatos=CANDIDATOS): # eficiencia del producto
    erosion = erosion or EROSION
    nombres = list(candidatos)
    c = candidatos[nombres[i]]
    u = c["utilidad_esperada_anual"] * (1 - erosion[nombres[i]] if criterio == "peor_caso" else 1)
    return u / c["costo_lanzamiento"]


def reparar_portafolio(ind, criterio, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL, erosion=None):
    n_genes = len(candidatos)
    ind = list(ind)
    while not es_portafolio_valido(ind, candidatos, presupuesto, espacio):
        incluidos = [i for i in range(n_genes) if ind[i] == 1]
        ind[min(incluidos, key=lambda i: razon(i, criterio, erosion, candidatos))] = 0
    return tuple(ind)


def crear_poblacion(tamano, criterio, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL, erosion=None):
    n_genes = len(candidatos)
    return [reparar_portafolio(tuple(random.choice([0, 1]) for _ in range(n_genes)), criterio, candidatos, presupuesto, espacio, erosion) for _ in range(tamano)]


def seleccionar_por_ruleta(poblacion, criterio, erosion=None, k=None, candidatos=CANDIDATOS):
    valores = [fitness(ind, criterio, erosion, k, candidatos) for ind in poblacion]
    base = min(valores)
    pesos = [(v - base) / 1_000_000 + 1 for v in valores]            # fitness escalado
    return random.choices(poblacion, weights=pesos, k=1)[0]


def cruzar(p1, p2, criterio, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL, erosion=None):
    n_genes = len(candidatos)
    corte = random.randint(1, n_genes - 1)
    hijo = reparar_portafolio(p1[:corte] + p2[corte:], criterio, candidatos, presupuesto, espacio, erosion)
    assert es_portafolio_valido(hijo, candidatos, presupuesto, espacio)
    return hijo


def mutar(ind, criterio, probabilidad=0.10, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL, erosion=None):
    if random.random() >= probabilidad:
        return ind
    n_genes = len(candidatos)
    pos = random.randrange(n_genes)
    mutado = list(ind); mutado[pos] = 1 - mutado[pos]
    mutado = reparar_portafolio(mutado, criterio, candidatos, presupuesto, espacio, erosion)
    assert es_portafolio_valido(mutado, candidatos, presupuesto, espacio)
    return mutado


def ag_portafolio(criterio, poblacion_inicial, generaciones=30, probabilidad_mutacion=0.10, elitismo=1,
                  candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL,
                  erosion=None, k=None):
    """AG del portafolio con criterio "esperada" o "peor_caso" (Minimax).

    Responde: ¿qué portafolio lanzamos si queremos protegernos de un rival?
    Devuelve (mejor, historial) — historial es un DataFrame con "Generación",
    "Mejor utilidad esperada", "Mejor peor caso", "Peor caso promedio" y "Diversidad".
    """
    poblacion = list(poblacion_inicial)
    tamano = len(poblacion)
    historial = []
    for gen in range(generaciones + 1):
        poblacion.sort(key=lambda ind: fitness(ind, criterio, erosion, k, candidatos), reverse=True)
        historial.append({"Generación": gen,
                          "Mejor utilidad esperada": utilidad_total(poblacion[0], candidatos),
                          "Mejor peor caso": utilidad_peor_caso(poblacion[0], erosion, k, candidatos),
                          "Peor caso promedio": sum(utilidad_peor_caso(i, erosion, k, candidatos) for i in poblacion) / tamano,
                          "Diversidad": len(set(poblacion))})
        if gen == generaciones:
            break
        nueva = poblacion[:elitismo]
        while len(nueva) < tamano:
            hijo = cruzar(seleccionar_por_ruleta(poblacion, criterio, erosion, k, candidatos),
                          seleccionar_por_ruleta(poblacion, criterio, erosion, k, candidatos),
                          criterio, candidatos, presupuesto, espacio, erosion)
            nueva.append(mutar(hijo, criterio, probabilidad_mutacion, candidatos, presupuesto, espacio, erosion))
        poblacion = nueva
    return poblacion[0], pd.DataFrame(historial)


def fuerza_bruta(valor, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL):
    """Control: revisa las 2^n combinaciones. Devuelve el mejor valor y todos los portafolios que lo alcanzan."""
    n_genes = len(candidatos)
    validas = [c for c in itertools.product([0, 1], repeat=n_genes) if es_portafolio_valido(c, candidatos, presupuesto, espacio)]
    mejor = max(valor(c) for c in validas)
    return mejor, [c for c in validas if abs(valor(c) - mejor) < 1e-6], validas


# =============================================================================
# 6. EJECUCIÓN Y VALIDACIÓN CON FUERZA BRUTA
# =============================================================================
PARAMS_AG = dict(generaciones=40, probabilidad_mutacion=0.10, elitismo=1)
TAMANO_POBLACION = 30


def ejecutar_ag(criterio, semilla=SEMILLA, tamano_poblacion=TAMANO_POBLACION, generaciones=PARAMS_AG["generaciones"],
                probabilidad_mutacion=PARAMS_AG["probabilidad_mutacion"], elitismo=PARAMS_AG["elitismo"],
                candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL,
                erosion=None, k=None):
    """Corrida reproducible (sección 6 del notebook): reinicia la semilla,
    crea la población con el mismo criterio y corre ag_portafolio.

    Devuelve (mejor, historial), igual que ag_portafolio.
    """
    random.seed(semilla)
    poblacion_inicial = crear_poblacion(tamano_poblacion, criterio, candidatos, presupuesto, espacio, erosion)
    return ag_portafolio(criterio, poblacion_inicial, generaciones, probabilidad_mutacion, elitismo,
                         candidatos, presupuesto, espacio, erosion, k)


# =============================================================================
# 7. ROBUSTEZ — 20 semillas distintas
#    Un solo resultado no demuestra que el AG sea confiable. Se repite con
#    20 semillas distintas y se cuenta cuántas veces llega al óptimo.
# =============================================================================
def analisis_robustez(semillas=range(20), tamano_poblacion=TAMANO_POBLACION, params_ag=PARAMS_AG,
                      candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL,
                      erosion=None, k=None):
    """Devuelve {criterio: aciertos} para "esperada" y "peor_caso"."""
    valor_esperada = lambda ind: utilidad_total(ind, candidatos)
    valor_peor_caso = lambda ind: utilidad_peor_caso(ind, erosion, k, candidatos)
    opt_esp, _, _ = fuerza_bruta(valor_esperada, candidatos, presupuesto, espacio)
    opt_mm, _, _ = fuerza_bruta(valor_peor_caso, candidatos, presupuesto, espacio)

    resultado = {}
    for criterio, objetivo, valor in [("esperada", opt_esp, valor_esperada), ("peor_caso", opt_mm, valor_peor_caso)]:
        aciertos = 0
        for semilla in semillas:
            random.seed(semilla)
            mejor, _ = ag_portafolio(criterio, crear_poblacion(tamano_poblacion, criterio, candidatos, presupuesto, espacio, erosion),
                                     **params_ag, candidatos=candidatos, presupuesto=presupuesto, espacio=espacio,
                                     erosion=erosion, k=k)
            aciertos += abs(valor(mejor) - objetivo) < 1e-6
        resultado[criterio] = aciertos
    return resultado


# =============================================================================
# 8. SENSIBILIDAD — factor de erosión y número de ataques
#    La erosión es un supuesto, así que se multiplica por un factor (0.5 =
#    rivales mucho más débiles, 1.5 = más fuertes) y se mira si el portafolio
#    óptimo cambia. También se prueba un rival que puede atacar 2 productos.
# =============================================================================
def analisis_sensibilidad(ataques=(1, 2), factores=(0.5, 0.75, 1.0, 1.25, 1.5),
                          candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL,
                          erosion=None, portafolio_referencia=PORTAFOLIO_SPRINT3):
    """Devuelve la tabla de sensibilidad del notebook como lista de filas."""
    erosion = erosion or EROSION
    filas = []
    for k in ataques:
        for factor in factores:
            ero = {n: min(0.95, e * factor) for n, e in erosion.items()}
            valor = lambda ind, ero=ero, k=k: utilidad_peor_caso(ind, ero, k, candidatos)
            mejor_valor, optimos, _ = fuerza_bruta(valor, candidatos, presupuesto, espacio)
            filas.append({"Ataques del rival": k, "Factor de erosión": factor,
                          "Portafolio óptimo": " | ".join(", ".join(nombre_incluidos(c, candidatos)) for c in optimos),
                          "Peor caso": mejor_valor,
                          "Peor caso del portafolio Sprint 3": valor(portafolio_referencia)})
    return filas
