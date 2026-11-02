"""Herramientas del agente: cada una envuelve funciones de megamarket/.

Reglas:
- Ninguna modifica los datos originales: los cambios "¿qué pasa si…?" se
  aplican sobre copias.
- Devuelven dicts serializables a JSON. Las cifras van en bruto y también en
  texto en español ("9,9 km", "$122,0 M") para que el modelo las repita tal cual.
- Ante un dato inválido devuelven {"error": "..."} en vez de lanzar una
  excepción, para que el modelo pueda corregirse.
"""

import copy
import json
import unicodedata

from megamarket import competidor, difuso, genetico
from megamarket.busqueda import REDES, recorrido_completo, tramos_del_recorrido
from megamarket.datos import BODEGA, CANDIDATOS, EROSION, ESPACIO_BODEGA_TOTAL, PLATAFORMA, PRESUPUESTO_TOTAL, SEMILLA
from megamarket.sistema_experto_logistica import (
    BASE_CONOCIMIENTO,
    construir_memoria_trabajo,
    decidir_clientes_de_la_ruta,
    leer_memoria_logistica,
)
from megamarket.sistema_experto_portafolio import (
    CRITERIOS_DETALLE,
    CRITERIOS_NOMBRES,
    construir_memoria_trabajo_portafolio,
    evaluar_producto,
    leer_memoria_portafolio,
)

RUTAS = list(REDES)
COLUMNAS_SI_NO = {"visita_mercaderista_disponible", "queja_urgente", "precio_actualizado_en_punto_de_venta"}
COLUMNAS_NUMERICAS = {"dias_desde_ultima_entrega", "valor_factura_pedido", "costo_flete_estimado"}
COLUMNA_STOCK = "mercaderista_reporta_stock_bajo"


# =============================================================================
# FORMATO (español, igual que la interfaz)
# =============================================================================
def _numero(valor, decimales):
    return f"{valor:,.{decimales}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _km(valor):
    return f"{_numero(valor, 1)} km"


def _cop_m(valor):
    signo = "−" if valor < 0 else ""
    return f"{signo}${_numero(abs(valor) / 1e6, 1)} M"


def _normalizar(texto):
    """Minúsculas, sin tildes ni " Riovalle", para comparar nombres."""
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return texto.lower().replace(" riovalle", "").strip()


def _buscar(nombre, opciones):
    """Encuentra un nombre entre opciones aunque venga sin tildes o abreviado."""
    objetivo = _normalizar(nombre)
    for opcion in opciones:
        if _normalizar(opcion) == objetivo:
            return opcion
    parecidos = [o for o in opciones if objetivo and objetivo in _normalizar(o)]
    return parecidos[0] if len(parecidos) == 1 else None


def _corto(nombre):
    return nombre.replace(" Riovalle", "")


# =============================================================================
# LOGÍSTICA (Sprint 2 + Sprint 1)
# =============================================================================
def _memoria_y_base(cambios_memoria=None, umbrales=None):
    """Memoria de trabajo y base de conocimiento con los cambios pedidos (sobre copias)."""
    df = leer_memoria_logistica()
    clientes = list(df["cliente"])
    for nombre, cambios in (cambios_memoria or {}).items():
        cliente = _buscar(nombre, clientes)
        if cliente is None:
            return None, None, f"No existe el cliente «{nombre}». Clientes: {', '.join(clientes)}."
        for columna, valor in (cambios or {}).items():
            if columna in COLUMNAS_SI_NO:
                valor = "Sí" if (valor is True or _normalizar(valor) in ("si", "true")) else "No"
            elif columna == COLUMNA_STOCK:
                valor = {"si": "Sí", "true": "Sí", "no": "No", "false": "No"}.get(_normalizar(valor), "No hubo visita")
            elif columna in COLUMNAS_NUMERICAS:
                try:
                    valor = int(float(valor))
                except (TypeError, ValueError):
                    return None, None, f"«{columna}» debe ser un número."
                if columna == "valor_factura_pedido" and valor <= 0:
                    return None, None, "La factura debe ser mayor que 0."
            else:
                return None, None, (f"Columna desconocida «{columna}». Columnas: "
                                    f"{', '.join(sorted(COLUMNAS_SI_NO | COLUMNAS_NUMERICAS | {COLUMNA_STOCK}))}.")
            df.loc[df["cliente"] == cliente, columna] = valor
    base = copy.deepcopy(BASE_CONOCIMIENTO)
    for clave, valor in (umbrales or {}).items():
        if clave not in base["umbrales"]:
            return None, None, f"Umbral desconocido «{clave}». Umbrales: dias_sin_entrega, flete_sobre_factura."
        base["umbrales"][clave] = float(valor) if clave == "flete_sobre_factura" else int(valor)
    return construir_memoria_trabajo(df), base, None


