"""Página 3 — Viabilidad de productos (Sprint 2 · sistema experto de portafolio). Se construye en la Fase 3."""

from megamarket_app import componentes

componentes.encabezado_pagina(
    "¿La nueva categoría cumple los criterios del gerente?",
    "Sprint 2 · Sistema experto",
    "Antes de distribuir una categoría nueva, MegaMarket revisa siete criterios (C1–C7). "
    "Es un chequeo de «todas las luces en verde»: basta con que falle uno para descartarla.",
)
componentes.proximamente("Esta página se construye en la Fase 3. La versión difusa llega con el Sprint 4.")
componentes.ver_codigo([])
componentes.supuestos_y_limites([
    "Quien llena la memoria de trabajo marca Sí/No por criterio; el umbral de margen (12 %) es un supuesto de política interna.",
])
