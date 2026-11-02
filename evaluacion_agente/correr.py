"""Corre las preguntas de prueba contra un proveedor y califica las respuestas.

Uso:
    python -m evaluacion_agente.correr                        # Gemini, 2 repeticiones
    python -m evaluacion_agente.correr --modelo gemini-3.5-flash --repeticiones 1
    python -m evaluacion_agente.correr --solo P01,P08

Lee la clave de .streamlit/secrets.toml. Escribe en evaluacion_agente/resultados/:
  <modelo>.jsonl      todas las respuestas, trazas y calificaciones
  <modelo>.md         resumen (tabla por pregunta y puntaje total)
  <modelo>_claridad.csv  para que el equipo califique el punto 5 a mano
"""

import argparse
import csv
import json
import time
import tomllib
from pathlib import Path

import openai

from agente.bucle import responder
from agente.proveedor import PROVEEDORES, crear_cliente
from evaluacion_agente.calificar import calificar
from evaluacion_agente.preguntas import construir_preguntas

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = Path(__file__).resolve().parent / "resultados"
PUNTOS = ["herramientas", "argumentos", "cifras", "no_inventa"]


def _clave(proveedor):
    secreto = PROVEEDORES[proveedor]["secreto"]
    if not secreto:
        return None
    return tomllib.load(open(RAIZ / ".streamlit" / "secrets.toml", "rb"))[secreto]


class CuotaDiariaAgotada(Exception):
    """La capa gratuita tiene un tope de solicitudes por día: esperar no sirve."""


def _responder_con_reintentos(pregunta, cliente, modelo, intentos=4):
    for intento in range(intentos):
        try:
            return responder(pregunta, cliente, modelo)
        except openai.RateLimitError as error:
            if "per day" in str(error):
                raise CuotaDiariaAgotada(str(error)) from error
            espera = 30 * (intento + 1)
            print(f"   límite de la capa gratuita: espero {espera}s…", flush=True)
            time.sleep(espera)
        except openai.APIError as error:
            if intento == intentos - 1:
                return {"texto": f"[ERROR] {type(error).__name__}: {error}", "traza": [], "vueltas": 0,
                        "tokens_entrada": 0, "tokens_salida": 0, "terminado": False}
            time.sleep(10)
    return {"texto": "[ERROR] límite de la capa gratuita", "traza": [], "vueltas": 0,
            "tokens_entrada": 0, "tokens_salida": 0, "terminado": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proveedor", default="gemini", choices=list(PROVEEDORES))
    parser.add_argument("--modelo", default=None)
    parser.add_argument("--repeticiones", type=int, default=2)
    parser.add_argument("--pausa", type=float, default=4.0, help="segundos entre preguntas (cuidar la cuota)")
    parser.add_argument("--solo", default=None, help="IDs separados por coma")
    args = parser.parse_args()

    modelo = args.modelo or PROVEEDORES[args.proveedor]["modelo"]
    cliente = crear_cliente(_clave(args.proveedor), args.proveedor)
    preguntas = construir_preguntas()
    if args.solo:
        ids = set(args.solo.split(","))
        preguntas = [p for p in preguntas if p["id"] in ids]

    CARPETA.mkdir(exist_ok=True)
    filas = []
    with open(CARPETA / f"{modelo}.jsonl", "w", encoding="utf-8") as salida:
        for p in preguntas:
            for rep in range(1, args.repeticiones + 1):
                inicio = time.time()
                try:
                    r = _responder_con_reintentos(p["pregunta"], cliente, modelo)
                except CuotaDiariaAgotada:
                    print(f"\nSe agotó la cuota DIARIA de {modelo} en {p['id']}. Se guarda lo que alcanzó a correr; "
                          f"sigue mañana con --solo o usa otro --modelo.", flush=True)
                    break
                segundos = time.time() - inicio
                nota = calificar(p, r)
                fila = {"id": p["id"], "categoria": p["categoria"], "repeticion": rep, "pregunta": p["pregunta"],
                        "respuesta": r["texto"], "traza": r["traza"], "segundos": round(segundos, 1),
                        "tokens_entrada": r["tokens_entrada"], "tokens_salida": r["tokens_salida"],
                        **{k: nota[k] for k in PUNTOS}, "detalle": nota["detalle"]}
                salida.write(json.dumps(fila, ensure_ascii=False, default=float) + "\n")
                salida.flush()  # guarda cada respuesta apenas llega, por si la corrida se interrumpe
                filas.append(fila)
                marca = "".join("✓" if fila[k] else "✗" for k in PUNTOS)
                print(f"{p['id']}#{rep} {marca} {segundos:5.1f}s  {nota['detalle']['llamadas']}"
                      + (f"  INVENTÓ {nota['detalle']['numeros_inventados']}" if not fila["no_inventa"] else ""),
                      flush=True)
                time.sleep(args.pausa)
            else:
                continue
            break  # cuota diaria agotada

    # Resumen
    total = len(filas)
    puntos = {k: sum(f[k] for f in filas) for k in PUNTOS}
    porcentaje = sum(puntos.values()) / (4 * total) * 100 if total else 0
    lineas = [f"# Evaluación del agente · {modelo}", "",
              f"- Respuestas: {total} ({len(preguntas)} preguntas × {args.repeticiones})",
              *[f"- {k}: {v}/{total}" for k, v in puntos.items()],
              f"- **Puntaje automático (puntos 1–4): {porcentaje:.1f} %**",
              f"- **Respuestas con cifras inventadas: {total - puntos['no_inventa']}**",
              f"- Tiempo medio: {sum(f['segundos'] for f in filas) / max(total, 1):.1f} s · "
              f"tokens medios: {sum(f['tokens_entrada'] + f['tokens_salida'] for f in filas) // max(total, 1)}",
              "", "| ID | Rep | Herr. | Arg. | Cifras | No inventa | Detalle |", "|---|---|---|---|---|---|---|"]
    for f in filas:
        d = f["detalle"]
        nota_detalle = "; ".join(x for x in [
            f"faltan args {d['argumentos_faltantes']}" if d["argumentos_faltantes"] else "",
            f"faltan cifras {d['cifras_faltantes']}" if d["cifras_faltantes"] else "",
            f"faltan nombres {d['nombres_faltantes']}" if d["nombres_faltantes"] else "",
            f"inventó {d['numeros_inventados']}" if d["numeros_inventados"] else ""] if x)
        lineas.append(f"| {f['id']} | {f['repeticion']} | {'✓' if f['herramientas'] else '✗'} | "
                      f"{'✓' if f['argumentos'] else '✗'} | {'✓' if f['cifras'] else '✗'} | "
                      f"{'✓' if f['no_inventa'] else '✗'} | {nota_detalle} |")
    (CARPETA / f"{modelo}.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    with open(CARPETA / f"{modelo}_claridad.csv", "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["id", "repeticion", "pregunta", "respuesta", "claridad (0/1)", "comentario"])
        for fila in filas:
            escritor.writerow([fila["id"], fila["repeticion"], fila["pregunta"], fila["respuesta"], "", ""])

    print(f"\nPuntaje automático: {porcentaje:.1f} % · cifras inventadas en {total - puntos['no_inventa']} respuestas")
    print(f"Resumen: {CARPETA / (modelo + '.md')}")


if __name__ == "__main__":
    main()