def _rutas_pedidas(ruta):
    if ruta in (None, "", "Ambas"):
        return RUTAS
    encontrada = _buscar(ruta, RUTAS)
    return [encontrada] if encontrada else None


def decidir_clientes_semana(ruta="Ambas", cambios_memoria=None, umbrales=None):
    """Sistema experto (Sprint 2): quién entra en la ruta esta semana, con qué prioridad y por qué."""
    rutas = _rutas_pedidas(ruta)
    if rutas is None:
        return {"error": f"No existe la ruta «{ruta}». Solo existen: {', '.join(RUTAS)}."}
    memoria, base, error = _memoria_y_base(cambios_memoria, umbrales)
    if error:
        return {"error": error}
    salida = {"algoritmo": "Sistema experto (Sprint 2): reglas R1–R6, encadenamiento hacia adelante",
              "umbrales": base["umbrales"], "rutas": {}}
    for nombre_ruta in rutas:
        incluidos, prioridad, traza = decidir_clientes_de_la_ruta(nombre_ruta, base, memoria)
        salida["rutas"][nombre_ruta] = {
            "incluidos": incluidos,
            "prioridad": prioridad,
            "clientes_incluidos": f"{len(incluidos)} de {len(traza)}",
            "decisiones": [{"cliente": t["cliente"], "incluir": t["incluir_en_ruta"],
                            "prioridad": t["prioridad"], "razones": t["razones"]} for t in traza],
        }
    return salida


def calcular_ruta(ruta="Ambas", fuente_clientes="sistema_experto", clientes=None, cambios_memoria=None, umbrales=None):
    """A* (Sprint 1): orden de visita y km desde la bodega hasta la plataforma logística."""
    rutas = _rutas_pedidas(ruta)
    if rutas is None:
        return {"error": f"No existe la ruta «{ruta}». Solo existen: {', '.join(RUTAS)}."}
    memoria, base, error = _memoria_y_base(cambios_memoria, umbrales)
    if error:
        return {"error": error}
    salida = {"algoritmo": "Búsqueda A* + vecino más cercano por tandas de prioridad (Sprint 1)",
              "fuente_clientes": fuente_clientes, "rutas": {}}
    total = 0.0
    for nombre_ruta in rutas:
        universo = [c for c, d in BASE_CONOCIMIENTO["clientes"].items() if d["ruta"] == nombre_ruta]
        prioridad = None
        if fuente_clientes == "todos":
            lista = universo
        elif fuente_clientes == "lista":
            lista = []
            for nombre in clientes or []:
                cliente = _buscar(nombre, universo)
                if cliente is None:
                    return {"error": f"«{nombre}» no es cliente de la ruta {nombre_ruta}. Clientes: {', '.join(universo)}."}
                lista.append(cliente)
        else:
            lista, prioridad, _ = decidir_clientes_de_la_ruta(nombre_ruta, base, memoria)
        paradas, km, orden = recorrido_completo(REDES[nombre_ruta], BODEGA, lista, PLATAFORMA, prioridad)
        total += km
        salida["rutas"][nombre_ruta] = {
            "km": round(km, 2), "km_texto": _km(km),
            "orden_entrega": orden,
            "prioridad": prioridad or {},
            "nodos_de_paso": [n for n in dict.fromkeys(paradas) if n in universo and n not in orden],
            "tramos": [{"desde": t["desde"], "hasta": t["hasta"], "km": round(t["km"], 2),
                        "camino": t["camino"]} for t in tramos_del_recorrido(REDES[nombre_ruta], BODEGA, orden, PLATAFORMA)],
        }
    if len(rutas) > 1:
        salida["km_total"] = round(total, 2)
        salida["km_total_texto"] = _km(total)
    return salida


