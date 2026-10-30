"""Sprint 4 — Lógica difusa: nota de viabilidad (4A) y desempate de portafolios (4B).

Sigue el notebook de clase `referencia/clase/09_Logica_Difusa_Mercado_Libre.ipynb`:
Mamdani hecho a mano con numpy. `trimf`, `trapmf`, `pertenencia_en` y `centroide`
se copian LITERALMENTE. `inferencia_mamdani` se generaliza para recibir los
conjuntos y las reglas como parámetros (en clase tenía reputación/urgencia
fijos), sin cambiar sus cuatro pasos:

1. Fuzzificación: grados de pertenencia de las dos entradas.
2. Evaluación de reglas: Y = mínimo; cada regla recorta su salida.
3. Agregación: máximo de las salidas recortadas.
4. Defuzzificación: centroide.

Cada sistema tiene 2 entradas y 9 reglas (tabla 3x3 completa), como en clase.
Para usar 6 criterios se encadenan 5 sistemas (jerarquía): la salida 0–100 de
uno es la entrada del siguiente. Decisiones de diseño: docs/SPRINT4_DECISIONES.md.

> Los puntos de corte, las reglas y los datos son una propuesta ilustrativa que
> debe validarse; no describen una política real de MegaMarket.
"""

import numpy as np
import pandas as pd

from megamarket.datos import CARPETA_DATOS

RUTA_MEMORIA_DIFUSA = CARPETA_DATOS / "memoria_trabajo_portafolio_difusa.csv"


# =============================================================================
# 2. FUNCIONES DE PERTENENCIA (literales del notebook de clase)
# =============================================================================
def trimf(x, a, b, c):
    """Función triangular con parámetros ordenados a <= b <= c."""
    if not (a <= b <= c):
        raise ValueError("La función triangular requiere a <= b <= c.")
    x = np.asarray(x, dtype=float)
    izq = (x - a) / (b - a) if b != a else np.where(x >= a, 1.0, 0.0)
    der = (c - x) / (c - b) if c != b else np.where(x <= c, 1.0, 0.0)
    return np.clip(np.minimum(izq, der), 0.0, 1.0)


def trapmf(x, a, b, c, d):
    """Función trapezoidal con parámetros ordenados a <= b <= c <= d."""
    if not (a <= b <= c <= d):
        raise ValueError("La función trapezoidal requiere a <= b <= c <= d.")
    x = np.asarray(x, dtype=float)
    subida = (x - a) / (b - a) if b != a else np.where(x >= a, 1.0, 0.0)
    bajada = (d - x) / (d - c) if d != c else np.where(x <= d, 1.0, 0.0)
    return np.clip(np.minimum(np.minimum(subida, 1.0), bajada), 0.0, 1.0)


# =============================================================================
# 4. INFERENCIA MAMDANI (literales del notebook de clase + versión general)
# =============================================================================
def pertenencia_en(valor, universo, curva):
    """Interpola una pertenencia y rechaza valores fuera del universo modelado."""
    valor = float(valor)
    if not np.isfinite(valor):
        raise ValueError("La entrada debe ser un número finito.")
    if valor < universo[0] or valor > universo[-1]:
        raise ValueError(f"La entrada {valor} está fuera del rango [{universo[0]}, {universo[-1]}].")
    return float(np.interp(valor, universo, curva))


def centroide(universo, curva):
    """Defuzzificación por centroide (centro de gravedad) de la salida agregada."""
    universo = np.asarray(universo, dtype=float)
    curva = np.asarray(curva, dtype=float)
    if universo.shape != curva.shape:
        raise ValueError("El universo y la curva deben tener la misma forma.")
    if not np.all(np.isfinite(curva)):
        raise ValueError("La curva agregada contiene valores no finitos.")
    integrar = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    area = integrar(curva, universo)
    if np.isclose(area, 0.0):
        raise ValueError("No hay área en la salida agregada; no se puede calcular el centroide.")
    return float(integrar(universo * curva, universo) / area)


