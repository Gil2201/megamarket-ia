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
