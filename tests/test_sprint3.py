"""Paridad Sprint 3A y 3B (SPEC §8): algoritmo genético, Minimax y teoría de juegos."""

import pytest

from megamarket import competidor, genetico
from megamarket.datos import CANDIDATOS

HIGO, MIX, BARRA, GRANOLA, JUGO, SNACK, COMPOTA, CAFE = list(CANDIDATOS)


def portafolio(*productos):
    return tuple(1 if n in productos else 0 for n in CANDIDATOS)


# =============================================================================
# Sprint 3A — AG de portafolio (semilla 42, población 10, 15 generaciones)
# =============================================================================
def test_ag_3a_semilla_42():
    mejor, historial = genetico.ejecutar_experimento()
    assert genetico.nombre_incluidos(mejor) == [HIGO, JUGO, CAFE]
    assert genetico.costo_total(mejor) == 70_000_000
    assert genetico.espacio_total(mejor) == 22
    assert genetico.utilidad_total(mejor) == 122_000_000
    # Evolución completa, tal como sale del notebook
    assert list(historial["Mejor utilidad"]) == [118_000_000] + [122_000_000] * 15
    assert list(historial["Diversidad"]) == [9, 7, 6, 6, 4, 3, 1, 1, 1, 1, 1, 3, 3, 4, 4, 4]
    assert list(historial["Utilidad promedio"]) == [
        78_400_000, 89_800_000, 101_200_000, 93_800_000, 89_400_000, 102_600_000,
        122_000_000, 122_000_000, 122_000_000, 122_000_000, 122_000_000,
        114_000_000, 117_800_000, 111_200_000, 109_000_000, 115_800_000,
    ]


def test_fuerza_bruta_3a():
    fb = genetico.validar_con_fuerza_bruta()
    assert fb["mejor_utilidad_fb"] == 122_000_000
    assert len(fb["validas"]) == 111
    # El notebook se queda con el primero que encuentra
    assert fb["mejor_fuerza_bruta"] == portafolio(MIX, BARRA, JUGO)
    assert set(fb["optimos"]) == {portafolio(HIGO, JUGO, CAFE), portafolio(MIX, BARRA, JUGO)}


def test_reparacion_de_lanzar_los_8():
    reparado = genetico.reparar_portafolio(tuple([1] * 8))
    assert genetico.nombre_incluidos(reparado) == [HIGO, MIX]
    assert genetico.es_portafolio_valido(reparado)


def test_parametros_explicitos_iguales_a_los_por_defecto():
    con_defecto = genetico.ejecutar_experimento()
    explicito = genetico.ejecutar_experimento(
        candidatos=dict(CANDIDATOS), presupuesto=70_000_000, espacio=25
    )
    assert con_defecto[0] == explicito[0]
    assert con_defecto[1].equals(explicito[1])


def test_candidatos_editados_cambian_el_resultado():
    candidatos = {n: dict(d) for n, d in CANDIDATOS.items()}
    del candidatos[JUGO]
    mejor, _ = genetico.ejecutar_experimento(candidatos=candidatos)
    assert len(mejor) == 7
    assert genetico.es_portafolio_valido(mejor, candidatos)
    assert JUGO not in genetico.nombre_incluidos(mejor, candidatos)


# =============================================================================
# Sprint 3B — Juego 2x2 del Jugo Natural
# =============================================================================
def test_caso_a():
    caso = competidor.mostrar_caso(*competidor.CASOS_JUGO["A"])
    assert caso["nash"] == [(0, 0)]                      # (Lanzar, Entrar)
    assert caso["secuencial"] == (0, 0)
    assert round(caso["pago_riovalle"] / 1e6, 1) == 3.8
    assert caso["pago_rival"] == 6e6


def test_caso_b():
    caso = competidor.mostrar_caso(*competidor.CASOS_JUGO["B"])
    assert caso["nash"] == [(1, 0)]                      # (No lanzar, Entrar)
    assert caso["secuencial"] == (1, 0)
    assert caso["pago_riovalle"] == 0.0


def test_caso_c():
    caso = competidor.mostrar_caso(*competidor.CASOS_JUGO["C"])
    assert caso["nash"] == [(0, 1), (1, 0)]              # dos equilibrios
    assert caso["secuencial"] == (0, 1)                  # (Lanzar, No entrar)
    assert round(caso["pago_riovalle"] / 1e6, 1) == 22.0


