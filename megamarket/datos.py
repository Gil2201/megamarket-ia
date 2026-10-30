"""Datos del caso MegaMarket, copiados literalmente de los notebooks de `referencia/`.

- COORDENADAS y listas de clientes: Sprint 1 (MegaMarket_Sprint1_AEstrella.ipynb).
- CANDIDATOS y restricciones: Sprint 3A (MegaMarket_Sprint3A_AG_Portafolio.ipynb).
- EROSION y K_ATAQUES: Sprint 3B (MegaMarket_Sprint3B_AG_Minimax_Competidor.ipynb).
- Rutas a las memorias de trabajo (CSV) del Sprint 2.

Las cifras de negocio (costos, utilidades, erosión) son ILUSTRATIVAS.
"""

from pathlib import Path

# =============================================================================
# 1. COORDENADAS (lat, lon) de cada punto real de la operación
# =============================================================================
COORDENADAS = {
    "Bodega Olaya Herrera": (6.2197, -75.5905),

    # --- Accesos viales a cada zona ---
    "Acceso Poblado (Aguacatala)": (6.1935, -75.5790),
    "Acceso Sur (Itagüí Centro)": (6.1720, -75.6120),

    # --- Ruta Poblado: 8 clientes ---
    "Fruver del Río": (6.2218, -75.5745),
    "Fruver Visitación": (6.2013, -75.5598),
    "Five Sisters": (6.2077, -75.5658),
    "Supermercado Merka 10": (6.2093, -75.5688),
    "Hotel Four Points": (6.2029, -75.5722),
    "Mercados Verona": (6.2046, -75.5605),
    "EAFIT La Bodeguita": (6.2006, -75.5783),
    "Redetrans": (6.2112, -75.5628),

    # --- Ruta Valle de Aburrá (Sur): 4 clientes ---
    "CEDI Vaquita Itagüí": (6.1735, -75.6152),
    "CEDI Euro La Estrella": (6.1448, -75.6198),
    "CEDI Merkepaisa": (6.1618, -75.6062),
    "CEDI Supermú": (6.1548, -75.6122),

    # --- Destino final compartido por las dos rutas ---
    # Cra. 51C #12B Sur-76, San Fernando, Guayabal, Medellín.
    # OJO: esta coordenada es una ESTIMACIÓN a partir de la nomenclatura vial
    # (mismo método y mismo margen de error, +/- 200-400 m, que se usó para
    # el resto de puntos del proyecto original). Si tienes la ubicación
    # exacta (por ejemplo, del pin en Google Maps), reemplázala aquí.
    "Plataforma Logística": (6.1976, -75.5807),
}

BODEGA = "Bodega Olaya Herrera"
PLATAFORMA = "Plataforma Logística"

# Universo TOTAL de clientes de cada ruta (el catálogo completo). En el
# Sprint 2 el sistema experto decide, cada semana, cuál subconjunto de este
# universo realmente sale a reparto.
clientes_poblado = [
    "Fruver del Río", "Fruver Visitación", "Five Sisters",
    "Supermercado Merka 10", "Hotel Four Points", "Mercados Verona",
    "EAFIT La Bodeguita", "Redetrans",
]

clientes_valle_aburra = [
    "CEDI Vaquita Itagüí", "CEDI Euro La Estrella",
    "CEDI Merkepaisa", "CEDI Supermú",
]

# =============================================================================
# 2. MEMORIAS DE TRABAJO DEL SPRINT 2 (CSV)
# =============================================================================
CARPETA_DATOS = Path(__file__).resolve().parent.parent / "data"
RUTA_MEMORIA_LOGISTICA = CARPETA_DATOS / "memoria_trabajo_logistica.csv"
RUTA_MEMORIA_PORTAFOLIO = CARPETA_DATOS / "memoria_trabajo_portafolio.csv"

# =============================================================================
# 3. CANDIDATOS — ya viables según el Sprint 2, con sus datos de negocio
# =============================================================================
CANDIDATOS = {
    "Higo Deshidratado Riovalle":     {"costo_lanzamiento": 18_000_000, "espacio_bodega": 6,  "utilidad_esperada_anual": 32_000_000},
    "Mix de Frutos Secos Riovalle":   {"costo_lanzamiento": 25_000_000, "espacio_bodega": 8,  "utilidad_esperada_anual": 48_000_000},
    "Barra Energética Riovalle":      {"costo_lanzamiento": 15_000_000, "espacio_bodega": 4,  "utilidad_esperada_anual": 22_000_000},
    "Granola Riovalle":               {"costo_lanzamiento": 20_000_000, "espacio_bodega": 7,  "utilidad_esperada_anual": 30_000_000},
    "Jugo Natural Riovalle":          {"costo_lanzamiento": 30_000_000, "espacio_bodega": 10, "utilidad_esperada_anual": 52_000_000},
    "Snack de Plátano Riovalle":      {"costo_lanzamiento": 12_000_000, "espacio_bodega": 5,  "utilidad_esperada_anual": 17_000_000},
    "Compota Riovalle":               {"costo_lanzamiento": 10_000_000, "espacio_bodega": 3,  "utilidad_esperada_anual": 14_000_000},
    "Café Molido Riovalle":           {"costo_lanzamiento": 22_000_000, "espacio_bodega": 6,  "utilidad_esperada_anual": 38_000_000},
}

# El orden de esta lista define la posición de cada gen en el cromosoma.
NOMBRES = list(CANDIDATOS.keys())
N_GENES = len(NOMBRES)

# =============================================================================
# 4. RESTRICCIONES DE LA DECISIÓN
# =============================================================================
PRESUPUESTO_TOTAL = 70_000_000        # COP disponibles para lanzamientos este semestre
ESPACIO_BODEGA_TOTAL = 25             # posiciones de bodega disponibles para SKU nuevas

SEMILLA = 42

# =============================================================================
# 5. EROSIÓN (Sprint 3B)
# =============================================================================
# SUPUESTO ILUSTRATIVO: fracción de la utilidad que se pierde si el rival entra en ese producto
EROSION = {
    "Higo Deshidratado Riovalle":   0.30,
    "Mix de Frutos Secos Riovalle": 0.50,
    "Barra Energética Riovalle":    0.40,
    "Granola Riovalle":             0.40,
    "Jugo Natural Riovalle":        0.60,
    "Snack de Plátano Riovalle":    0.30,
    "Compota Riovalle":             0.20,
    "Café Molido Riovalle":         0.50,
}

# SUPUESTO ILUSTRATIVO: cuántos productos puede atacar el rival a la vez (recursos limitados)
K_ATAQUES = 1
