"""Sprint 2 — Sistema experto 2: ¿una nueva categoría de producto es viable?

Portado de `referencia/sprint2/MegaMarket_Sprint2_SistemaExperto.ipynb`
(segunda mitad). Misma arquitectura de tres piezas (base de conocimiento,
memoria de trabajo, motor de inferencia); para no confundir sus reglas con
las del sistema de logística se llaman C1 a C7 ("criterio").

Los 7 criterios son requisitos conjuntos: un producto es VIABLE solo si
cumple los 7 al mismo tiempo (C1 AND C2 AND ... AND C7). Es un chequeo tipo
"todas las luces en verde", no una competencia entre reglas.

Adaptaciones permitidas (SPEC §5.2): la lectura del CSV quedó en funciones
y `evaluar_producto` devuelve el resultado en vez de imprimirlo.
"""

import pandas as pd

from megamarket.datos import RUTA_MEMORIA_PORTAFOLIO
from megamarket.sistema_experto_logistica import a_booleano

# =============================================================================
# 10. BASE DE CONOCIMIENTO — Decisión de portafolio
# =============================================================================
BASE_CONOCIMIENTO_PORTAFOLIO = {
    "contexto": {
        "canal_objetivo": "Cadenas de supermercado (mismo canal que opera MegaMarket)",
        "categoria_actual": "Consumo masivo - alimentos y bebidas",
    },
    "umbrales": {
        "vida_util_minima_meses": 6,   # Criterio 6 del gerente general
        "margen_minimo_pct": 12,       # supuesto de política interna (ajustar con dato real)
    },
}

# Los 7 criterios del gerente general de MegaMarket SAS, formalizados como reglas:
#
#   C1 - SI el producto es afín al portafolio actual (consumo masivo) Y se
#        vende por el mismo canal/segmento (cadenas de supermercado)
#        ENTONCES cumple afinidad de portafolio y canal.
#   C2 - SI el producto tiene registro sanitario vigente Y ficha técnica de
#        respaldo ENTONCES cumple el criterio legal.
#   C3 - SI el producto es fácil de transportar/almacenar/manipular Y NO
#        representa riesgo de contaminación cruzada con los alimentos que ya
#        maneja MegaMarket ENTONCES cumple viabilidad operativa.
#   C4 - SI el producto tiene alta calidad Y presentación estéticamente
#        atractiva ENTONCES cumple el criterio de calidad/presentación.
#   C5 - SI el producto permite venta cruzada con el portafolio actual
#        ENTONCES cumple complementariedad.
#   C6 - SI la vida útil del producto es >= 6 meses ENTONCES cumple vida útil.
#   C7 - SI el producto tiene precio asequible Y un margen de rentabilidad
#        >= al mínimo esperado ENTONCES cumple precio/rentabilidad.
#
# Un producto es VIABLE solo si cumple los 7 al mismo tiempo (C1 AND C2 AND
# ... AND C7). Si falla uno solo, no entra al portafolio.

CRITERIOS_NOMBRES = {
    "C1": "Afinidad de portafolio y canal/segmento",
    "C2": "Cumplimiento legal (registro sanitario y ficha técnica)",
    "C3": "Viabilidad operativa (transporte, almacenamiento, manipulación)",
    "C4": "Estándares de calidad y presentación",
    "C5": "Complementariedad / venta cruzada",
    "C6": "Vida útil (mínimo 6 meses)",
    "C7": "Precio asequible y rentabilidad",
}

# Descripción completa de cada criterio (SI...ENTONCES), para mostrar como
# el detalle de cada fila cuando el motor de inferencia evalúa un producto.
CRITERIOS_DETALLE = {
    "C1": "El producto es afín al portafolio actual (consumo masivo) y se vende por el mismo canal y segmento: cadenas de supermercado.",
    "C2": "El producto cuenta con registro sanitario vigente y ficha técnica de respaldo.",
    "C3": "Es fácil de transportar, almacenar y manipular, y no representa riesgo de contaminación cruzada con los alimentos que ya maneja MegaMarket.",
    "C4": "Cumple altos estándares de calidad y tiene una presentación estéticamente atractiva.",
    "C5": "Complementa el portafolio actual y permite hacer venta cruzada.",
    "C6": f"Tiene una vida útil de {BASE_CONOCIMIENTO_PORTAFOLIO['umbrales']['vida_util_minima_meses']} meses o más.",
    "C7": f"Tiene un precio asequible y un margen de rentabilidad de al menos {BASE_CONOCIMIENTO_PORTAFOLIO['umbrales']['margen_minimo_pct']}%.",
}


# =============================================================================
# 11. MEMORIA DE TRABAJO — las referencias candidatas (leídas desde CSV)
# =============================================================================
def leer_memoria_portafolio(fuente=RUTA_MEMORIA_PORTAFOLIO):
    """Lee el CSV de la memoria de trabajo de portafolio (o copia un DataFrame ya cargado)."""
    if isinstance(fuente, pd.DataFrame):
        return fuente.copy()
    # Misma lectura robusta que en el sistema de logística: detecta si el CSV
    # viene separado por "," o por ";" (Excel en español exporta con ";") y
    # quita el BOM que Excel agrega al guardar como "CSV UTF-8".
    return pd.read_csv(fuente, sep=None, engine="python", encoding="utf-8-sig")


def construir_memoria_trabajo_portafolio(memoria_portafolio_df):
    """Convierte el DataFrame en {producto: {"C1": bool, ..., "C7": bool}}.

    Reutilizamos a_booleano(), la misma función que ya se definió para el
    sistema de logística: convierte 'Sí' / 'No' del CSV a True / False.
    """
    MEMORIA_TRABAJO_PORTAFOLIO = {}
    for _, fila in memoria_portafolio_df.iterrows():
        MEMORIA_TRABAJO_PORTAFOLIO[fila["producto"]] = {
            criterio: a_booleano(fila[criterio]) for criterio in CRITERIOS_NOMBRES
        }
    return MEMORIA_TRABAJO_PORTAFOLIO


# =============================================================================
# 12. MOTOR DE INFERENCIA — Decisión de portafolio
# =============================================================================
def motor_inferencia_portafolio(hechos, criterios_nombres, criterios_detalle):
    """Verifica, para UN producto candidato, si cumple cada uno de los 7
    criterios del gerente general, y arma el veredicto final: viable
    solo si los 7 se cumplen a la vez.

    Devuelve {"viable": bool, "incumplidos": [criterio], "evaluacion": {criterio: {"cumple", "detalle"}}}.
    """
    evaluacion = {
        c: {"cumple": hechos[c], "detalle": criterios_detalle[c]}
        for c in criterios_nombres
    }
    incumplidos = [c for c, v in evaluacion.items() if not v["cumple"]]
    viable = len(incumplidos) == 0
    return {"viable": viable, "incumplidos": incumplidos, "evaluacion": evaluacion}


def evaluar_producto(nombre_producto, memoria_trabajo, criterios_nombres, criterios_detalle):
    """Corre el motor de inferencia sobre UN producto candidato y devuelve
    la casuística completa: criterio por criterio, y el veredicto final.

    Responde: ¿esta categoría o producto es viable para MegaMarket?
    """
    hechos = memoria_trabajo[nombre_producto]
    resultado = motor_inferencia_portafolio(hechos, criterios_nombres, criterios_detalle)
    return resultado
