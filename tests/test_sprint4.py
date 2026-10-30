"""Pruebas del Sprint 4 (docs/SPRINT4_LOGICA_DIFUSA.md §8): lógica difusa."""

import itertools

import numpy as np
import pytest

from megamarket import competidor, difuso
from megamarket.datos import CANDIDATOS, EROSION

HIGO, MIX, BARRA, GRANOLA, JUGO, SNACK, COMPOTA, CAFE = list(CANDIDATOS)


@pytest.fixture(scope="module")
def productos():
    return difuso.construir_productos_difusos(difuso.leer_memoria_difusa())


@pytest.fixture(scope="module")
def notas(productos):
    return difuso.notas_de_productos(productos)


# =============================================================================
# Paridad con el notebook de clase (Mercado Libre, pedido ML-2048)
# =============================================================================
def test_paridad_con_clase_ml_2048():
    r = difuso.evaluar_sistema(difuso.SISTEMA_CLASE, 65, 7)
    assert r["valor"] == pytest.approx(70.1672721768, abs=1e-6)
    assert r["grados_1"] == pytest.approx({"baja": 0.0, "media": 0.25, "alta": 0.75})
    assert r["grados_2"] == pytest.approx({"baja": 0.0, "media": 1 / 3, "alta": 0.5})


@pytest.mark.parametrize("entradas", [(105, 4), (60, 12), (-1, 5), (float("nan"), 5)])
def test_entradas_fuera_del_universo_se_rechazan(entradas):
    with pytest.raises(ValueError):
        difuso.evaluar_sistema(difuso.SISTEMA_CLASE, *entradas)


def test_funciones_de_pertenencia_validan_parametros():
    with pytest.raises(ValueError):
        difuso.trimf(5, 3, 2, 1)
    with pytest.raises(ValueError):
        difuso.trapmf(5, 0, 3, 2, 4)


# =============================================================================
# Estructura de los sistemas
# =============================================================================
@pytest.mark.parametrize("sistema", list(difuso.SISTEMAS_VIABILIDAD.values()) + [difuso.SISTEMA_DESEMPATE])
def test_cada_tabla_tiene_9_reglas_y_cubre_todas_las_combinaciones(sistema):
    reglas = sistema["reglas"]
    assert len(reglas) == 9
    etiquetas_1 = list(sistema["entrada_1"]["conjuntos"])
    etiquetas_2 = list(sistema["entrada_2"]["conjuntos"])
    assert {(a, b) for a, b, _ in reglas} == set(itertools.product(etiquetas_1, etiquetas_2))
    assert all(s in sistema["salida"]["conjuntos"] for _, _, s in reglas)


@pytest.mark.parametrize("var", [difuso.MARGEN, difuso.VIDA_UTIL, difuso.COMPLEMENTARIEDAD,
                                 difuso.NOTA, difuso.EXPOSICION])
def test_los_conjuntos_cubren_todo_el_universo(var):
    total = sum(var["conjuntos"].values())
    assert np.all(total > 0)


def test_umbrales_del_sprint_2_quedan_justo_en_el_cruce():
    m = {k: difuso.pertenencia_en(12, difuso.margen_u, v) for k, v in difuso.MARGEN["conjuntos"].items()}
    assert m["bajo"] == pytest.approx(0.5) and m["medio"] == pytest.approx(0.5)
    v = {k: difuso.pertenencia_en(6, difuso.vida_util_u, c) for k, c in difuso.VIDA_UTIL["conjuntos"].items()}
    assert v["corta"] == pytest.approx(0.5) and v["media"] == pytest.approx(0.5)


@pytest.mark.parametrize("var", [difuso.MARGEN, difuso.VIDA_UTIL, difuso.COMPLEMENTARIEDAD,
                                 difuso.NOTA, difuso.EXPOSICION])
def test_las_variables_del_sprint_4_son_particiones(var):
    assert np.allclose(sum(var["conjuntos"].values()), 1.0)


# =============================================================================
# 4A — Nota de viabilidad
# =============================================================================
def test_coherencia_con_el_sprint_2(productos):
    bebidas = difuso.nota_viabilidad(productos["Bebidas"])
    alqueria = difuso.nota_viabilidad(productos["Productos Alquería (lácteos)"])
    aseo = difuso.nota_viabilidad(productos["Productos de aseo para el hogar"])
    assert bebidas["etiqueta"] == "alta"
    assert alqueria["etiqueta"] == "baja"
    assert aseo["etiqueta"] == "baja"
    # Lo que hunde a Alquería es la solidez operativa (vida útil corta)
    assert difuso.etiqueta_dominante(alqueria["nodos"]["S2"]["valor"], difuso.SOLIDEZ) == "baja"


def test_referencias_riovalle_no_salen_bajas(notas, productos):
    # Ya pasaron los 7 criterios del Sprint 2: pueden ser "media" o "alta", nunca "baja".
    for nombre, datos in productos.items():
        if datos["tipo"] == "Referencia Riovalle":
            assert difuso.etiqueta_dominante(notas[nombre]) != "baja", nombre


def test_notas_de_referencia(notas):
    assert notas["Bebidas"] == pytest.approx(80.56, abs=0.01)
    assert notas["Productos Alquería (lácteos)"] == pytest.approx(19.44, abs=0.01)
    assert notas["Productos de aseo para el hogar"] == pytest.approx(21.79, abs=0.01)
    assert notas[JUGO] == pytest.approx(47.83, abs=0.01)


