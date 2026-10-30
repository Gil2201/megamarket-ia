# Sprint 4 — Decisiones tomadas (propuesta para validar con el profesor)

> Cierra la sección 6 de `SPRINT4_LOGICA_DIFUSA.md`. Las decisiones 1, 2 y 6 siguen la recomendación
> de ese documento; los cortes, las reglas y los datos (3, 4 y 5) son una **propuesta** escrita con
> criterio de negocio y anclada a los umbrales del Sprint 2. El equipo puede cambiarlos editando
> `megamarket/difuso.py` y `data/memoria_trabajo_portafolio_difusa.csv`; las pruebas
> (`tests/test_sprint4.py`) dirán si algo deja de ser coherente.

## 1. Alcance
**4A y 4B, con 4A primero.** La nota de viabilidad de 4A es una de las entradas del desempate de 4B.

## 2. Opción para 4A
**Opción A: jerarquía de 5 sistemas, 45 reglas, 6 criterios.** C2 (registro sanitario) sigue siendo un
filtro duro de lógica clásica: si es No, el producto es "No viable" sin pasar por el sistema difuso.

```
margen ──────────┐
                 ├─► [S1] Atractivo comercial ─┐
complementar. ───┘                             ├─► [S4] Fortaleza del negocio ─┐
vida útil ───────┐                             │                               ├─► [S5] NOTA DE VIABILIDAD
                 ├─► [S2] Solidez operativa ───┘                               │
facilidad op. ───┘                                                             │
afinidad ────────┐                                                             │
                 ├─► [S3] Encaje con la marca ─────────────────────────────────┘
calidad ─────────┘
```

## 3. Funciones de pertenencia

Todas las variables del Sprint 4 son **particiones**: las pertenencias de etiquetas vecinas suman 1.

| Variable | Universo | Etiqueta 1 | Etiqueta 2 | Etiqueta 3 |
|---|---|---|---|---|
| `margen_pct` (C7) | 0–40 % | bajo: trap 0-0-6-18 | medio: tri 6-18-30 | alto: trap 18-30-40-40 |
| `vida_util_meses` (C6) | 0–24 meses | corta: trap 0-0-3-9 | media: tri 3-9-15 | larga: trap 9-15-24-24 |
| `complementariedad`, `facilidad_operativa`, `afinidad`, `calidad_presentacion` | 0–10 | baja: trap 0-0-2-5 | media: tri 2-5-8 | alta: trap 5-8-10-10 |
| Salidas intermedias, nota final, nota promedio y preferencia | 0–100 | baja: trap 0-0-25-50 | media: tri 25-50-75 | alta: trap 50-75-100-100 |
| `exposicion_competidor` (4B) | 0–100 % | baja: trap 0-0-30-45 | media: tri 30-45-60 | alta: trap 45-60-100-100 |

- **Anclaje a los umbrales del Sprint 2:** el margen mínimo de 12 % y la vida útil mínima de 6 meses
  caen **justo en el cruce** (pertenencia 0,5 a cada etiqueta vecina): la frontera dura de antes es
  ahora el punto de máxima ambigüedad.
- **Por qué particiones:** una primera versión usaba los cortes de la urgencia de clase para las
  escalas 0–10 (baja 0-0-2-4, media 2-5-8), que no suman 1 en el cruce. Con ellos, **subir** la
  complementariedad podía **bajar** la nota hasta 4,4 puntos. Con particiones la peor caída es 1,3
  puntos, el ruido propio del método (§8).
- La exposición se calibró al rango real de la erosión (20 %–60 %): una escala 0–100 genérica
  dejaría todos los portafolios en "media".
- El ejemplo de clase (Mercado Libre) conserva sus cortes originales: es la prueba de paridad.

## 4. Tablas de reglas (filas = primera entrada, columnas = segunda)

**S1 · Atractivo comercial** = margen × complementariedad. *El margen domina: un margen bajo arrastra
a "baja" aunque la complementariedad sea alta, pero no al revés.*

| margen \ complementariedad | baja | media | alta |
|---|---|---|---|
| bajo | baja | baja | baja |
| medio | baja | media | alta |
| alto | media | alta | alta |

**S2 · Solidez operativa** = vida útil × facilidad operativa. *La vida útil domina (por eso Alquería sale baja).*

| vida útil \ facilidad | baja | media | alta |
|---|---|---|---|
| corta | baja | baja | baja |
| media | baja | media | alta |
| larga | media | alta | alta |

**S3 · Encaje con la marca** = afinidad × calidad. *La afinidad domina: un producto ajeno al
portafolio no encaja con la marca por buena que sea su presentación (por eso Aseo sale baja).*

| afinidad \ calidad | baja | media | alta |
|---|---|---|---|
| baja | baja | baja | baja |
| media | baja | media | alta |
| alta | media | alta | alta |