# =============================================================================
# PORTAFOLIO (Sprint 2 + Sprint 4)
# =============================================================================
def evaluar_viabilidad(producto):
    """Sistema experto de portafolio (Sprint 2): ¿la categoría cumple C1–C7?"""
    memoria = construir_memoria_trabajo_portafolio(leer_memoria_portafolio())
    nombre = _buscar(producto, memoria)
    if nombre is None:
        return {"error": f"No hay datos de «{producto}». Categorías evaluadas: {', '.join(memoria)}."}
    resultado = evaluar_producto(nombre, memoria, CRITERIOS_NOMBRES, CRITERIOS_DETALLE)
    return {"algoritmo": "Sistema experto de portafolio (Sprint 2): viable solo si cumple C1 Y … Y C7",
            "producto": nombre, "viable": resultado["viable"],
            "incumplidos": [{"criterio": c, "nombre": CRITERIOS_NOMBRES[c]} for c in resultado["incumplidos"]]}


def nota_viabilidad(producto=None, cambios=None):
    """Lógica difusa (Sprint 4): nota 0–100 con la jerarquía de 5 sistemas Mamdani.

    Sin producto, devuelve la nota de todos.
    """
    productos = difuso.construir_productos_difusos(difuso.leer_memoria_difusa())
    if not producto:
        notas = difuso.notas_de_productos(productos)
        return {"algoritmo": "Lógica difusa Mamdani (Sprint 4)",
                "notas": {n: (round(v, 1) if v is not None else None) for n, v in notas.items()},
                "etiquetas": {n: (difuso.etiqueta_dominante(v) if v is not None else "no viable") for n, v in notas.items()}}
    nombre = _buscar(producto, productos)
    if nombre is None:
        return {"error": f"No hay datos difusos de «{producto}». Productos: {', '.join(productos)}."}
    datos = dict(productos[nombre])
    for criterio, valor in (cambios or {}).items():
        if criterio not in difuso.CRITERIOS_DIFUSOS and criterio != "C2":
            return {"error": f"Criterio desconocido «{criterio}». Criterios: {', '.join(difuso.CRITERIOS_DIFUSOS)}, C2."}
        datos[criterio] = bool(valor) if criterio == "C2" else float(valor)
    try:
        r = difuso.nota_viabilidad(datos)
    except ValueError as error:
        return {"error": str(error)}
    nombres_nodos = {k: s["nombre"] for k, s in difuso.SISTEMAS_VIABILIDAD.items()}
    return {
        "algoritmo": "Lógica difusa Mamdani (Sprint 4): jerarquía de 5 sistemas de 2 entradas y 9 reglas",
        "producto": nombre, "datos": {c: datos[c] for c in difuso.CRITERIOS_DIFUSOS},
        "cumple_registro_sanitario_C2": r["cumple_C2"],
        "nota": round(r["nota"], 1) if r["nota"] is not None else None,
        "etiqueta": r["etiqueta"],
        "nodos": {f"{k} {nombres_nodos[k]}": {"valor": round(n["valor"], 1),
                                              "etiqueta": difuso.etiqueta_dominante(n["valor"])}
                  for k, n in r["nodos"].items()},
    }


def _portafolio_texto(individuo, candidatos):
    return {"productos": [_corto(n) for n in genetico.nombre_incluidos(individuo, candidatos)],
            "utilidad": genetico.utilidad_total(individuo, candidatos),
            "utilidad_texto": _cop_m(genetico.utilidad_total(individuo, candidatos)),
            "costo_texto": _cop_m(genetico.costo_total(individuo, candidatos)),
            "espacio": genetico.espacio_total(individuo, candidatos)}


