"""Puente entre el CSV de la memoria de trabajo de logística y la tabla editable.

El CSV (y el motor de inferencia) usan texto: "Sí" / "No" / "No hubo visita".
La tabla editable de la página 1 usa casillas para las columnas Sí/No.
Estas funciones convierten en los dos sentidos, para que al motor siempre
le llegue el mismo formato del notebook. Aquí no hay lógica de negocio.
"""

import pandas as pd

from megamarket.sistema_experto_logistica import BASE_CONOCIMIENTO, a_booleano

COLUMNAS_CSV = [
    "cliente",
    "visita_mercaderista_disponible",
    "mercaderista_reporta_stock_bajo",
    "dias_desde_ultima_entrega",
    "queja_urgente",
    "precio_actualizado_en_punto_de_venta",
    "valor_factura_pedido",
    "costo_flete_estimado",
]
COLUMNAS_SI_NO = ["visita_mercaderista_disponible", "queja_urgente", "precio_actualizado_en_punto_de_venta"]
COLUMNAS_ENTERAS = ["dias_desde_ultima_entrega", "valor_factura_pedido", "costo_flete_estimado"]
OPCIONES_STOCK = ["Sí", "No", "No hubo visita"]


def _normalizar_stock(valor):
    texto = str(valor).strip().lower()
    if texto == "sí":
        return "Sí"
    if texto == "no":
        return "No"
    return "No hubo visita"


def validar_memoria(df):
    """Revisa que un CSV de memoria de trabajo se pueda pasar al motor.

    Devuelve una lista de errores en español (vacía si todo está bien).
    """
    faltantes = [c for c in COLUMNAS_CSV if c not in df.columns]
    if faltantes:
        return [f"Faltan columnas: {', '.join(faltantes)}."]

    errores = []
    clientes = list(df["cliente"].astype(str).str.strip())
    conocidos = list(BASE_CONOCIMIENTO["clientes"])
    desconocidos = [c for c in clientes if c not in conocidos]
    sin_fila = [c for c in conocidos if c not in clientes]
    repetidos = sorted({c for c in clientes if clientes.count(c) > 1})
    if desconocidos:
        errores.append(f"Clientes que no están en la base de conocimiento: {', '.join(desconocidos)}.")
    if sin_fila:
        errores.append(f"Faltan filas para: {', '.join(sin_fila)}.")
    if repetidos:
        errores.append(f"Clientes repetidos: {', '.join(repetidos)}.")

    for columna in COLUMNAS_ENTERAS:
        numeros = pd.to_numeric(df[columna], errors="coerce")
        if numeros.isna().any():
            errores.append(f"La columna «{columna}» tiene valores que no son números.")
        elif (numeros < 0).any():
            errores.append(f"La columna «{columna}» tiene valores negativos.")
    facturas = pd.to_numeric(df["valor_factura_pedido"], errors="coerce")
    if (facturas == 0).any():
        errores.append("El valor de la factura no puede ser 0 (R4 divide el flete entre la factura).")
    return errores


def csv_a_editor(df_csv):
    """DataFrame del CSV -> DataFrame para la tabla editable (casillas + columna Ruta)."""
    df = df_csv[COLUMNAS_CSV].copy()
    df["cliente"] = df["cliente"].astype(str).str.strip()
    for columna in COLUMNAS_SI_NO:
        df[columna] = df[columna].map(a_booleano)
    df["mercaderista_reporta_stock_bajo"] = df["mercaderista_reporta_stock_bajo"].map(_normalizar_stock)
    for columna in COLUMNAS_ENTERAS:
        df[columna] = pd.to_numeric(df[columna]).astype(int)
    rutas = {c: datos["ruta"] for c, datos in BASE_CONOCIMIENTO["clientes"].items()}
    df.insert(1, "ruta", df["cliente"].map(rutas))
    return df.reset_index(drop=True)


def editor_a_csv(df_editor):
    """DataFrame de la tabla editable -> mismo formato del CSV ("Sí"/"No")."""
    df = df_editor[COLUMNAS_CSV].copy()
    for columna in COLUMNAS_SI_NO:
        df[columna] = df[columna].map(lambda v: "Sí" if bool(v) else "No")
    return df


def csv_para_descargar(df_editor):
    """Texto del CSV con ';' y BOM, igual al de data/ (se abre bien en Excel)."""
    return "﻿" + editor_a_csv(df_editor).to_csv(sep=";", index=False)