def test_erosion_de_equilibrio():
    assert round(competidor.erosion_de_equilibrio(HIGO), 3) == 0.438
    assert round(competidor.erosion_de_equilibrio(JUGO), 3) == 0.423
    assert round(competidor.erosion_de_equilibrio(CAFE), 3) == 0.421


# =============================================================================
# Sprint 3B — Minimax y AG con criterio configurable (semilla 42, población 30, 40 generaciones)
# =============================================================================
def test_arbol_minimax_portafolio_sprint3():
    arbol = competidor.mostrar_arbol(competidor.PORTAFOLIO_SPRINT3, "Portafolio del Sprint 3")
    assert arbol["utilidad_esperada"] == 122_000_000
    assert arbol["rival_ataca"] == "Jugo Natural"
    assert arbol["valor_minimax"] == pytest.approx(90_800_000)
    assert [(p, round(v / 1e6, 1)) for p, v in arbol["ataques"]] == [
        ("Jugo Natural", 90.8), ("Café Molido", 103.0), ("Higo Deshidratado", 112.4),
    ]


def test_ag_esperada_3b():
    mejor, _ = competidor.ejecutar_ag("esperada")
    assert mejor == portafolio(HIGO, JUGO, CAFE)


def test_ag_minimax_3b():
    mejor, historial = competidor.ejecutar_ag("peor_caso")
    assert mejor == portafolio(HIGO, MIX, BARRA, SNACK)
    assert competidor.utilidad_total(mejor) == 119_000_000
    assert competidor.espacio_total(mejor) == 23
    assert competidor.utilidad_peor_caso(mejor) == pytest.approx(95_000_000)
    assert len(historial) == 41


def test_fuerza_bruta_3b():
    opt_esp, optimos_esp, validas = competidor.fuerza_bruta(competidor.utilidad_total)
    assert opt_esp == 122_000_000
    assert len(validas) == 111
    assert set(optimos_esp) == {portafolio(HIGO, JUGO, CAFE), portafolio(MIX, BARRA, JUGO)}

    opt_mm, optimos_mm, _ = competidor.fuerza_bruta(competidor.utilidad_peor_caso)
    assert opt_mm == pytest.approx(95_000_000)
    assert set(optimos_mm) == {portafolio(HIGO, MIX, BARRA, SNACK), portafolio(HIGO, GRANOLA, COMPOTA, CAFE)}
    assert competidor.utilidad_total(portafolio(HIGO, GRANOLA, COMPOTA, CAFE)) == 114_000_000


def test_robustez_20_semillas():
    assert competidor.analisis_robustez() == {"esperada": 19, "peor_caso": 19}


def test_sensibilidad():
    filas = competidor.analisis_sensibilidad()
    tabla = {(f["Ataques del rival"], f["Factor de erosión"]): (round(f["Peor caso"] / 1e6, 2),
                                                                 round(f["Peor caso del portafolio Sprint 3"] / 1e6, 2))
             for f in filas}
    assert tabla == {
        (1, 0.5): (107.0, 106.4), (1, 0.75): (101.0, 98.6), (1, 1.0): (95.0, 90.8),
        (1, 1.25): (90.25, 83.0), (1, 1.5): (85.5, 75.2),
        (2, 0.5): (102.2, 96.9), (2, 0.75): (93.8, 84.35), (2, 1.0): (85.4, 71.8),
        (2, 1.25): (77.0, 59.25), (2, 1.5): (68.6, 46.7),
    }
    assert filas[2]["Portafolio óptimo"] == (
        "Higo Deshidratado, Granola, Compota, Café Molido | "
        "Higo Deshidratado, Mix de Frutos Secos, Barra Energética, Snack de Plátano"
    )


def test_erosion_editada_llega_al_ag():
    sin_erosion = {n: 0.0 for n in CANDIDATOS}
    mejor, _ = competidor.ejecutar_ag("peor_caso", erosion=sin_erosion)
    # Sin erosión el peor caso es la utilidad esperada: el óptimo vuelve a ser $122M
    assert competidor.utilidad_total(mejor) == 122_000_000