def optimizar_portafolio(presupuesto=None, espacio=None, excluir=None, nota_minima=None):
    """Algoritmo genético (Sprint 3A) validado con fuerza bruta: qué referencias lanzar."""
    presupuesto = int(presupuesto or PRESUPUESTO_TOTAL)
    espacio = int(espacio or ESPACIO_BODEGA_TOTAL)
    candidatos = dict(CANDIDATOS)
    excluidos = []
    for nombre in excluir or []:
        encontrado = _buscar(nombre, candidatos)
        if encontrado is None:
            return {"error": f"«{nombre}» no es un candidato. Candidatos: {', '.join(_corto(c) for c in CANDIDATOS)}."}
        candidatos.pop(encontrado)
        excluidos.append(_corto(encontrado))
    excluidos_por_nota = {}
    if nota_minima is not None:
        notas = difuso.notas_de_productos(difuso.construir_productos_difusos(difuso.leer_memoria_difusa()))
        for nombre in list(candidatos):
            if notas.get(nombre) is not None and notas[nombre] < float(nota_minima):
                excluidos_por_nota[_corto(nombre)] = round(notas[nombre], 1)
                candidatos.pop(nombre)
    if len(candidatos) < 2:
        return {"error": "Quedan menos de 2 candidatos: no hay nada que optimizar."}

    mejor, historial = genetico.ejecutar_experimento(semilla=SEMILLA, candidatos=candidatos,
                                                     presupuesto=presupuesto, espacio=espacio)
    fb = genetico.validar_con_fuerza_bruta(candidatos, presupuesto, espacio)
    return {
        "algoritmo": "Algoritmo genético (Sprint 3A, semilla 42, población 10, 15 generaciones) validado con fuerza bruta",
        "presupuesto_texto": _cop_m(presupuesto), "espacio_disponible": espacio,
        "excluidos": excluidos, "excluidos_por_nota_baja": excluidos_por_nota,
        "portafolio_ag": _portafolio_texto(mejor, candidatos),
        "utilidad_optima": fb["mejor_utilidad_fb"], "utilidad_optima_texto": _cop_m(fb["mejor_utilidad_fb"]),
        "el_ag_llego_al_optimo": genetico.utilidad_total(mejor, candidatos) == fb["mejor_utilidad_fb"],
        "portafolios_optimos_empatados": [_portafolio_texto(o, candidatos) for o in fb["optimos"]],
        "combinaciones_validas": len(fb["validas"]),
    }


def _individuo(productos):
    individuo, faltantes = [], []
    elegidos = set()
    for nombre in productos:
        encontrado = _buscar(nombre, CANDIDATOS)
        if encontrado is None:
            faltantes.append(nombre)
        elegidos.add(encontrado)
    if faltantes:
        return None, f"No son candidatos: {', '.join(faltantes)}. Candidatos: {', '.join(_corto(c) for c in CANDIDATOS)}."
    return tuple(1 if n in elegidos else 0 for n in CANDIDATOS), None


def analizar_competidor(portafolio=None, factor_erosion=1.0, k_ataques=1, presupuesto=None, espacio=None):
    """Minimax (Sprint 3B): peor caso de un portafolio si un rival ataca, y el que mejor aguanta."""
    presupuesto = int(presupuesto or PRESUPUESTO_TOTAL)
    espacio = int(espacio or ESPACIO_BODEGA_TOTAL)
    k = int(k_ataques or 1)
    erosion = {n: min(0.95, e * float(factor_erosion or 1.0)) for n, e in EROSION.items()}
    if portafolio:
        individuo, error = _individuo(portafolio)
        if error:
            return {"error": error}
    else:
        individuo = competidor.PORTAFOLIO_SPRINT3

    arbol = competidor.mostrar_arbol(individuo, "evaluado", erosion)
    peor = competidor.utilidad_peor_caso(individuo, erosion, k)
    valor = lambda ind: competidor.utilidad_peor_caso(ind, erosion, k)
    mejor_valor, optimos, _ = competidor.fuerza_bruta(valor, CANDIDATOS, presupuesto, espacio)
    return {
        "algoritmo": "Minimax de dos niveles (Sprint 3B): MAX elige portafolio, MIN (el rival) ataca donde más daño hace",
        "factor_erosion": float(factor_erosion or 1.0), "k_ataques": k, "presupuesto_texto": _cop_m(presupuesto),
        "portafolio_evaluado": {
            "productos": arbol["productos"],
            "cabe_en_presupuesto_y_bodega": competidor.es_portafolio_valido(individuo, CANDIDATOS, presupuesto, espacio),
            "utilidad_esperada_texto": _cop_m(arbol["utilidad_esperada"]),
            "peor_caso": peor, "peor_caso_texto": _cop_m(peor),
            "rival_ataca": arbol["rival_ataca"] if k == 1 else f"los {k} productos que más daño hacen",
            "si_el_rival_ataca_cada_producto": {p: _cop_m(v) for p, v in arbol["ataques"]},
        },
        "mejor_peor_caso_posible": mejor_valor, "mejor_peor_caso_posible_texto": _cop_m(mejor_valor),
        "portafolios_que_mejor_aguantan": [
            {"productos": competidor.nombre_incluidos(o), "utilidad_esperada_texto": _cop_m(competidor.utilidad_total(o)),
             "peor_caso_texto": _cop_m(valor(o)), "espacio": competidor.espacio_total(o)}
            for o in optimos
        ],
    }