def inferencia_mamdani(x1, x2, universo_1, conjuntos_1, universo_2, conjuntos_2,
                       universo_salida, conjuntos_salida, reglas, devolver_detalle=False):
    """Versión general de la inferencia_mamdani de clase: los conjuntos y las
    reglas llegan como parámetros. Los cuatro pasos son los mismos.

    reglas: lista de tuplas (etiqueta_1, etiqueta_2, salida).
    Devuelve el centroide, o (resultado, grados_1, grados_2, agregado, detalle)
    si devolver_detalle=True. Rechaza entradas fuera de su universo con ValueError.
    """
    x1, x2 = float(x1), float(x2)

    # 1. Fuzzificación
    grados_1 = {k: pertenencia_en(x1, universo_1, v) for k, v in conjuntos_1.items()}
    grados_2 = {k: pertenencia_en(x2, universo_2, v) for k, v in conjuntos_2.items()}
    agregado = np.zeros_like(universo_salida)
    detalle = []

    for etq_1, etq_2, salida in reglas:
        # AND (mínimo), implicación Mamdani (recorte) y agregación (máximo).
        activacion = min(grados_1[etq_1], grados_2[etq_2])
        recorte = np.minimum(activacion, conjuntos_salida[salida])
        agregado = np.maximum(agregado, recorte)
        detalle.append({
            "entrada_1": etq_1,
            "entrada_2": etq_2,
            "salida": salida,
            "activación": activacion,
        })

    # 4. Defuzzificación
    resultado = centroide(universo_salida, agregado)
    if devolver_detalle:
        return resultado, grados_1, grados_2, agregado, detalle
    return resultado


# =============================================================================
# VARIABLES LINGÜÍSTICAS Y SISTEMAS
#    Una variable = {"nombre", "universo", "conjuntos"}.
#    Un sistema = {"nombre", "entrada_1", "entrada_2", "salida", "reglas"}.
# =============================================================================
def variable(nombre, universo, conjuntos):
    return {"nombre": nombre, "universo": universo, "conjuntos": conjuntos}


def evaluar_sistema(sistema, x1, x2):
    """Corre un sistema de 2 entradas y 9 reglas.

    Devuelve {"valor", "grados_1", "grados_2", "agregado", "detalle"}.
    """
    e1, e2, s = sistema["entrada_1"], sistema["entrada_2"], sistema["salida"]
    resultado, grados_1, grados_2, agregado, detalle = inferencia_mamdani(
        x1, x2, e1["universo"], e1["conjuntos"], e2["universo"], e2["conjuntos"],
        s["universo"], s["conjuntos"], sistema["reglas"], devolver_detalle=True,
    )
    return {"valor": resultado, "grados_1": grados_1, "grados_2": grados_2,
            "agregado": agregado, "detalle": detalle}


# Universos numéricos
universo_0_100 = np.linspace(0, 100, 1001)
universo_0_10 = np.linspace(0, 10, 1001)
margen_u = np.linspace(0, 40, 1001)
vida_util_u = np.linspace(0, 24, 1001)


def conjuntos_0_100():
    """Los conjuntos de salida de clase (prioridad), usados para toda salida 0–100."""
    return {
        "baja": trapmf(universo_0_100, 0, 0, 20, 40),
        "media": trimf(universo_0_100, 25, 50, 75),
        "alta": trapmf(universo_0_100, 60, 80, 100, 100),
    }


def conjuntos_0_10():
    """Los conjuntos de la urgencia de clase, usados para los criterios 0–10."""
    return {
        "baja": trapmf(universo_0_10, 0, 0, 2, 4),
        "media": trimf(universo_0_10, 2, 5, 8),
        "alta": trapmf(universo_0_10, 6, 8, 10, 10),
    }


