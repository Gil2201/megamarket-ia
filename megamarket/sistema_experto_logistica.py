"""Sprint 2 — Sistema experto 1: ¿qué clientes entran en la ruta de esta semana?

Portado de `referencia/sprint2/MegaMarket_Sprint2_SistemaExperto.ipynb`.
Estructura clásica vista en clase:

1. **Base de conocimiento**: lo que MegaMarket sabe de forma *estable*
   (reglas generales del negocio, atributos fijos de cada cliente).
2. **Memoria de trabajo**: los datos *de esta semana en particular* para
   cada cliente (leídos de un CSV).
3. **Motor de inferencia**: combina las dos piezas anteriores y concluye
   si el cliente entra en la ruta, con qué prioridad, y **por qué**.

Adaptaciones permitidas (SPEC §5.2): la lectura del CSV quedó en funciones
que reciben una ruta o un DataFrame ya cargado, y `decidir_clientes_de_la_ruta`
devuelve la traza en vez de imprimirla.

| # | Regla | Efecto |
|---|-------|--------|
| R1 | Mercaderista reporta stock bajo -> incluir; prioridad según rotación | Inclusión |
| R2 | Sin visita + más de 15 días sin entrega + rotación media/alta | Inclusión, BAJA |
| R3 | Queja urgente | Inclusión, ALTA |
| R4 | Flete > 4 % de la factura | Veto |
| R5 | PVP no actualizado | Veto |
| R6 | Ninguna de R1-R3 | Exclusión por defecto |
H1 — Política de entrega 48-72 h: se documenta, no filtra clientes.
"""

import pandas as pd

from megamarket.datos import RUTA_MEMORIA_LOGISTICA

# =============================================================================
# 6. BASE DE CONOCIMIENTO — reglas generales, hechos y relaciones (estable)
# =============================================================================
BASE_CONOCIMIENTO = {

    # --- Reglas generales de negocio (umbrales que usan R2 y R4) ---
    "umbrales": {
        "dias_sin_entrega": 15,        # días sin entrega para activar el respaldo (R2)
        "flete_sobre_factura": 0.04,   # 4% — tope de flete sobre la factura (R4)
    },

    # --- Política de servicio (H1): no filtra clientes, solo documenta el compromiso ---
    "politicas": {
        "ventana_entrega_horas": (48, 72),
    },

    # --- Hechos y relaciones: atributos FIJOS de cada cliente ---
    # (a diferencia de la visita del mercaderista o las quejas, la ruta y la
    # rotación del producto en ese punto no cambian cada semana)
    "clientes": {
        # Ruta Poblado
        "Fruver del Río":          {"ruta": "Poblado", "rotacion_producto": "alta"},
        "Fruver Visitación":       {"ruta": "Poblado", "rotacion_producto": "media"},
        "Five Sisters":            {"ruta": "Poblado", "rotacion_producto": "media"},
        "Supermercado Merka 10":   {"ruta": "Poblado", "rotacion_producto": "alta"},
        "Hotel Four Points":       {"ruta": "Poblado", "rotacion_producto": "baja"},
        "Mercados Verona":         {"ruta": "Poblado", "rotacion_producto": "media"},
        "EAFIT La Bodeguita":      {"ruta": "Poblado", "rotacion_producto": "alta"},
        "Redetrans":               {"ruta": "Poblado", "rotacion_producto": "baja"},

        # Ruta Valle de Aburrá (Sur)
        "CEDI Vaquita Itagüí":     {"ruta": "Valle de Aburrá", "rotacion_producto": "alta"},
        "CEDI Euro La Estrella":   {"ruta": "Valle de Aburrá", "rotacion_producto": "media"},
        "CEDI Merkepaisa":         {"ruta": "Valle de Aburrá", "rotacion_producto": "media"},
        "CEDI Supermú":            {"ruta": "Valle de Aburrá", "rotacion_producto": "baja"},
    },

    # --- Relación: destino final compartido por todas las rutas ---
    "destino_final": "Plataforma Logística",
}