def juego_producto(producto, erosion, pago_rival_si_lanzamos=6_000_000, pago_rival_si_no_lanzamos=18_000_000):
    """Teoría de juegos (Sprint 3B): matriz 2x2, Nash e inducción hacia atrás de un producto."""
    nombre = _buscar(producto, CANDIDATOS)
    if nombre is None:
        return {"error": f"«{producto}» no es un candidato. Candidatos: {', '.join(_corto(c) for c in CANDIDATOS)}."}
    if not 0 <= float(erosion) <= 0.95:
        return {"error": "La erosión debe estar entre 0 y 0,95."}
    caso = competidor.mostrar_caso("Juego", nombre, float(erosion), float(pago_rival_si_lanzamos),
                                   float(pago_rival_si_no_lanzamos))
    filas, cols = competidor.FILAS, competidor.COLS
    i, j = caso["secuencial"]
    return {
        "algoritmo": "Juego 2x2 (Sprint 3B): equilibrios de Nash puros e inducción hacia atrás",
        "producto": _corto(nombre),
        "matriz": {f"Riovalle {filas[a]} / Rival {cols[b]}":
                   f"Riovalle {_cop_m(caso['A'][a][b])} ; Rival {_cop_m(caso['B'][a][b])}"
                   for a in range(2) for b in range(2)},
        "equilibrios_nash": [f"({filas[a]}, {cols[b]})" for a, b in caso["nash"]],
        "si_riovalle_mueve_primero": f"({filas[i]}, {cols[j]})",
        "pago_riovalle_texto": _cop_m(caso["pago_riovalle"]),
        "pago_rival_texto": _cop_m(caso["pago_rival"]),
        "erosion_de_equilibrio": f"{_numero(competidor.erosion_de_equilibrio(nombre) * 100, 1)} %",
    }


def desempatar_portafolios(criterio="esperada", tolerancia=0.0):
    """Lógica difusa (Sprint 4): elige entre portafolios empatados por nota y exposición al rival."""
    if criterio == "esperada":
        valor = competidor.utilidad_total
    elif criterio == "peor_caso":
        valor = competidor.utilidad_peor_caso
    else:
        return {"error": "criterio debe ser «esperada» o «peor_caso»."}
    _, _, validas = competidor.fuerza_bruta(competidor.utilidad_total)
    empatados = difuso.empates_con_tolerancia(validas, valor, float(tolerancia or 0.0))
    if len(empatados) < 2:
        return {"resultado": "No hay empate: un solo portafolio alcanza el mejor valor.",
                "portafolio": competidor.nombre_incluidos(empatados[0])}
    notas = difuso.notas_de_productos(difuso.construir_productos_difusos(difuso.leer_memoria_difusa()))
    nombres = [[n for n, g in zip(CANDIDATOS, ind) if g] for ind in empatados]
    ranking = difuso.desempatar_portafolios(nombres, CANDIDATOS, EROSION, notas, ESPACIO_BODEGA_TOTAL)
    return {
        "algoritmo": "Desempate difuso Mamdani (Sprint 4): nota promedio × exposición al competidor",
        "criterio": criterio, "valor_empatado_texto": _cop_m(valor(empatados[0])),
        "ranking": [{"productos": [_corto(p) for p in r["productos"]],
                     "preferencia": round(r["preferencia"], 1),
                     "nota_promedio": round(r["nota_promedio"], 1),
                     "exposicion_competidor": f"{_numero(r['exposicion'], 1)} %",
                     "holgura_bodega": r["holgura"]} for r in ranking],
        "ganador": [_corto(p) for p in ranking[0]["productos"]],
        "decidio": ranking[0]["criterio"],
    }


