"""Las respuestas de las preguntas de prueba del agente deben coincidir con el código.

Si cambias la lógica o los datos y esta prueba falla, regenera el JSON con:
    python -m evaluacion_agente.preguntas
y revisa en el diff qué respuestas cambiaron.
"""

import json

from evaluacion_agente import preguntas


def test_json_al_dia_con_el_codigo(tmp_path):
    nuevo = tmp_path / "preguntas.json"
    preguntas.exportar(nuevo)
    assert json.loads(nuevo.read_text(encoding="utf-8")) == json.loads(
        preguntas.RUTA_JSON.read_text(encoding="utf-8")
    ), "preguntas_prueba.json está desactualizado: corre python -m evaluacion_agente.preguntas"


def test_cada_pregunta_usa_herramientas_definidas():
    for p in preguntas.construir_preguntas():
        assert set(p["herramientas"]) <= set(preguntas.HERRAMIENTAS), p["id"]
        assert p["categoria"] in {"directa", "que_pasa_si", "cadena", "explicacion", "fuera_de_alcance"}
        assert p["pregunta"].strip()


def test_respuestas_clave_coinciden_con_spec():
    datos = {p["id"]: p["hechos"] for p in preguntas.construir_preguntas()}
    assert datos["P01"]["km"] == 9.9
    assert datos["P02"]["km"] == 18.0
    assert datos["P04"]["utilidad"] == 122_000_000
    assert datos["P07"]["peor_caso"] == 90_800_000
    assert datos["P15"]["peor_caso"] == 95_000_000


# =============================================================================
# Calificador automático
# =============================================================================
from agente.herramientas import ejecutar_herramienta  # noqa: E402
from evaluacion_agente.calificar import calificar, numeros_en  # noqa: E402


def test_lee_numeros_en_formato_espanol_e_ingles():
    assert numeros_en("$122,0 M · 9,9 km · 5,9 % · $850.000 · 80 millones") == [122e6, 9.9, 5.9, 850000, 80e6]
    assert numeros_en("El flete ($50,000) es el 5.9% de la factura") == [50000, 5.9]


def _pregunta(id_):
    return next(p for p in preguntas.construir_preguntas() if p["id"] == id_)


def test_respuesta_correcta_saca_los_cuatro_puntos():
    traza = [{"herramienta": "calcular_ruta", "argumentos": {"ruta": "Poblado"},
              "resultado": ejecutar_herramienta("calcular_ruta", {"ruta": "Poblado"})}]
    texto = ("Esta semana la ruta Poblado recorre 9,9 km: EAFIT La Bodeguita, Supermercado Merka 10, "
             "Mercados Verona y Five Sisters. Algoritmos: Sistema experto (Sprint 2) y A* (Sprint 1).")
    nota = calificar(_pregunta("P01"), {"texto": texto, "traza": traza})
    assert (nota["herramientas"], nota["argumentos"], nota["cifras"], nota["no_inventa"]) == (1, 1, 1, 1)


def test_cifra_inventada_se_detecta():
    traza = [{"herramienta": "calcular_ruta", "argumentos": {"ruta": "Poblado"},
              "resultado": ejecutar_herramienta("calcular_ruta", {"ruta": "Poblado"})}]
    nota = calificar(_pregunta("P01"), {"texto": "Recorre 9,9 km y gasta 37,5 litros de diésel.", "traza": traza})
    assert nota["no_inventa"] == 0 and 37.5 in nota["detalle"]["numeros_inventados"]


def test_fuera_de_alcance_sin_herramientas_y_sin_cifras():
    nota = calificar(_pregunta("P17"), {"texto": "No tengo datos de ventas reales; las cifras de la app son ilustrativas.",
                                        "traza": []})
    assert nota["herramientas"] == 1 and nota["no_inventa"] == 1
    nota = calificar(_pregunta("P17"), {"texto": "Vendió cerca de $45.000 M.", "traza": []})
    assert nota["no_inventa"] == 0
