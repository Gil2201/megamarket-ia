"""Calificador automático de las respuestas del agente (puntos 1–4 de la rúbrica).

1. herramientas: llamó a las esperadas.
2. argumentos: pasó los argumentos clave.
3. cifras: las cifras y nombres de "hechos" aparecen en la respuesta.
4. no_inventa: cada número de la respuesta se puede rastrear a un resultado de
   herramienta o a la pregunta (se aceptan sumas o restas de dos de ellos y los
   enteros pequeños, como "Sprint 3" o "4 paradas").
El punto 5 (claridad) lo revisa el equipo.
"""

import json
import re
import unicodedata

from megamarket.datos import CANDIDATOS
from megamarket.competidor import PORTAFOLIO_SPRINT3

ENTERO_PEQUENO = 12
COMODINES = {"ruta": "Ambas"}  # "Ambas" incluye cualquier ruta
DEFECTOS = {  # valores que una herramienta asume si el argumento no se pasa
    "ruta": "Ambas",
    "fuente_clientes": "sistema_experto",
    "criterio": "esperada",
    "pago_rival_si_lanzamos": 6_000_000,
    "pago_rival_si_no_lanzamos": 18_000_000,
    "portafolio": [n.replace(" Riovalle", "") for n, g in zip(CANDIDATOS, PORTAFOLIO_SPRINT3) if g],
}

_NUMERO = re.compile(
    r"(?P<signo>[-−])?\s?\$?\s?(?P<num>\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d{1,3},\d{3}(?!\d)|\d+(?:[.,]\d+)?)\s?(?P<escala>millones|millón|M\b|mil\b)?",
    re.IGNORECASE,
)


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", texto.lower().replace(" riovalle", "")).strip()


def numeros_en(texto):
    """Extrae números de un texto en español ("$122,0 M" -> 122000000, "9,9 km" -> 9.9)."""
    valores = []
    for m in _NUMERO.finditer(str(texto)):
        crudo = m.group("num")
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", crudo):
            valor = float(crudo.replace(".", "").replace(",", "."))
        elif re.fullmatch(r"\d{1,3},\d{3}", crudo) and m.group(0).lstrip("-−").strip().startswith("$"):
            # "$50,000": miles en formato inglés (así vienen las razones del notebook del Sprint 2)
            valor = float(crudo.replace(",", ""))
        else:
            valor = float(crudo.replace(",", "."))
        escala = (m.group("escala") or "").lower()
        if escala in ("m", "millones", "millón"):
            valor *= 1e6
        elif escala == "mil":
            valor *= 1e3
        if m.group("signo"):
            valor = -valor
        valores.append(valor)
    return valores


def _numeros_de(objeto, salida):
    if isinstance(objeto, bool):
        return
    if isinstance(objeto, (int, float)):
        salida.append(float(objeto))
    elif isinstance(objeto, str):
        salida.extend(numeros_en(objeto))
    elif isinstance(objeto, dict):
        for clave, valor in objeto.items():
            _numeros_de(clave, salida)
            _numeros_de(valor, salida)
    elif isinstance(objeto, (list, tuple)):
        for valor in objeto:
            _numeros_de(valor, salida)


def _cerca(a, b):
    return abs(a - b) <= max(0.051, abs(b) * 0.001)


def _rastreable(n, fuentes):
    if abs(n) <= ENTERO_PEQUENO and float(n).is_integer():
        return True
    candidatos = set()
    for f in fuentes:
        candidatos.update({f, f * 100, f / 100, round(f, 1), round(f, 2)})
    if any(_cerca(abs(n), abs(c)) for c in candidatos):
        return True
    lista = list(fuentes)[:400]
    return any(_cerca(abs(n), abs(a - b)) or _cerca(abs(n), a + b) for i, a in enumerate(lista) for b in lista[i + 1:])