# =============================================================================
# REGISTRO DE HERRAMIENTAS: función + esquema JSON (formato compatible con OpenAI)
# =============================================================================
_CAMBIOS_MEMORIA = {
    "type": "object",
    "description": ("Cambios a los datos de ESTA semana, por cliente. Ej: {\"Fruver del Río\": "
                    "{\"costo_flete_estimado\": 30000}}. Columnas: costo_flete_estimado, valor_factura_pedido, "
                    "dias_desde_ultima_entrega (números); queja_urgente, visita_mercaderista_disponible, "
                    "precio_actualizado_en_punto_de_venta (true/false); mercaderista_reporta_stock_bajo (Sí/No/No hubo visita)."),
}
_UMBRALES = {
    "type": "object",
    "description": "Umbrales de la base de conocimiento. flete_sobre_factura es una fracción (0.04 = 4 %); dias_sin_entrega un entero.",
    "properties": {"flete_sobre_factura": {"type": "number"}, "dias_sin_entrega": {"type": "integer"}},
}
_RUTA = {"type": "string", "enum": RUTAS + ["Ambas"], "description": "Ruta de reparto. «Ambas» calcula las dos."}
_PRODUCTOS = {"type": "array", "items": {"type": "string"},
              "description": "Nombres de referencias Riovalle, p. ej. «Higo Deshidratado», «Jugo Natural»."}