# =============================================================================
# 7. MEMORIA DE TRABAJO — datos de ESTA semana (leídos desde CSV)
# =============================================================================
def leer_memoria_logistica(fuente=RUTA_MEMORIA_LOGISTICA):
    """Lee el CSV de la memoria de trabajo de logística y devuelve un DataFrame.

    `fuente` puede ser una ruta (o un archivo subido) o un DataFrame ya
    cargado (por ejemplo, el que devuelve el editor de la app).
    """
    if isinstance(fuente, pd.DataFrame):
        return fuente.copy()
    # sep=None + engine="python" detecta solo si el CSV viene separado por comas
    # o por punto y coma (Excel en español/Latinoamérica exporta con ";" porque
    # usa la coma como separador decimal). encoding="utf-8-sig" quita el BOM
    # invisible que Excel agrega al guardar como "CSV UTF-8". Así la celda no
    # se rompe sin importar cómo lo haya guardado la última persona que lo editó.
    return pd.read_csv(fuente, sep=None, engine="python", encoding="utf-8-sig")


def a_booleano(valor):
    """Convierte 'Sí' / 'No' del CSV a True / False."""
    return str(valor).strip().lower() == "sí"


def interpretar_stock_reportado(valor):
    """La columna 'mercaderista_reporta_stock_bajo' tiene TRES estados
    posibles, no dos: 'Sí' (reportó stock bajo), 'No' (visitó y el stock
    está bien) o 'No hubo visita' (no hay observación -- ahí es donde
    entra en juego la regla R2, el respaldo por falta de visibilidad).
    """
    valor = str(valor).strip().lower()
    if valor == "sí":
        return True
    if valor == "no":
        return False
    return None  # "No hubo visita" (o cualquier otro texto que no sea Sí/No)


def construir_memoria_trabajo(memoria_df):
    """Convierte el DataFrame del CSV en el diccionario MEMORIA_TRABAJO
    {cliente: {hecho: valor}} que usa el motor de inferencia."""
    MEMORIA_TRABAJO = {}
    for _, fila in memoria_df.iterrows():
        MEMORIA_TRABAJO[fila["cliente"]] = {
            "visita_mercaderista_disponible": a_booleano(fila["visita_mercaderista_disponible"]),
            "mercaderista_reporta_stock_bajo": interpretar_stock_reportado(fila["mercaderista_reporta_stock_bajo"]),
            "dias_desde_ultima_entrega": int(fila["dias_desde_ultima_entrega"]),
            "queja_urgente": a_booleano(fila["queja_urgente"]),
            "precio_actualizado_en_punto_de_venta": a_booleano(fila["precio_actualizado_en_punto_de_venta"]),
            "valor_factura_pedido": int(fila["valor_factura_pedido"]),
            "costo_flete_estimado": int(fila["costo_flete_estimado"]),
        }
    return MEMORIA_TRABAJO


# =============================================================================
# 8. MOTOR DE INFERENCIA
# =============================================================================
NIVEL_PRIORIDAD = {"ALTA": 3, "MEDIA": 2, "BAJA": 1}

# La rotación del producto en el punto de venta define la prioridad de R1
MAPA_ROTACION_PRIORIDAD = {"alta": "ALTA", "media": "MEDIA", "baja": "BAJA"}


def prioridad_mas_alta(actual, nueva):
    """Se queda con la prioridad más alta entre 'actual' y 'nueva'."""
    if actual is None or NIVEL_PRIORIDAD[nueva] > NIVEL_PRIORIDAD[actual]:
        return nueva
    return actual


