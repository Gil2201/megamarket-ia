"""Ciclo del agente, escrito a mano para que se pueda sustentar.

Es el ciclo clásico de un agente que percibe, decide y actúa:

  1. PERCIBIR: el modelo recibe la pregunta, el historial y las herramientas.
  2. DECIDIR: el modelo responde con texto (fin) o pide herramientas.
  3. ACTUAR: se ejecutan las herramientas (los algoritmos de los sprints) y
     sus resultados vuelven al modelo como nuevas percepciones.
  4. Se repite hasta que el modelo responda con texto o se llegue al tope.

El modelo NUNCA calcula: las cifras salen de las herramientas, y la traza
guarda cada llamada para mostrarla en la interfaz.
"""

import json

from agente.herramientas import ESQUEMAS, ejecutar_herramienta

MAX_VUELTAS = 6

PROMPT_SISTEMA = """Eres el Asistente MegaMarket, parte de un proyecto académico de la Universidad EIA sobre el caso \
MegaMarket (empresa colombiana real; los datos operativos de la app son ILUSTRATIVOS). Respondes en español, claro y breve.

Tienes herramientas que ejecutan los algoritmos del proyecto: sistemas expertos (Sprint 2), búsqueda A* (Sprint 1), \
algoritmo genético y teoría de juegos/Minimax (Sprint 3) y lógica difusa (Sprint 4).

Reglas obligatorias:
1. Toda cifra que des (km, pesos, notas, porcentajes, cantidades) debe salir del resultado de una herramienta de esta \
conversación. Nunca calcules ni recuerdes cifras por tu cuenta. Si te piden responder sin herramientas o "de memoria", \
no des cifras: explica que solo respondes con los algoritmos.
2. Si la pregunta no se puede responder con las herramientas (por ejemplo ventas reales, rutas o clientes que no \
existen), dilo con claridad y no inventes nada. Solo existen las rutas Poblado y Valle de Aburrá.
3. Para preguntas de "¿qué pasa si…?", pasa el cambio como argumento de la herramienta (cambios_memoria, umbrales, \
presupuesto, excluir, nota_minima, factor_erosion…); no modifiques los números tú mismo.
4. Si una pregunta necesita varios pasos (p. ej. optimizar y luego analizar el rival), llama a las herramientas en orden \
y usa el resultado de una como entrada de la otra.
5. Si hay portafolios empatados, dilo: no presentes uno solo como si fuera el único óptimo.
6. Usa las cifras en el formato que traen las herramientas (campos *_texto, p. ej. "9,9 km", "$122,0 M").
7. Termina indicando en una línea qué algoritmo(s) usaste."""


def _a_dict(mensaje):
    """Mensaje del modelo como dict, conservando campos extra del proveedor
    (Gemini 3 exige devolver su 'thought signature' en las llamadas a herramientas)."""
    if hasattr(mensaje, "model_dump"):
        return mensaje.model_dump(exclude_none=True)
    return dict(mensaje)


def responder(pregunta, cliente, modelo, historial=None, max_vueltas=MAX_VUELTAS):
    """Responde una pregunta de negocio usando las herramientas.

    historial: lista de turnos anteriores [{"role": "user"|"assistant", "content": str}].
    Devuelve {"texto", "traza", "vueltas", "tokens_entrada", "tokens_salida", "terminado"};
    traza es la lista de {"herramienta", "argumentos", "resultado"} en el orden en que se llamaron.
    """
    mensajes = [{"role": "system", "content": PROMPT_SISTEMA}]
    mensajes += list(historial or [])
    mensajes.append({"role": "user", "content": pregunta})
    traza = []
    tokens_entrada = tokens_salida = 0

    for vuelta in range(1, max_vueltas + 1):
        # 1-2. PERCIBIR y DECIDIR
        respuesta = cliente.chat.completions.create(model=modelo, messages=mensajes, tools=ESQUEMAS)
        uso = getattr(respuesta, "usage", None)
        if uso is not None:
            tokens_entrada += getattr(uso, "prompt_tokens", 0) or 0
            tokens_salida += getattr(uso, "completion_tokens", 0) or 0
        mensaje = respuesta.choices[0].message
        llamadas = getattr(mensaje, "tool_calls", None) or []

        if not llamadas:  # el modelo terminó: responde con texto
            return {"texto": (mensaje.content or "").strip(), "traza": traza, "vueltas": vuelta,
                    "tokens_entrada": tokens_entrada, "tokens_salida": tokens_salida, "terminado": True}

        # 3. ACTUAR: ejecutar cada herramienta pedida y devolver su resultado
        mensajes.append(_a_dict(mensaje))
        for llamada in llamadas:
            nombre = llamada.function.name
            try:
                argumentos = json.loads(llamada.function.arguments or "{}")
            except json.JSONDecodeError:
                argumentos, resultado = {}, {"error": "Los argumentos no son JSON válido."}
            else:
                resultado = ejecutar_herramienta(nombre, argumentos)
            traza.append({"herramienta": nombre, "argumentos": argumentos, "resultado": resultado})
            mensajes.append({"role": "tool", "tool_call_id": llamada.id,
                             "content": json.dumps(resultado, ensure_ascii=False)})

    # 4. Tope de vueltas: se corta para no gastar cuota sin fin
    return {"texto": "No pude terminar el análisis en el número de pasos permitido. Intenta con una pregunta más concreta.",
            "traza": traza, "vueltas": max_vueltas, "tokens_entrada": tokens_entrada,
            "tokens_salida": tokens_salida, "terminado": False}