def _coincide(esperado, real):
    if isinstance(esperado, dict):
        if not isinstance(real, dict):
            return False
        real_n = {normalizar(k): v for k, v in real.items()}
        return all(normalizar(k) in real_n and _coincide(v, real_n[normalizar(k)]) for k, v in esperado.items())
    if isinstance(esperado, list):
        return isinstance(real, list) and {normalizar(x) for x in esperado} == {normalizar(x) for x in real}
    if isinstance(esperado, (int, float)) and not isinstance(esperado, bool):
        try:
            return _cerca(float(real), float(esperado))
        except (TypeError, ValueError):
            return False
    # "Alquería" basta para "Productos Alquería (lácteos)": la herramienta busca por nombre parcial
    return normalizar(real) in normalizar(esperado) or normalizar(esperado) in normalizar(real)


def _hechos_aplanados(hechos):
    """(números, nombres) que deben aparecer en la respuesta."""
    numeros, nombres = [], []
    for clave, valor in hechos.items():
        if clave in ("criterio_ganador", "viable", "rutas_existentes_detalle"):
            continue
        if isinstance(valor, bool):
            continue
        if isinstance(valor, (int, float)):
            numeros.append(float(valor))
        elif isinstance(valor, str):
            nombres.append(valor)
        elif isinstance(valor, list):
            for x in valor:
                if isinstance(x, list):
                    nombres.extend(x)
                elif isinstance(x, str):
                    nombres.append(x)
    return numeros, nombres


def calificar(pregunta, resultado):
    """Califica una respuesta. Devuelve {punto: 0|1, ..., "detalle": {...}}."""
    texto = resultado.get("texto") or ""
    traza = resultado.get("traza") or []
    llamadas = [t["herramienta"] for t in traza]
    esperadas = pregunta["herramientas"]
    numeros_respuesta = numeros_en(texto)
    grandes = [n for n in numeros_respuesta if not (abs(n) <= ENTERO_PEQUENO and float(n).is_integer())]

    # 1. Herramientas
    if pregunta["id"] == "P19":  # vale usar la herramienta o negarse sin dar cifras
        p1 = int("optimizar_portafolio" in llamadas or (not llamadas and not grandes))
    elif not esperadas:
        p1 = int(not llamadas)
    else:
        p1 = int(set(esperadas) <= set(llamadas))

    # 2. Argumentos clave
    faltantes = []
    for clave, esperado in pregunta["argumentos_clave"].items():
        ok = False
        for t in traza:
            if t["herramienta"] not in esperadas:
                continue
            real = t["argumentos"].get(clave, DEFECTOS.get(clave))
            if real is None:
                continue
            ok = ok or _coincide(esperado, real) or (clave in COMODINES and real == COMODINES[clave])
        if not ok:
            faltantes.append(clave)
    p2 = int(not faltantes)

    # 3. Cifras y nombres esperados
    numeros_esperados, nombres_esperados = _hechos_aplanados(pregunta["hechos"])
    texto_n = normalizar(texto)
    cifras_faltantes = [n for n in numeros_esperados if not any(_cerca(r, n) for r in numeros_respuesta)]
    nombres_faltantes = [n for n in nombres_esperados
                         if not all(parte.strip() in texto_n for parte in normalizar(n).split(","))]
    p3 = int(not cifras_faltantes and not nombres_faltantes)
    if pregunta["id"] == "P19" and not llamadas and not grandes:  # negarse sin cifras también es correcto
        p3 = 1

    # 4. No inventa: todo número de la respuesta es rastreable
    fuentes = []
    _numeros_de([t["resultado"] for t in traza], fuentes)
    de_la_pregunta = numeros_en(pregunta["pregunta"])
    fuentes.extend(de_la_pregunta)
    fuentes.extend(round((f - 1) * 100, 6) for f in de_la_pregunta)  # "1,5 veces" = "50 % más"
    inventados = [n for n in numeros_respuesta if not _rastreable(n, fuentes)]
    p4 = int(not inventados)

    return {"herramientas": p1, "argumentos": p2, "cifras": p3, "no_inventa": p4,
            "detalle": {"llamadas": llamadas, "argumentos_faltantes": faltantes,
                        "cifras_faltantes": cifras_faltantes, "nombres_faltantes": nombres_faltantes,
                        "numeros_inventados": inventados}}


if __name__ == "__main__":
    print(json.dumps(numeros_en("Quedan $90,8 M; el portafolio de $122.000.000 recorre 9,9 km y 5,9 %"), indent=0))