def particion_0_10():
    """Criterios 0–10 del Sprint 4. Es una PARTICIÓN: las pertenencias vecinas
    suman 1 (cruces en 3,5 y 6,5). Con cortes que no suman 1 (como la urgencia
    de clase) la nota podía bajar hasta 4 puntos al SUBIR un criterio."""
    return {
        "baja": trapmf(universo_0_10, 0, 0, 2, 5),
        "media": trimf(universo_0_10, 2, 5, 8),
        "alta": trapmf(universo_0_10, 5, 8, 10, 10),
    }


def particion_0_100():
    """Salidas intermedias y finales 0–100 del Sprint 4 (partición; cruces en 37,5 y 62,5)."""
    return {
        "baja": trapmf(universo_0_100, 0, 0, 25, 50),
        "media": trimf(universo_0_100, 25, 50, 75),
        "alta": trapmf(universo_0_100, 50, 75, 100, 100),
    }


# --- El ejemplo de clase (Mercado Libre), para la prueba de paridad ---
SISTEMA_CLASE = {
    "nombre": "Prioridad de despacho (clase)",
    "entrada_1": variable("Reputación", universo_0_100, {
        "baja": trapmf(universo_0_100, 0, 0, 30, 50),
        "media": trimf(universo_0_100, 30, 50, 70),
        "alta": trapmf(universo_0_100, 50, 70, 100, 100),
    }),
    "entrada_2": variable("Urgencia", universo_0_10, conjuntos_0_10()),
    "salida": variable("Prioridad", universo_0_100, conjuntos_0_100()),
    "reglas": [
        ("baja",  "baja",  "baja"),
        ("baja",  "media", "baja"),
        ("baja",  "alta",  "media"),
        ("media", "baja",  "baja"),
        ("media", "media", "media"),
        ("media", "alta",  "alta"),
        ("alta",  "baja",  "media"),
        ("alta",  "media", "alta"),
        ("alta",  "alta",  "alta"),
    ],
}


# =============================================================================
# 4A — NOTA DE VIABILIDAD: jerarquía de 5 sistemas (opción A)
# =============================================================================
# --- Entradas (criterios del gerente, ahora numéricos) ---
# Los umbrales clásicos del Sprint 2 (margen 12 %, vida útil 6 meses) quedan
# JUSTO en el cruce: ahí la pertenencia es 0,5 a cada etiqueta vecina, el punto
# de máxima ambigüedad. Ya no son fronteras duras.
MARGEN = variable("Margen (%)", margen_u, {
    "bajo": trapmf(margen_u, 0, 0, 6, 18),
    "medio": trimf(margen_u, 6, 18, 30),
    "alto": trapmf(margen_u, 18, 30, 40, 40),
})
VIDA_UTIL = variable("Vida útil (meses)", vida_util_u, {
    "corta": trapmf(vida_util_u, 0, 0, 3, 9),
    "media": trimf(vida_util_u, 3, 9, 15),
    "larga": trapmf(vida_util_u, 9, 15, 24, 24),
})
COMPLEMENTARIEDAD = variable("Complementariedad (0–10)", universo_0_10, particion_0_10())
FACILIDAD_OPERATIVA = variable("Facilidad operativa (0–10)", universo_0_10, particion_0_10())
AFINIDAD = variable("Afinidad con el portafolio (0–10)", universo_0_10, particion_0_10())
CALIDAD = variable("Calidad y presentación (0–10)", universo_0_10, particion_0_10())

# --- Salidas intermedias y final (0–100) ---
ATRACTIVO = variable("Atractivo comercial", universo_0_100, particion_0_100())
SOLIDEZ = variable("Solidez operativa", universo_0_100, particion_0_100())
ENCAJE = variable("Encaje con la marca", universo_0_100, particion_0_100())
FORTALEZA = variable("Fortaleza del negocio", universo_0_100, particion_0_100())
NOTA = variable("Nota de viabilidad", universo_0_100, particion_0_100())

