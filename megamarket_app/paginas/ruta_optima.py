"""Página 2 — Ruta óptima (Sprint 1 · búsqueda A*). Se construye en la Fase 2."""

from megamarket_app import componentes

componentes.encabezado_pagina(
    "¿En qué orden visitamos a los clientes y cuántos km recorremos?",
    "Sprint 1 · Búsqueda A*",
    "El camión sale de la Bodega Olaya Herrera, visita a cada cliente y termina en la "
    "Plataforma Logística. A* encuentra el camino más corto de cada tramo y el vecino "
    "más cercano decide a quién se visita después.",
)
componentes.proximamente("Esta página se construye en la Fase 2.")
componentes.ver_codigo([])
componentes.supuestos_y_limites([
    "La coordenada de la Plataforma Logística es una estimación por nomenclatura vial (±200–400 m).",
    "El vecino más cercano no garantiza el orden más corto de todos los posibles.",
    "Los grafos son los de los notebooks; no son calles reales.",
])
