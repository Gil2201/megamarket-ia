"""Pruebas del agente SIN llamar a ninguna API (gratis y deterministas).

- Cada herramienta devuelve las respuestas de las preguntas de prueba.
- El ciclo del agente se prueba con un proveedor falso que sigue un guion.
"""

import json
from types import SimpleNamespace

import pytest

from agente import bucle
from agente.herramientas import ESQUEMAS, HERRAMIENTAS, ejecutar_herramienta
from evaluacion_agente.preguntas import construir_preguntas

HECHOS = {p["id"]: p["hechos"] for p in construir_preguntas()}


# =============================================================================
# Herramientas
# =============================================================================
def test_cada_herramienta_tiene_esquema():
    assert {e["function"]["name"] for e in ESQUEMAS} == set(HERRAMIENTAS)
    json.dumps(ESQUEMAS)  # serializable


@pytest.mark.parametrize("nombre, argumentos, ruta, km", [
    ("calcular_ruta", {"ruta": "Poblado"}, "Poblado", HECHOS["P01"]["km"]),
    ("calcular_ruta", {"ruta": "Valle de Aburrá", "fuente_clientes": "todos"}, "Valle de Aburrá", HECHOS["P02"]["km"]),
    ("calcular_ruta", {"ruta": "Poblado", "cambios_memoria": {"Fruver del Rio": {"costo_flete_estimado": 30000}}},
     "Poblado", HECHOS["P08"]["km"]),
])
def test_calcular_ruta(nombre, argumentos, ruta, km):
    r = ejecutar_herramienta(nombre, argumentos)
    assert round(r["rutas"][ruta]["km"], 1) == km


def test_umbral_de_flete_en_las_dos_rutas():
    r = ejecutar_herramienta("calcular_ruta", {"umbrales": {"flete_sobre_factura": 0.06}})
    assert round(r["km_total"], 1) == HECHOS["P09"]["km_total"]


def test_por_que_fruver_del_rio_no_entra():
    r = ejecutar_herramienta("decidir_clientes_semana", {"ruta": "Poblado"})
    fruver = next(d for d in r["rutas"]["Poblado"]["decisiones"] if d["cliente"] == "Fruver del Río")
    assert fruver["incluir"] is False and fruver["razones"][1].startswith("R4 (VETO)")


def test_portafolio_y_empates():
    r = ejecutar_herramienta("optimizar_portafolio", {})
    assert r["utilidad_optima"] == HECHOS["P04"]["utilidad"]
    assert len(r["portafolios_optimos_empatados"]) == 2
    r = ejecutar_herramienta("optimizar_portafolio", {"nota_minima": 60})
    assert r["utilidad_optima"] == HECHOS["P14"]["utilidad"]
    assert set(r["excluidos_por_nota_baja"]) == set(HECHOS["P14"]["excluidos"])


def test_competidor_y_desempate():
    r = ejecutar_herramienta("analizar_competidor", {})
    assert r["portafolio_evaluado"]["peor_caso"] == pytest.approx(HECHOS["P07"]["peor_caso"])
    assert r["portafolio_evaluado"]["rival_ataca"] == HECHOS["P07"]["rival_ataca"]
    r = ejecutar_herramienta("desempatar_portafolios", {"criterio": "peor_caso"})
    assert r["ganador"] == HECHOS["P15"]["ganador"]


def test_juego_caso_c():
    r = ejecutar_herramienta("juego_producto", {"producto": "Jugo", "erosion": 0.5,
                                               "pago_rival_si_lanzamos": -3e6, "pago_rival_si_no_lanzamos": 18e6})
    assert len(r["equilibrios_nash"]) == 2 and r["si_riovalle_mueve_primero"] == "(Lanzar, No entrar)"