def motor_inferencia(cliente, base_conocimiento, memoria_trabajo):
    """Aplica la base de conocimiento (reglas) sobre los hechos de UN
    cliente (memoria de trabajo) y devuelve la conclusión: si entra en la
    ruta de esta semana, con qué prioridad, y por qué.

    Devuelve {"incluir_en_ruta": bool, "prioridad": str | None, "razones": [str]}.
    """
    hechos_fijos = base_conocimiento["clientes"][cliente]   # ruta, rotacion_producto
    hechos_semana = memoria_trabajo[cliente]                # visita, dias, queja, PVP, factura, flete
    umbrales = base_conocimiento["umbrales"]

    razones = []
    prioridad = None

    # --- R1: el mercaderista vio, en su última visita, que el stock está bajo ---
    if hechos_semana["visita_mercaderista_disponible"] and hechos_semana["mercaderista_reporta_stock_bajo"]:
        rotacion = hechos_fijos["rotacion_producto"]
        prioridad_r1 = MAPA_ROTACION_PRIORIDAD[rotacion]
        razones.append(
            f"R1 - El mercaderista reportó stock bajo en su visita "
            f"(rotación {rotacion} -> prioridad {prioridad_r1})"
        )
        prioridad = prioridad_mas_alta(prioridad, prioridad_r1)

    # --- R2: respaldo por falta de visibilidad (sin visita + mucho tiempo + rotación relevante) ---
    # OJO: si SÍ hubo visita reciente, esta regla NO aplica -- la observación
    # directa del mercaderista manda sobre cualquier estimación por tiempo.
    if (not hechos_semana["visita_mercaderista_disponible"]
            and hechos_semana["dias_desde_ultima_entrega"] > umbrales["dias_sin_entrega"]
            and hechos_fijos["rotacion_producto"] in ("media", "alta")):
        razones.append(
            f"R2 - Sin visita reciente del mercaderista, "
            f"{hechos_semana['dias_desde_ultima_entrega']} días sin entrega "
            f"(> {umbrales['dias_sin_entrega']}), rotación {hechos_fijos['rotacion_producto']}"
        )
        prioridad = prioridad_mas_alta(prioridad, "BAJA")

    # --- R3: queja urgente reportada ---
    if hechos_semana["queja_urgente"]:
        razones.append("R3 - Queja urgente reportada: debe visitarse primero")
        prioridad = prioridad_mas_alta(prioridad, "ALTA")

    # --- R6: regla por defecto (ninguna regla de inclusión se cumplió) ---
    if not razones:
        return {
            "incluir_en_ruta": False,
            "prioridad": None,
            "razones": ["R6 - Por defecto: no cumple ningún criterio de inclusión esta semana"],
        }

    # --- R4 y R5: restricciones duras (veto). Solo importan si el cliente ya es candidato ---
    vetos = []

    ratio_flete = hechos_semana["costo_flete_estimado"] / hechos_semana["valor_factura_pedido"]
    if ratio_flete > umbrales["flete_sobre_factura"]:
        vetos.append(
            f"R4 (VETO) - El flete (${hechos_semana['costo_flete_estimado']:,}) es el "
            f"{ratio_flete:.1%} de la factura (${hechos_semana['valor_factura_pedido']:,}), "
            f"por encima del {umbrales['flete_sobre_factura']:.0%} permitido"
        )

    if not hechos_semana["precio_actualizado_en_punto_de_venta"]:
        vetos.append(
            "R5 (VETO) - El punto de venta no ha actualizado el PVP de la "
            "referencia según la lista vigente de MegaMarket"
        )

    if vetos:
        razones.extend(vetos)
        return {"incluir_en_ruta": False, "prioridad": None, "razones": razones}

    return {"incluir_en_ruta": True, "prioridad": prioridad, "razones": razones}


def decidir_clientes_de_la_ruta(nombre_ruta, base_conocimiento, memoria_trabajo):
    """Corre el motor de inferencia sobre TODOS los clientes de una ruta y
    devuelve la lista de clientes incluidos + su prioridad — el mismo
    formato que antes recibía 'clientes_poblado' / 'clientes_valle_aburra'
    a mano — junto con la traza de razonamiento.

    Responde: ¿a quién visitamos esta semana en esta ruta y con qué prioridad?
    Devuelve (incluidos, prioridad_por_cliente, traza), donde traza es una
    lista de {"cliente", "incluir_en_ruta", "prioridad", "razones"}.
    """
    clientes_de_la_ruta = [
        c for c, datos in base_conocimiento["clientes"].items()
        if datos["ruta"] == nombre_ruta
    ]

    incluidos = []
    prioridad_por_cliente = {}
    traza = []

    for cliente in clientes_de_la_ruta:
        conclusion = motor_inferencia(cliente, base_conocimiento, memoria_trabajo)
        traza.append({"cliente": cliente, **conclusion})

        if conclusion["incluir_en_ruta"]:
            incluidos.append(cliente)
            prioridad_por_cliente[cliente] = conclusion["prioridad"]

    return incluidos, prioridad_por_cliente, traza