**S4 · Fortaleza del negocio** = atractivo comercial × solidez operativa. *Eslabón más débil: el
negocio no es fuerte si falla lo comercial O lo operativo.* Una primera versión simétrica dejaba a
Alquería con nota 83,7 (lo comercial compensaba la vida útil corta); se descartó por incoherente con
el Sprint 2.

| atractivo \ solidez | baja | media | alta |
|---|---|---|---|
| baja | baja | baja | baja |
| media | baja | media | media |
| alta | baja | media | alta |

**S5 · Nota de viabilidad** = fortaleza del negocio × encaje con la marca. *La fortaleza manda: si es
baja, la nota es baja para cualquier encaje; el encaje solo sube o baja un nivel.*

| fortaleza \ encaje | baja | media | alta |
|---|---|---|---|
| baja | baja | baja | baja |
| media | baja | media | alta |
| alta | media | alta | alta |

**4B · Preferencia** = nota promedio × exposición al competidor. *Se prefiere nota alta y exposición baja.*

| nota \ exposición | baja | media | alta |
|---|---|---|---|
| baja | media | baja | baja |
| media | alta | media | baja |
| alta | alta | alta | media |

## 5. Datos numéricos (ilustrativos)
`data/memoria_trabajo_portafolio_difusa.csv`: las 3 categorías del Sprint 2 y las 8 referencias
Riovalle del Sprint 3. Coherentes con el Sprint 2:
- **Aseo:** afinidad baja (C1 = No) y facilidad operativa baja (C3 = No).
- **Alquería:** vida útil corta (C6 = No).
- **Bebidas:** alta en todo.
- **Referencias Riovalle:** todas cumplen los umbrales (margen ≥ 12 %, vida útil ≥ 6 meses) porque se
  suponen ya filtradas; difieren en qué tan bien los cumplen. Ninguna sale "baja".

**Resultado:** Bebidas 80,6 (alta) · Alquería 19,4 (baja) · Aseo 21,8 (baja). Referencias Riovalle:
Higo 80,6 · Mix 80,6 · Café 80,2 · Granola 79,0 · Compota 74,6 · Barra 71,8 · Snack 52,7 (media) ·
Jugo 47,8 (media: lo bajan su vida útil corta y su manejo refrigerado).

## 6. Tolerancia y umbral de empate (4B)
- **Tolerancia** para considerar empatados dos portafolios: por defecto **0 %** (solo empates exactos,
  como en las páginas 4 y 5), configurable hasta 5 %. A 2 % solo están los dos empates exactos.
- **Umbral de preferencia:** si dos portafolios quedan a menos de **1,5 puntos** de preferencia, se
  consideran empatados y gana el de **mayor holgura de bodega**; si siguen iguales, el orden de la
  fuerza bruta. El documento de diseño proponía 0,5 puntos; se subió a 1,5 porque es el tamaño del
  ruido propio del método (§8): una diferencia menor no significa nada.

**Resultado con los datos actuales:**
- Empate de $122 M: gana **{Higo, Jugo, Café}** por preferencia difusa (60,4 vs. 52,6). Las dos tienen
  la misma utilidad, costo, espacio y peor caso; la diferencia está en la exposición (49,0 % vs. 52,5 %).
- Empate Minimax de $95 M: las preferencias quedan a 0,6 puntos (78,8 vs. 78,2), así que gana
  **{Higo, Granola, Compota, Café}** por holgura de bodega (3 vs. 2 posiciones). Es también el que
  tiene mejor nota (79,3 vs. 75,0) y menor exposición (38,1 % vs. 39,9 %). El notebook 3B, con su
  desempate de 0,001 × utilidad, elegía el otro.

## 7. Ponderación del desempate
- `nota_promedio` = Σ(nota × utilidad) / Σ utilidad de los productos del portafolio.
- `exposicion_competidor` = Σ(utilidad × erosión) / Σ utilidad × 100.

## 8. Límite conocido: monotonía
Mamdani con recorte por mínimo y defuzzificación por centroide (el método de clase) **no es
estrictamente monótono**. Cuando varias celdas vecinas de una tabla dan la misma salida, la activación
de esa salida es el máximo de pertenencias que se cruzan, y ese máximo baja un poco en el cruce. Al
moverse, el centro de gravedad se corre aunque la información no haya cambiado. El sistema de clase
tiene el mismo efecto: subir la reputación de 40 a 40,25 baja la prioridad 0,19 puntos con urgencia 2,5.

Con los cortes de §3 la peor caída de la nota al subir un criterio es 1,3 puntos de 100. Las pruebas
exigen **monotonía práctica**: ninguna caída mayor a 1,5 puntos y nunca terminar por debajo del punto
de partida. No se cambia el método, para conservar el visto en clase.