SISTEMAS_VIABILIDAD = {
    # S1: el margen domina. Un margen bajo arrastra a "baja" aunque la
    # complementariedad sea alta, pero no al revés.
    "S1": {"nombre": "Atractivo comercial", "entrada_1": MARGEN, "entrada_2": COMPLEMENTARIEDAD,
           "salida": ATRACTIVO, "reglas": [
               ("bajo",  "baja",  "baja"),
               ("bajo",  "media", "baja"),
               ("bajo",  "alta",  "baja"),
               ("medio", "baja",  "baja"),
               ("medio", "media", "media"),
               ("medio", "alta",  "alta"),
               ("alto",  "baja",  "media"),
               ("alto",  "media", "alta"),
               ("alto",  "alta",  "alta"),
           ]},
    # S2: la vida útil domina (un producto que se vence rápido no es sólido).
    "S2": {"nombre": "Solidez operativa", "entrada_1": VIDA_UTIL, "entrada_2": FACILIDAD_OPERATIVA,
           "salida": SOLIDEZ, "reglas": [
               ("corta", "baja",  "baja"),
               ("corta", "media", "baja"),
               ("corta", "alta",  "baja"),
               ("media", "baja",  "baja"),
               ("media", "media", "media"),
               ("media", "alta",  "alta"),
               ("larga", "baja",  "media"),
               ("larga", "media", "alta"),
               ("larga", "alta",  "alta"),
           ]},
    # S3: la afinidad domina. Un producto ajeno al portafolio no encaja con
    # la marca por buena que sea su presentación.
    "S3": {"nombre": "Encaje con la marca", "entrada_1": AFINIDAD, "entrada_2": CALIDAD,
           "salida": ENCAJE, "reglas": [
               ("baja",  "baja",  "baja"),
               ("baja",  "media", "baja"),
               ("baja",  "alta",  "baja"),
               ("media", "baja",  "baja"),
               ("media", "media", "media"),
               ("media", "alta",  "alta"),
               ("alta",  "baja",  "media"),
               ("alta",  "media", "alta"),
               ("alta",  "alta",  "alta"),
           ]},
    # S4: eslabón más débil. El negocio no es fuerte si falla lo comercial
    # O lo operativo: basta un "baja" para que la fortaleza sea baja.
    "S4": {"nombre": "Fortaleza del negocio", "entrada_1": ATRACTIVO, "entrada_2": SOLIDEZ,
           "salida": FORTALEZA, "reglas": [
               ("baja",  "baja",  "baja"),
               ("baja",  "media", "baja"),
               ("baja",  "alta",  "baja"),
               ("media", "baja",  "baja"),
               ("media", "media", "media"),
               ("media", "alta",  "media"),
               ("alta",  "baja",  "baja"),
               ("alta",  "media", "media"),
               ("alta",  "alta",  "alta"),
           ]},
    # S5: la fortaleza manda. Si es baja, la nota es baja para cualquier
    # encaje; el encaje con la marca solo sube o baja un nivel.
    "S5": {"nombre": "Nota de viabilidad", "entrada_1": FORTALEZA, "entrada_2": ENCAJE,
           "salida": NOTA, "reglas": [
               ("baja",  "baja",  "baja"),
               ("baja",  "media", "baja"),
               ("baja",  "alta",  "baja"),
               ("media", "baja",  "baja"),
               ("media", "media", "media"),
               ("media", "alta",  "alta"),
               ("alta",  "baja",  "media"),
               ("alta",  "media", "alta"),
               ("alta",  "alta",  "alta"),
           ]},
}

CRITERIOS_DIFUSOS = ["margen_pct", "complementariedad", "vida_util_meses",
                     "facilidad_operativa", "afinidad", "calidad_presentacion"]


def etiqueta_dominante(valor, var=NOTA):
    """Etiqueta con mayor pertenencia para un valor (p. ej. nota 72 -> "alta")."""
    grados = {k: pertenencia_en(valor, var["universo"], v) for k, v in var["conjuntos"].items()}
    return max(grados, key=grados.get)