HERRAMIENTAS = {
    "decidir_clientes_semana": (decidir_clientes_semana, {
        "description": "Sistema experto (Sprint 2): decide qué clientes entran en la ruta de esta semana, con qué "
                       "prioridad y por qué (reglas R1–R6 y vetos). Úsala para preguntas de por qué un cliente entra o no.",
        "properties": {"ruta": _RUTA, "cambios_memoria": _CAMBIOS_MEMORIA, "umbrales": _UMBRALES},
    }),
    "calcular_ruta": (calcular_ruta, {
        "description": "Búsqueda A* (Sprint 1): km y orden de visita desde la Bodega Olaya Herrera hasta la Plataforma "
                       "Logística. Por defecto usa los clientes que decide el sistema experto esta semana.",
        "properties": {"ruta": _RUTA,
                       "fuente_clientes": {"type": "string", "enum": ["sistema_experto", "todos", "lista"],
                                           "description": "sistema_experto (por defecto), todos los clientes de la ruta, o una lista."},
                       "clientes": {"type": "array", "items": {"type": "string"}, "description": "Solo si fuente_clientes = lista."},
                       "cambios_memoria": _CAMBIOS_MEMORIA, "umbrales": _UMBRALES},
    }),
    "evaluar_viabilidad": (evaluar_viabilidad, {
        "description": "Sistema experto de portafolio (Sprint 2): si una categoría (aseo, Alquería, bebidas) cumple "
                       "los 7 criterios C1–C7 y cuáles falla. Responde Sí/No.",
        "properties": {"producto": {"type": "string", "description": "Nombre de la categoría."}},
        "required": ["producto"],
    }),
    "nota_viabilidad": (nota_viabilidad, {
        "description": "Lógica difusa (Sprint 4): nota de viabilidad 0–100 de un producto o categoría y el valor de "
                       "cada sistema de la jerarquía. Sin producto devuelve la nota de todos.",
        "properties": {"producto": {"type": "string"},
                       "cambios": {"type": "object", "description": "Cambios a los criterios numéricos, p. ej. {\"margen_pct\": 30}."}},
    }),
    "optimizar_portafolio": (optimizar_portafolio, {
        "description": "Algoritmo genético (Sprint 3A) validado con fuerza bruta: qué referencias Riovalle lanzar para "
                       "maximizar la utilidad con el presupuesto y la bodega. Devuelve también los portafolios empatados.",
        "properties": {"presupuesto": {"type": "number", "description": "COP. Por defecto 70.000.000."},
                       "espacio": {"type": "integer", "description": "Posiciones de bodega. Por defecto 25."},
                       "excluir": _PRODUCTOS,
                       "nota_minima": {"type": "number", "description": "Excluye candidatos con nota difusa menor."}},
    }),
    "analizar_competidor": (analizar_competidor, {
        "description": "Minimax (Sprint 3B): cuánto deja un portafolio en el peor caso si un rival ataca, qué producto "
                       "ataca, y qué portafolio aguanta mejor. Sin portafolio evalúa el del Sprint 3 (Higo, Jugo, Café).",
        "properties": {"portafolio": _PRODUCTOS,
                       "factor_erosion": {"type": "number", "description": "Fuerza del rival. 1 = supuesto base; 1.5 = 50 % más fuerte."},
                       "k_ataques": {"type": "integer", "description": "Cuántos productos ataca a la vez. Por defecto 1."},
                       "presupuesto": {"type": "number", "description": "COP. Por defecto 70.000.000."},
                       "espacio": {"type": "integer"}},
    }),
    "juego_producto": (juego_producto, {
        "description": "Teoría de juegos (Sprint 3B): matriz 2x2 Riovalle vs. rival para un producto, equilibrios de "
                       "Nash y qué pasa si Riovalle mueve primero.",
        "properties": {"producto": {"type": "string"},
                       "erosion": {"type": "number", "description": "Fracción de utilidad que quita el rival (0.5 = 50 %)."},
                       "pago_rival_si_lanzamos": {"type": "number", "description": "COP que gana el rival si entra y Riovalle lanzó. "
                                                  "Pásalo solo si la pregunta lo da; por defecto 6.000.000 (notebook)."},
                       "pago_rival_si_no_lanzamos": {"type": "number", "description": "COP que gana el rival si entra y Riovalle no "
                                                     "lanzó. Pásalo solo si la pregunta lo da; por defecto 18.000.000 (notebook)."}},
        "required": ["producto", "erosion"],
    }),
    "desempatar_portafolios": (desempatar_portafolios, {
        "description": "Lógica difusa (Sprint 4): cuando varios portafolios empatan, elige uno por nota de viabilidad "
                       "promedio y exposición al competidor.",
        "properties": {"criterio": {"type": "string", "enum": ["esperada", "peor_caso"],
                                    "description": "esperada = empate en utilidad; peor_caso = empate con Minimax."},
                       "tolerancia": {"type": "number", "description": "Fracción; 0 = solo empates exactos."}},
    }),
}

ESQUEMAS = [
    {"type": "function", "function": {
        "name": nombre, "description": esquema["description"],
        "parameters": {"type": "object", "properties": esquema["properties"], "required": esquema.get("required", [])},
    }}
    for nombre, (_, esquema) in HERRAMIENTAS.items()
]


def ejecutar_herramienta(nombre, argumentos):
    """Ejecuta una herramienta por nombre. Nunca lanza: los errores vuelven como {"error": ...}."""
    if nombre not in HERRAMIENTAS:
        return {"error": f"No existe la herramienta «{nombre}». Herramientas: {', '.join(HERRAMIENTAS)}."}
    funcion, esquema = HERRAMIENTAS[nombre]
    permitidos = set(esquema["properties"])
    argumentos = {k: v for k, v in (argumentos or {}).items() if k in permitidos}
    faltan = [r for r in esquema.get("required", []) if r not in argumentos]
    if faltan:
        return {"error": f"Faltan argumentos: {', '.join(faltan)}."}
    try:
        resultado = funcion(**argumentos)
    except Exception as error:  # una herramienta nunca debe tumbar el agente
        return {"error": f"{type(error).__name__}: {error}"}
    # Garantiza JSON (numpy, tuplas, etc.)
    return json.loads(json.dumps(resultado, ensure_ascii=False, default=float))