BASE = {"C2": True, "margen_pct": 20, "complementariedad": 7, "vida_util_meses": 10,
        "facilidad_operativa": 7, "afinidad": 7, "calidad_presentacion": 7}


def test_producto_perfecto_tiene_nota_alta():
    perfecto = {"C2": True, "margen_pct": 40, "complementariedad": 10, "vida_util_meses": 24,
                "facilidad_operativa": 10, "afinidad": 10, "calidad_presentacion": 10}
    assert difuso.nota_viabilidad(perfecto)["etiqueta"] == "alta"


def test_margen_cero_tiene_nota_baja():
    assert difuso.nota_viabilidad({**BASE, "margen_pct": 0})["etiqueta"] == "baja"


def test_sin_registro_sanitario_no_es_viable_sin_importar_lo_demas():
    perfecto_sin_c2 = {"C2": False, "margen_pct": 40, "complementariedad": 10, "vida_util_meses": 24,
                       "facilidad_operativa": 10, "afinidad": 10, "calidad_presentacion": 10}
    resultado = difuso.nota_viabilidad(perfecto_sin_c2)
    assert resultado["cumple_C2"] is False and resultado["nota"] is None


@pytest.mark.parametrize("criterio, maximo", [
    ("margen_pct", 40), ("complementariedad", 10), ("vida_util_meses", 24),
    ("facilidad_operativa", 10), ("afinidad", 10), ("calidad_presentacion", 10),
])
@pytest.mark.parametrize("base", [
    BASE,
    {**BASE, "margen_pct": 12, "vida_util_meses": 6},
    {**BASE, "complementariedad": 3, "facilidad_operativa": 3, "afinidad": 3, "calidad_presentacion": 3},
])
def test_monotonia_practica_subir_un_criterio_no_baja_la_nota(criterio, maximo, base):
    """Mamdani con recorte por mínimo y centroide NO es estrictamente monótono: al
    apagarse una regla el centro de gravedad se corre un poco. Pasa también con el
    sistema de clase (ver la prueba siguiente). Se exige monotonía práctica: ninguna
    caída mayor a 1,5 puntos de 100, y nunca terminar por debajo de donde se empezó."""
    valores = np.linspace(0, maximo, 81)
    notas = [difuso.nota_viabilidad({**base, criterio: v})["nota"] for v in valores]
    caidas = [a - b for a, b in zip(notas, notas[1:])]
    assert max(caidas) <= 1.5
    assert notas[-1] >= notas[0]


def test_el_sistema_de_clase_tampoco_es_estrictamente_monotono():
    xs = np.linspace(0, 100, 401)
    ys = [difuso.evaluar_sistema(difuso.SISTEMA_CLASE, x, 2.5)["valor"] for x in xs]
    assert any(b < a - 1e-6 for a, b in zip(ys, ys[1:]))


# =============================================================================
# 4B — Desempate
# =============================================================================
def test_desempate_de_los_dos_optimos_de_122m(notas):
    ranking = difuso.desempatar_portafolios([[MIX, BARRA, JUGO], [HIGO, JUGO, CAFE]],
                                            CANDIDATOS, EROSION, notas, 25)
    assert ranking[0]["productos"] == [HIGO, JUGO, CAFE]
    assert ranking[0]["criterio"] == "preferencia difusa"
    # Misma utilidad: la diferencia está en la exposición al competidor (SPRINT4 §3)
    assert ranking[0]["exposicion"] == pytest.approx(59.8 / 122 * 100)
    assert ranking[1]["exposicion"] == pytest.approx(64.0 / 122 * 100)


def test_desempate_minimax_es_reproducible_y_no_depende_del_orden(notas):
    a = difuso.desempatar_portafolios([[HIGO, MIX, BARRA, SNACK], [HIGO, GRANOLA, COMPOTA, CAFE]],
                                      CANDIDATOS, EROSION, notas, 25)
    b = difuso.desempatar_portafolios([[HIGO, GRANOLA, COMPOTA, CAFE], [HIGO, MIX, BARRA, SNACK]],
                                      CANDIDATOS, EROSION, notas, 25)
    # Las preferencias quedan a menos de 1,5 puntos: decide la holgura de bodega (3 vs. 2)
    assert abs(a[0]["preferencia"] - a[1]["preferencia"]) < difuso.DIFERENCIA_MINIMA
    assert a[0]["productos"] == b[0]["productos"] == [HIGO, GRANOLA, COMPOTA, CAFE]
    assert a[0]["criterio"].startswith("holgura")


def test_preferencias_casi_iguales_se_desempatan_por_holgura(notas):
    # El mismo portafolio dos veces: preferencia idéntica, gana el primero (orden).
    ranking = difuso.desempatar_portafolios([[HIGO, JUGO, CAFE], [HIGO, JUGO, CAFE]],
                                            CANDIDATOS, EROSION, notas, 25)
    assert ranking[0]["orden"] == 0
    assert ranking[0]["criterio"].startswith("orden")


def test_tolerancia_cero_da_los_empates_exactos():
    _, _, validas = competidor.fuerza_bruta(competidor.utilidad_total)
    exactos = difuso.empates_con_tolerancia(validas, competidor.utilidad_total, 0.0)
    assert len(exactos) == 2
    al_2 = difuso.empates_con_tolerancia(validas, competidor.utilidad_total, 0.02)
    assert len(al_2) == 2     # SPRINT4 §3: a 2 % solo están los dos exactos
    al_5 = difuso.empates_con_tolerancia(validas, competidor.utilidad_total, 0.05)
    assert len(al_5) > 2
