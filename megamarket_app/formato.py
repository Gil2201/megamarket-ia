"""Formato de números para la interfaz (SPEC §4.4).

Convención colombiana: punto para miles y coma para decimales.
  cop(122_000_000)          -> "$122.000.000"
  cop_millones(122_000_000) -> "$122,0 M"
  km(16.8)                  -> "16,8 km"
  pct(0.059)                -> "5,9 %"
"""


def _numero(valor, decimales):
    """Formatea con separador de miles '.' y decimal ','."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def cop(valor):
    """Pesos colombianos completos, sin decimales: $122.000.000."""
    signo = "−" if valor < 0 else ""
    return f"{signo}${_numero(abs(valor), 0)}"


def cop_millones(valor, decimales=1):
    """Pesos en millones: $122,0 M."""
    signo = "−" if valor < 0 else ""
    return f"{signo}${_numero(abs(valor) / 1_000_000, decimales)} M"


def km(valor, decimales=1):
    """Distancia en kilómetros con 1 decimal: 16,8 km."""
    return f"{_numero(valor, decimales)} km"


def pct(fraccion, decimales=1):
    """Porcentaje a partir de una fracción (0.059 -> 5,9 %)."""
    return f"{_numero(fraccion * 100, decimales)} %"