def nota_viabilidad(producto):
    """Nota de viabilidad 0–100 de un producto con la jerarquía de 5 sistemas.

    Responde: ¿qué tan viable es este producto, sabiendo que no todos los
    criterios pesan igual? `producto` es un dict con "C2" (bool) y los 6
    criterios numéricos de CRITERIOS_DIFUSOS.
    Paso 0 (lógica clásica): si C2 es falso, no hay registro sanitario y el
    producto es "No viable" sin pasar por el sistema difuso.
    Devuelve {"cumple_C2", "nota", "etiqueta", "nodos": {S1..S5: resultado de evaluar_sistema}}.
    """
    if not producto["C2"]:
        return {"cumple_C2": False, "nota": None, "etiqueta": "no viable", "nodos": {}}

    s = SISTEMAS_VIABILIDAD
    nodos = {}
    nodos["S1"] = evaluar_sistema(s["S1"], producto["margen_pct"], producto["complementariedad"])
    nodos["S2"] = evaluar_sistema(s["S2"], producto["vida_util_meses"], producto["facilidad_operativa"])
    nodos["S3"] = evaluar_sistema(s["S3"], producto["afinidad"], producto["calidad_presentacion"])
    nodos["S4"] = evaluar_sistema(s["S4"], nodos["S1"]["valor"], nodos["S2"]["valor"])
    nodos["S5"] = evaluar_sistema(s["S5"], nodos["S4"]["valor"], nodos["S3"]["valor"])

    nota = nodos["S5"]["valor"]
    return {"cumple_C2": True, "nota": nota, "etiqueta": etiqueta_dominante(nota), "nodos": nodos}


def leer_memoria_difusa(fuente=RUTA_MEMORIA_DIFUSA):
    """Lee el CSV de datos numéricos (o copia un DataFrame ya cargado)."""
    if isinstance(fuente, pd.DataFrame):
        return fuente.copy()
    return pd.read_csv(fuente, sep=None, engine="python", encoding="utf-8-sig")


def construir_productos_difusos(memoria_df):
    """DataFrame -> {producto: {"tipo", "C2", criterios numéricos}}."""
    productos = {}
    for _, fila in memoria_df.iterrows():
        productos[fila["producto"]] = {
            "tipo": fila["tipo"],
            "C2": str(fila["C2"]).strip().lower() == "sí",
            **{c: float(fila[c]) for c in CRITERIOS_DIFUSOS},
        }
    return productos


def notas_de_productos(productos):
    """{producto: nota} para todos los productos (None si no cumple C2)."""
    return {nombre: nota_viabilidad(datos)["nota"] for nombre, datos in productos.items()}


# =============================================================================
# 4B — DESEMPATE DIFUSO DE PORTAFOLIOS
# =============================================================================
NOTA_PROMEDIO = variable("Nota promedio del portafolio", universo_0_100, particion_0_100())
# Calibrada al rango real de la erosión (20 %–60 %): con 0–100 genérico todos
# los portafolios quedarían en "media".
EXPOSICION = variable("Exposición al competidor (%)", universo_0_100, {
    "baja": trapmf(universo_0_100, 0, 0, 30, 45),
    "media": trimf(universo_0_100, 30, 45, 60),
    "alta": trapmf(universo_0_100, 45, 60, 100, 100),
})
PREFERENCIA = variable("Preferencia", universo_0_100, particion_0_100())

# Se prefiere el portafolio con nota alta y exposición al competidor baja.
SISTEMA_DESEMPATE = {
    "nombre": "Preferencia entre portafolios", "entrada_1": NOTA_PROMEDIO, "entrada_2": EXPOSICION,
    "salida": PREFERENCIA, "reglas": [
        ("baja",  "baja",  "media"),
        ("baja",  "media", "baja"),
        ("baja",  "alta",  "baja"),
        ("media", "baja",  "alta"),
        ("media", "media", "media"),
        ("media", "alta",  "baja"),
        ("alta",  "baja",  "alta"),
        ("alta",  "media", "alta"),
        ("alta",  "alta",  "media"),
    ],
}

