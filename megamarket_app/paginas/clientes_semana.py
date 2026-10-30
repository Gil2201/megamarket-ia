"""Página 1 — Clientes de la semana (Sprint 2 · sistema experto de logística). Se construye en la Fase 2."""

from megamarket_app import componentes

componentes.encabezado_pagina(
    "¿A quién visitamos esta semana y con qué prioridad?",
    "Sprint 2 · Sistema experto",
    "No todos los clientes necesitan mercancía cada semana. Un sistema experto con "
    "reglas de inclusión (R1–R3), vetos (R4–R5) y una regla por defecto (R6) decide "
    "quién entra en la ruta, con qué prioridad y por qué.",
)
componentes.proximamente("Esta página se construye en la Fase 2.")
componentes.ver_codigo([])
componentes.supuestos_y_limites([
    "Los datos de la memoria de trabajo (visitas, quejas, facturas, fletes) son ilustrativos.",
    "La política H1 (entrega en 48–72 h) se documenta, pero no se verifica: el recorrido no modela tiempos.",
])