@pytest.mark.parametrize("nombre, argumentos", [
    ("calcular_ruta", {"ruta": "Envigado"}),
    ("calcular_ruta", {"cambios_memoria": {"Cliente Fantasma": {"queja_urgente": True}}}),
    ("calcular_ruta", {"cambios_memoria": {"Redetrans": {"valor_factura_pedido": 0}}}),
    ("optimizar_portafolio", {"excluir": ["Arepas Riovalle"]}),
    ("juego_producto", {"producto": "Jugo"}),
    ("herramienta_inventada", {}),
])
def test_errores_vuelven_como_mensaje_y_no_como_excepcion(nombre, argumentos):
    assert "error" in ejecutar_herramienta(nombre, argumentos)


def test_las_herramientas_no_modifican_los_datos_originales():
    antes = ejecutar_herramienta("calcular_ruta", {"ruta": "Poblado"})
    ejecutar_herramienta("calcular_ruta", {"cambios_memoria": {"Fruver del Río": {"costo_flete_estimado": 1}},
                                           "umbrales": {"flete_sobre_factura": 0.5}})
    assert ejecutar_herramienta("calcular_ruta", {"ruta": "Poblado"}) == antes


# =============================================================================
# Ciclo del agente con un proveedor falso
# =============================================================================
def _llamada(id_, nombre, argumentos):
    return SimpleNamespace(id=id_, function=SimpleNamespace(name=nombre, arguments=json.dumps(argumentos)))


def _mensaje(texto=None, llamadas=None):
    msg = SimpleNamespace(content=texto, tool_calls=llamadas)
    msg.model_dump = lambda exclude_none=True: {
        "role": "assistant", "content": texto,
        **({"tool_calls": [{"id": l.id, "type": "function",
                            "function": {"name": l.function.name, "arguments": l.function.arguments}}
                           for l in llamadas]} if llamadas else {})}
    return msg


class ProveedorFalso:
    """Imita client.chat.completions.create devolviendo un guion de mensajes."""

    def __init__(self, guion):
        self.guion = list(guion)
        self.recibidos = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))

    def _crear(self, model, messages, tools):
        self.recibidos.append(list(messages))
        uso = SimpleNamespace(prompt_tokens=100, completion_tokens=10)
        return SimpleNamespace(choices=[SimpleNamespace(message=self.guion.pop(0))], usage=uso)


def test_ciclo_ejecuta_herramienta_y_devuelve_texto():
    falso = ProveedorFalso([
        _mensaje(llamadas=[_llamada("c1", "calcular_ruta", {"ruta": "Poblado"})]),
        _mensaje(texto="La ruta Poblado recorre 9,9 km."),
    ])
    r = bucle.responder("¿Cuántos km recorre la ruta Poblado?", falso, "modelo-falso")
    assert r["terminado"] and r["vueltas"] == 2
    assert r["texto"] == "La ruta Poblado recorre 9,9 km."
    assert r["traza"][0]["herramienta"] == "calcular_ruta"
    assert r["traza"][0]["resultado"]["rutas"]["Poblado"]["km_texto"] == "9,9 km"
    # El resultado de la herramienta le llega al modelo en la segunda vuelta
    ultimo = falso.recibidos[1][-1]
    assert ultimo["role"] == "tool" and ultimo["tool_call_id"] == "c1" and "9,9 km" in ultimo["content"]
    assert r["tokens_entrada"] == 200 and r["tokens_salida"] == 20


def test_herramienta_inexistente_no_rompe_el_ciclo():
    falso = ProveedorFalso([
        _mensaje(llamadas=[_llamada("c1", "vender_acciones", {})]),
        _mensaje(texto="No tengo una herramienta para eso."),
    ])
    r = bucle.responder("Vende acciones", falso, "modelo-falso")
    assert r["terminado"] and "error" in r["traza"][0]["resultado"]


def test_tope_de_vueltas():
    falso = ProveedorFalso([_mensaje(llamadas=[_llamada(f"c{i}", "calcular_ruta", {})]) for i in range(10)])
    r = bucle.responder("bucle infinito", falso, "modelo-falso", max_vueltas=3)
    assert not r["terminado"] and r["vueltas"] == 3 and len(r["traza"]) == 3


def test_el_prompt_del_sistema_prohibe_inventar_cifras():
    assert "Nunca calcules ni recuerdes cifras" in bucle.PROMPT_SISTEMA
