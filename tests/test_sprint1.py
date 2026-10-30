"""Paridad Sprint 1 (SPEC §8): A* + vecino más cercano con todos los clientes."""

import pytest

from megamarket.busqueda import (
    REDES,
    a_estrella,
    a_estrella_con_traza,
    heuristica,
    recorrido_completo,
    red_poblado,
    red_valle_aburra,
)
from megamarket.datos import BODEGA, PLATAFORMA, clientes_poblado, clientes_valle_aburra


def test_ruta_poblado_todos_los_clientes():
    paradas, distancia, orden = recorrido_completo(
        red_poblado, BODEGA, clientes_poblado, destino_final=PLATAFORMA
    )
    assert round(distancia, 1) == 16.8
    assert orden == [
        "EAFIT La Bodeguita", "Hotel Four Points", "Supermercado Merka 10", "Five Sisters",
        "Redetrans", "Mercados Verona", "Fruver Visitación", "Fruver del Río",
    ]
    assert paradas == [
        "Bodega Olaya Herrera", "Acceso Poblado (Aguacatala)", "EAFIT La Bodeguita",
        "Hotel Four Points", "Supermercado Merka 10", "Five Sisters", "Redetrans",
        "Mercados Verona", "Fruver Visitación", "Acceso Poblado (Aguacatala)",
        "Fruver del Río", "Acceso Poblado (Aguacatala)", "Plataforma Logística",
    ]


def test_ruta_valle_aburra_todos_los_clientes():
    paradas, distancia, orden = recorrido_completo(
        red_valle_aburra, BODEGA, clientes_valle_aburra, destino_final=PLATAFORMA
    )
    assert round(distancia, 1) == 18.0
    assert orden == ["CEDI Vaquita Itagüí", "CEDI Merkepaisa", "CEDI Supermú", "CEDI Euro La Estrella"]
    assert paradas == [
        "Bodega Olaya Herrera", "Acceso Sur (Itagüí Centro)", "CEDI Vaquita Itagüí",
        "Acceso Sur (Itagüí Centro)", "CEDI Merkepaisa", "CEDI Supermú",
        "CEDI Euro La Estrella", "Acceso Sur (Itagüí Centro)", "Plataforma Logística",
    ]


def test_recorrido_no_modifica_la_lista_de_clientes():
    clientes = list(clientes_poblado)
    recorrido_completo(red_poblado, BODEGA, clientes, destino_final=PLATAFORMA)
    assert clientes == clientes_poblado


def test_sin_destino_final_regresa_al_origen():
    paradas, _, _ = recorrido_completo(red_valle_aburra, BODEGA, ["CEDI Supermú"])
    assert paradas[-1] == BODEGA


def test_heuristica_es_simetrica_y_cero_en_el_mismo_punto():
    assert heuristica(BODEGA, BODEGA) == 0
    assert heuristica(BODEGA, PLATAFORMA) == pytest.approx(heuristica(PLATAFORMA, BODEGA))


@pytest.mark.parametrize("nombre_ruta", ["Poblado", "Valle de Aburrá"])
def test_a_estrella_con_traza_da_lo_mismo_que_a_estrella(nombre_ruta):
    red = REDES[nombre_ruta]
    for origen in red:
        for destino in red:
            camino, costo = a_estrella(red, origen, destino)
            camino_t, costo_t, traza = a_estrella_con_traza(red, origen, destino)
            assert camino_t == camino
            assert costo_t == costo
            assert traza[-1]["accion"] == "destino"
            assert traza[-1]["nodo"] == destino
            for paso in traza:
                assert paso["f"] == pytest.approx(paso["g"] + paso["h"])
