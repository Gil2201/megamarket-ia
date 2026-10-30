"""Paridad Sprint 2 (SPEC §8): sistemas expertos de logística y de portafolio."""

import copy

import pytest

from megamarket.busqueda import REDES, recorrido_completo
from megamarket.datos import BODEGA
from megamarket.sistema_experto_logistica import (
    BASE_CONOCIMIENTO,
    a_booleano,
    construir_memoria_trabajo,
    decidir_clientes_de_la_ruta,
    interpretar_stock_reportado,
    leer_memoria_logistica,
    motor_inferencia,
)
from megamarket.sistema_experto_portafolio import (
    CRITERIOS_DETALLE,
    CRITERIOS_NOMBRES,
    construir_memoria_trabajo_portafolio,
    evaluar_producto,
    leer_memoria_portafolio,
)


@pytest.fixture(scope="module")
def memoria():
    return construir_memoria_trabajo(leer_memoria_logistica())


# (incluir, prioridad, reglas que aparecen en las razones, en orden)
ESPERADO = {
    "Fruver del Río":        (False, None,    ["R1", "R4"]),
    "Fruver Visitación":     (False, None,    ["R6"]),
    "Five Sisters":          (True,  "BAJA",  ["R2"]),
    "Supermercado Merka 10": (True,  "ALTA",  ["R3"]),
    "Hotel Four Points":     (False, None,    ["R6"]),
    "Mercados Verona":       (True,  "MEDIA", ["R1"]),
    "EAFIT La Bodeguita":    (True,  "ALTA",  ["R3"]),
    "Redetrans":             (False, None,    ["R1", "R5"]),
    "CEDI Vaquita Itagüí":   (True,  "ALTA",  ["R1"]),
    "CEDI Euro La Estrella": (False, None,    ["R2", "R4"]),
    "CEDI Merkepaisa":       (False, None,    ["R1", "R4"]),
    "CEDI Supermú":          (True,  "ALTA",  ["R3"]),
}


@pytest.mark.parametrize("cliente", list(ESPERADO))
def test_decision_por_cliente(cliente, memoria):
    incluir, prioridad, reglas = ESPERADO[cliente]
    conclusion = motor_inferencia(cliente, BASE_CONOCIMIENTO, memoria)
    assert conclusion["incluir_en_ruta"] is incluir
    assert conclusion["prioridad"] == prioridad
    assert [r.split(" ")[0] for r in conclusion["razones"]] == reglas


def test_textos_de_razones_como_el_notebook(memoria):
    razones = {c: motor_inferencia(c, BASE_CONOCIMIENTO, memoria)["razones"] for c in ESPERADO}
    assert razones["Fruver del Río"][0] == "R1 - El mercaderista reportó stock bajo en su visita (rotación alta -> prioridad ALTA)"
    assert razones["Fruver del Río"][1] == "R4 (VETO) - El flete ($50,000) es el 5.9% de la factura ($850,000), por encima del 4% permitido"
    assert razones["Five Sisters"] == ["R2 - Sin visita reciente del mercaderista, 18 días sin entrega (> 15), rotación media"]
    assert "5.3%" in razones["CEDI Euro La Estrella"][1]
    assert "5.6%" in razones["CEDI Merkepaisa"][1]


@pytest.mark.parametrize("nombre_ruta, km, orden", [
    ("Poblado", 9.9, ["EAFIT La Bodeguita", "Supermercado Merka 10", "Mercados Verona", "Five Sisters"]),
    ("Valle de Aburrá", 14.9, ["CEDI Vaquita Itagüí", "CEDI Supermú"]),
])
def test_sistema_experto_mas_a_estrella(nombre_ruta, km, orden, memoria):
    incluidos, prioridad, traza = decidir_clientes_de_la_ruta(nombre_ruta, BASE_CONOCIMIENTO, memoria)
    assert len(traza) == (8 if nombre_ruta == "Poblado" else 4)
    paradas, distancia, orden_clientes = recorrido_completo(
        REDES[nombre_ruta], BODEGA, incluidos,
        destino_final=BASE_CONOCIMIENTO["destino_final"], prioridad=prioridad,
    )
    assert round(distancia, 1) == km
    assert orden_clientes == orden


def test_ruta_poblado_con_sistema_experto_pasa_por_hotel_sin_entregar(memoria):
    incluidos, prioridad, _ = decidir_clientes_de_la_ruta("Poblado", BASE_CONOCIMIENTO, memoria)
    paradas, _, orden = recorrido_completo(
        REDES["Poblado"], BODEGA, incluidos, destino_final="Plataforma Logística", prioridad=prioridad
    )
    assert "Hotel Four Points" in paradas
    assert "Hotel Four Points" not in orden


def test_umbrales_editables_cambian_la_decision(memoria):
    base = copy.deepcopy(BASE_CONOCIMIENTO)
    base["umbrales"]["flete_sobre_factura"] = 0.06   # con 6 % el flete de Fruver del Río (5,9 %) ya no veta
    assert motor_inferencia("Fruver del Río", base, memoria)["incluir_en_ruta"] is True
    assert BASE_CONOCIMIENTO["umbrales"]["flete_sobre_factura"] == 0.04


def test_lectura_desde_dataframe_da_lo_mismo():
    df = leer_memoria_logistica()
    assert construir_memoria_trabajo(leer_memoria_logistica(df)) == construir_memoria_trabajo(df)


def test_conversores_del_csv():
    assert a_booleano("Sí") and a_booleano(" sí ") and not a_booleano("No")
    assert interpretar_stock_reportado("Sí") is True
    assert interpretar_stock_reportado("No") is False
    assert interpretar_stock_reportado("No hubo visita") is None


def test_sistema_experto_portafolio():
    memoria_p = construir_memoria_trabajo_portafolio(leer_memoria_portafolio())
    resultados = {
        p: evaluar_producto(p, memoria_p, CRITERIOS_NOMBRES, CRITERIOS_DETALLE) for p in memoria_p
    }
    assert resultados["Productos de aseo para el hogar"]["viable"] is False
    assert resultados["Productos de aseo para el hogar"]["incumplidos"] == ["C1", "C3"]
    assert resultados["Productos Alquería (lácteos)"]["viable"] is False
    assert resultados["Productos Alquería (lácteos)"]["incumplidos"] == ["C6"]
    assert resultados["Bebidas"]["viable"] is True
    assert resultados["Bebidas"]["incumplidos"] == []
