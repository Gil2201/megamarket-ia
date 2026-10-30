"""Página 5 — Competidor (Sprint 3B · teoría de juegos + Minimax). Se construye en la Fase 3."""

from megamarket_app import componentes

componentes.encabezado_pagina(
    "¿Qué pasa con el portafolio si un competidor reacciona?",
    "Sprint 3B · Teoría de juegos y Minimax",
    "El portafolio óptimo supone que nadie reacciona. Si un rival entra con un producto "
    "parecido, nos quita parte de la utilidad. Una matriz de pagos y un Minimax de dos "
    "niveles miden cuánto nos queda en el peor caso.",
)
componentes.proximamente("Esta página se construye en la Fase 3.")
componentes.ver_codigo([])
componentes.supuestos_y_limites([
    "La erosión y los pagos del rival son supuestos ilustrativos.",
    "Es un Minimax simplificado: un solo movimiento del rival, sin poda Alfa-Beta.",
    "El análisis usa solo el primer año.",
])
