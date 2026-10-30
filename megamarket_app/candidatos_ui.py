"""Tabla editable de candidatos (páginas 4 y 5): conversión y validación.

Aquí no hay lógica de negocio: solo se pasa del dict CANDIDATOS del
notebook a un DataFrame editable y de vuelta, y se revisan los datos antes
de entregarlos al algoritmo genético.
"""

import pandas as pd

from megamarket.datos import EROSION

MIN_CANDIDATOS = 5
# Con n candidatos la fuerza bruta revisa 2^n combinaciones: 2^16 = 65.536 sigue siendo rápido.
MAX_CANDIDATOS = 16
EROSION_POR_DEFECTO = 0.40   # supuesto para candidatos nuevos que no estaban en el notebook 3B

CAMPOS = ["costo_lanzamiento", "espacio_bodega", "utilidad_esperada_anual"]


def candidatos_a_df(candidatos):
    return pd.DataFrame([{"producto": n, **{c: d[c] for c in CAMPOS}} for n, d in candidatos.items()])


def df_a_candidatos(df):
    """DataFrame editado -> dict con el mismo formato de CANDIDATOS (orden = genes)."""
    candidatos = {}
    for _, fila in df.iterrows():
        nombre = str(fila["producto"]).strip()
        candidatos[nombre] = {c: int(fila[c]) for c in CAMPOS}
    return candidatos


def validar_candidatos(df):
    """Devuelve una lista de errores en español (vacía si todo está bien)."""
    errores = []
    df = df.dropna(how="all")
    nombres = [str(n).strip() for n in df["producto"] if pd.notna(n)]
    if len(df) < MIN_CANDIDATOS:
        errores.append(f"Se necesitan al menos {MIN_CANDIDATOS} candidatos.")
    if len(df) > MAX_CANDIDATOS:
        errores.append(f"Máximo {MAX_CANDIDATOS} candidatos: con más, la fuerza bruta (2^n combinaciones) deja de ser instantánea.")
    if len(nombres) < len(df) or any(not n for n in nombres):
        errores.append("Todos los candidatos necesitan nombre.")
    repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
    if repetidos:
        errores.append(f"Nombres repetidos: {', '.join(repetidos)}.")
    for campo, etiqueta in [("costo_lanzamiento", "costo"), ("espacio_bodega", "espacio"),
                            ("utilidad_esperada_anual", "utilidad")]:
        valores = pd.to_numeric(df[campo], errors="coerce")
        if valores.isna().any():
            errores.append(f"Falta el {etiqueta} de algún candidato.")
        elif (valores < 0).any():
            errores.append(f"El {etiqueta} no puede ser negativo.")
    costos = pd.to_numeric(df["costo_lanzamiento"], errors="coerce")
    if (costos == 0).any():
        errores.append("El costo no puede ser 0: la reparación divide la utilidad entre el costo.")
    return errores


def erosion_para(candidatos, erosion_editada):
    """Erosión de cada candidato: la editada, la del notebook o la de por defecto."""
    return {n: erosion_editada.get(n, EROSION.get(n, EROSION_POR_DEFECTO)) for n in candidatos}


def como_tupla(candidatos):
    """Forma inmutable de los candidatos (para el caché de Streamlit)."""
    return tuple((n, tuple(d[c] for c in CAMPOS)) for n, d in candidatos.items())


def desde_tupla(tupla):
    return {n: dict(zip(CAMPOS, valores)) for n, valores in tupla}