# Puntos de preferencia por debajo de los cuales se considera empate. Mamdani
# con recorte por mínimo y centroide tiene un "ruido" propio de hasta ~1,3
# puntos (ver docs/SPRINT4_DECISIONES.md §8): diferencias menores no significan nada.
DIFERENCIA_MINIMA = 1.5


def entradas_desempate(productos, candidatos, erosion, notas):
    """Las dos entradas de 4B para un portafolio (lista de nombres de producto).

    nota_promedio = Σ(nota × utilidad) / Σ utilidad
    exposicion    = Σ(utilidad × erosión) / Σ utilidad × 100
    """
    utilidades = {p: candidatos[p]["utilidad_esperada_anual"] for p in productos}
    total = sum(utilidades.values())
    nota_promedio = sum(notas[p] * utilidades[p] for p in productos) / total
    exposicion = sum(utilidades[p] * erosion[p] for p in productos) / total * 100
    return nota_promedio, exposicion


def desempatar_portafolios(portafolios, candidatos, erosion, notas, espacio_total_bodega):
    """Ordena portafolios empatados por preferencia difusa.

    Responde: entre portafolios con la misma utilidad, ¿cuál conviene más?
    `portafolios` es una lista de listas de nombres; todos sus productos deben
    tener nota (cumplir C2). Si dos quedan a menos de DIFERENCIA_MINIMA puntos,
    gana el de mayor holgura de bodega; si siguen iguales, se respeta el orden
    recibido. Devuelve la lista ordenada de
    {"productos", "nota_promedio", "exposicion", "holgura", "preferencia", "inferencia"}.
    """
    resultados = []
    for orden, productos in enumerate(portafolios):
        nota_promedio, exposicion = entradas_desempate(productos, candidatos, erosion, notas)
        inferencia = evaluar_sistema(SISTEMA_DESEMPATE, nota_promedio, exposicion)
        espacio_usado = sum(candidatos[p]["espacio_bodega"] for p in productos)
        resultados.append({
            "productos": list(productos),
            "nota_promedio": nota_promedio,
            "exposicion": exposicion,
            "holgura": espacio_total_bodega - espacio_usado,
            "preferencia": inferencia["valor"],
            "inferencia": inferencia,
            "orden": orden,
        })

    # 1) Mayor preferencia difusa.
    resultados.sort(key=lambda r: (-r["preferencia"], r["orden"]))
    # 2) Si otros quedan a menos de DIFERENCIA_MINIMA del primero, se considera
    #    empate y gana la mayor holgura de bodega (luego el orden recibido).
    mejor = resultados[0]["preferencia"]
    empatados = [r for r in resultados if mejor - r["preferencia"] < DIFERENCIA_MINIMA]
    ganador = min(empatados, key=lambda r: (-r["holgura"], -r["preferencia"], r["orden"]))
    if len(empatados) == 1:
        ganador["criterio"] = "preferencia difusa"
    elif ganador is not resultados[0] or ganador["holgura"] > min(r["holgura"] for r in empatados):
        ganador["criterio"] = "holgura de bodega (preferencias a menos de 1,5 puntos)"
    else:
        ganador["criterio"] = "orden de la fuerza bruta (misma preferencia y holgura)"
    resultados.remove(ganador)
    return [ganador] + resultados


def empates_con_tolerancia(portafolios_validos, valor, tolerancia=0.0):
    """Portafolios cuyo valor está a menos de `tolerancia` (fracción) del mejor.

    Con tolerancia 0 son los empates exactos (como la fuerza bruta del notebook 3B).
    """
    mejor = max(valor(p) for p in portafolios_validos)
    return [p for p in portafolios_validos if valor(p) >= mejor * (1 - tolerancia) - 1e-6]
