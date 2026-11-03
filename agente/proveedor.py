"""Proveedores de modelo de lenguaje compatibles con el formato de OpenAI.

Cambiar de proveedor = cambiar la URL, el modelo y la clave. El ciclo del
agente (bucle.py) no cambia.
"""

from openai import OpenAI

PROVEEDORES = {
    # Google AI Studio, plan de pago con tope de gasto (la capa gratuita da 20 solicitudes al día).
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "modelo": "gemini-3.6-flash",
        "modelo_respaldo": "gemini-3.5-flash",
        "secreto": "GEMINI_API_KEY",
    },
    # Modelo local con Ollama (gratis, solo en el computador; no corre en Streamlit Cloud).
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "modelo": "qwen3",
        "modelo_respaldo": None,
        "secreto": None,
    },
}


def crear_cliente(clave, proveedor="gemini", timeout=90):
    """Cliente del proveedor. `clave` es la API key (o cualquier texto para Ollama)."""
    config = PROVEEDORES[proveedor]
    return OpenAI(api_key=clave or "sin-clave", base_url=config["base_url"], timeout=timeout, max_retries=2)
