"""Página 4 — Qué lanzar (Sprint 3A · algoritmo genético). Se construye en la Fase 3."""

from megamarket_app import componentes

componentes.encabezado_pagina(
    "¿Qué referencias lanzamos con el presupuesto y la bodega que tenemos?",
    "Sprint 3A · Algoritmo genético",
    "Hay 8 referencias Riovalle candidatas, pero el presupuesto y el espacio de bodega no "
    "alcanzan para todas. Con 2⁸ = 256 combinaciones posibles, un algoritmo genético busca "
    "la que deja más utilidad sin pasarse de los límites.",
)
componentes.proximamente("Esta página se construye en la Fase 3.")
componentes.ver_codigo([])
componentes.supuestos_y_limites([
    "Los costos, espacios y utilidades son ficticios.",
])
