# Sprint 4 — Lógica difusa (diseño preliminar)

> Estado: **propuesta para discutir con el equipo y el profesor. No construir hasta que la sección 6 esté cerrada.**
> Cuando se construya, va en `megamarket/difuso.py` (lógica) y en las páginas 3 y 6 de la app.
> Referencia obligatoria: `referencia/clase/09_Logica_Difusa_Mercado_Libre.ipynb`.

## 1. Qué queremos resolver

- **4A — Nota de viabilidad de productos.** Reemplazar el "todas las luces en verde" del SE de portafolio (Sprint 2), donde los 7 criterios valen lo mismo y basta que uno falle para descartar, por una **nota 0–100** que refleje *qué tanto* cumple cada producto, sabiendo que no todos los criterios pesan igual.
- **4B — Desempate de portafolios.** Cuando el AG (Sprint 3) encuentra varios portafolios con la misma utilidad, elegir entre ellos con un criterio difuso en vez de quedarse con el que salió primero.

Las dos se complementan: la nota de 4A es una de las entradas del desempate de 4B. Así el Sprint 4 conecta la cadena de portafolio, que hoy está desconectada (SPEC, sección 3).

## 2. Cómo se hizo en clase (y por qué eso define el diseño)

El notebook de clase (prioridad de despacho en Mercado Libre) implementa **Mamdani a mano con `numpy`**:

| Pieza | Función del notebook |
|---|---|
| Funciones de pertenencia | `trimf(x, a, b, c)`, `trapmf(x, a, b, c, d)` |
| Universos | `np.linspace(0, 100, 1001)` / `np.linspace(0, 10, 1001)` |
| Conjuntos | diccionarios `{"baja": ..., "media": ..., "alta": ...}` |
| Fuzzificación | `pertenencia_en(valor, universo, curva)` (rechaza valores fuera de rango) |
| Reglas | lista de tuplas `(etiqueta_1, etiqueta_2, salida)` — **2 entradas × 3 etiquetas = 9 reglas, tabla completa** |
| Inferencia | `inferencia_mamdani(...)`: Y = mínimo, implicación = recorte, agregación = máximo |
| Defuzzificación | `centroide(universo, curva)` |
| Validación | `assert` con valores conocidos (ML-2048 → 70.1672721768) |

**Consecuencias para el Sprint 4:**
1. No se usa `scikit-fuzzy`. Se reutilizan `trimf`, `trapmf`, `pertenencia_en` y `centroide` **literalmente**.
2. `inferencia_mamdani` se generaliza para recibir los conjuntos y las reglas como parámetros (hoy tiene reputación/urgencia fijos), sin cambiar sus cuatro pasos. **Prueba de paridad:** con los conjuntos y reglas de clase, la versión generalizada debe devolver 70.1672721768 para (65, 7).
3. **Cada sistema difuso tiene 2 entradas y 9 reglas**, como en clase. Es lo que se puede escribir completo, dibujar como tabla 3×3 y defender en la sustentación. Con 6 entradas en un solo sistema habría 3⁶ = 729 combinaciones: imposible de escribir y de defender.
4. Para usar más de 2 criterios se encadenan sistemas de 2 entradas (sistema **jerárquico**): la salida 0–100 de uno es la entrada del siguiente.
5. Las salidas intermedias y finales usan el universo 0–100 con los mismos conjuntos de salida de clase (baja: trap 0-0-20-40, media: tri 25-50-75, alta: trap 60-80-100-100), salvo que el equipo decida otros.

## 3. Hallazgo clave para el desempate (4B)

Los dos portafolios empatados en $122M del Sprint 3 son idénticos en casi todo:

| | {Higo, Jugo, Café} | {Mix, Barra, Jugo} |
|---|---|---|
| Utilidad esperada | $122,0M | $122,0M |
| Costo | $70M | $70M |
| Espacio | 22 / 25 | 22 / 25 |
| N.º de productos | 3 | 3 |
| Peor caso (Minimax) | $90,8M | $90,8M |
| Concentración (producto más grande / total) | 42,6 % | 42,6 % |
| **Exposición total al competidor** (Σ utilidad × erosión) | **$59,8M** | **$64,0M** |

**Consecuencia:** un desempate con las variables que ya usa el AG (utilidad, costo, espacio) **no desempata nada**. 4B necesita información nueva: la exposición al competidor y la nota de viabilidad de 4A. Por eso se construye **4A primero**.

Los empatados en peor caso del Minimax ($95,0M) sí difieren más: {Higo, Mix, Barra, Snack} usa 23 posiciones y deja $119M esperados; {Higo, Granola, Compota, Café} usa 22 y deja $114M. Hoy el notebook 3B desempata con `+ 0.001 × utilidad_total`; el desempate difuso puede reemplazar ese truco por un criterio explicable.

**Opcional:** considerar "empate" a los portafolios dentro de una tolerancia (≤ 1–5 % de la utilidad óptima), configurable con un slider. Con los datos actuales, a 2 % solo están los dos empates exactos.

## 4. Propuesta 4A — Nota de viabilidad

**Paso 0 — Filtro duro (lógica clásica, se mantiene del Sprint 2):** C2 (registro sanitario y ficha técnica) = No → "No viable" sin pasar por el sistema difuso. Un producto sin registro sanitario no se puede vender; difuminarlo sería un error conceptual.

**Entradas numéricas** (reemplazan los Sí/No del CSV):
| Variable | Criterio | Universo | Etiquetas |
|---|---|---|---|
| `margen_pct` | C7 | 0–40 % | bajo / medio / alto |
| `complementariedad` | C5 | 0–10 | baja / media / alta |
| `vida_util_meses` | C6 | 0–24 meses | corta / media / larga |
| `facilidad_operativa` | C3 | 0–10 | baja / media / alta |
| `afinidad` | C1 | 0–10 | baja / media / alta |
| `calidad_presentacion` | C4 | 0–10 | baja / media / alta |

Los puntos de corte deben anclarse a los umbrales que ya existían: p. ej. el margen mínimo de 12 % y la vida útil mínima de 6 meses del Sprint 2 deberían caer en la zona de transición "bajo → medio", no ser fronteras duras.

### Opción A (recomendada) — jerarquía de 5 sistemas, 45 reglas
```
margen ─────────┐
                ├─► [S1] Atractivo comercial ─┐
complementar. ──┘                             ├─► [S4] Fortaleza del negocio ─┐
vida útil ──────┐                             │                               ├─► [S5] NOTA DE VIABILIDAD
                ├─► [S2] Solidez operativa ───┘                               │
facilidad op. ──┘                                                             │
afinidad ───────┐                                                             │
                ├─► [S3] Encaje con la marca ─────────────────────────────────┘
calidad ────────┘
```
Cada caja es un `inferencia_mamdani` de 2 entradas con su tabla 3×3. Se usan los 6 criterios.

### Opción B — jerarquía corta de 3 sistemas, 27 reglas
S1 (margen × complementariedad) y S2 (vida útil × facilidad operativa) → S3 nota final. C1 y C4 se quedan como filtros Sí/No junto con C2. Menos trabajo, pero se pierde el grado en afinidad y calidad.

### "Que no valgan lo mismo" — dónde queda el peso
En Mamdani el peso no es un número que multiplica; está en **la estructura y en las tablas de reglas**:
- **Posición en la jerarquía:** en la opción A, lo comercial y lo operativo se combinan primero (S4) y el encaje de marca entra al final como ajuste.
- **Reglas dominantes:** en S5, "SI fortaleza es baja ENTONCES nota es baja" para cualquier valor de encaje hace que la fortaleza del negocio sea decisiva; el encaje solo sube o baja un nivel cuando la fortaleza es media o alta.
- **Reglas asimétricas:** en S1, "margen bajo" puede arrastrar a "atractivo bajo" aunque la complementariedad sea alta, pero no al revés.

Así se explica en la sustentación por qué un criterio pesa más que otro: se ve en la tabla.

### Qué se evalúa
Las 3 categorías del Sprint 2 **y** las 8 referencias Riovalle del Sprint 3. La página "Qué lanzar" puede filtrar candidatos con nota ≥ umbral, y así el Sprint 2 alimenta de verdad al Sprint 3.

## 5. Propuesta 4B — Desempate difuso

Un solo sistema de 2 entradas y 9 reglas, como en clase:

| Entrada | Cálculo | Etiquetas |
|---|---|---|
| `nota_promedio` | promedio de la nota 4A de los productos del portafolio, ponderado por utilidad | baja / media / alta |
| `exposicion_competidor` | Σ (utilidad × erosión) / utilidad total × 100 | baja / media / alta |

**Salida:** `preferencia` 0–100. Gana el de mayor preferencia. Si siguen empatados (diferencia < 0,5 puntos), se usa un criterio clásico explícito: mayor holgura de bodega.

En la app se muestran, para cada portafolio empatado: los grados de pertenencia de sus dos entradas, las reglas activas con su grado de activación (como la tabla `activas` del notebook de clase), la salida agregada con el centroide, y el ganador.

## 6. Decisiones que debe cerrar el equipo antes de construir
1. ¿4A, 4B o ambos? (Recomendación: ambos, 4A primero.)
2. Para 4A: ¿opción A (5 sistemas, 6 criterios) u opción B (3 sistemas, 4 criterios)?
3. Puntos de corte de las funciones de pertenencia de cada entrada.
4. Las tablas de reglas (5 o 3 tablas de 3×3 para 4A, 1 para 4B), escritas por el equipo.
5. **Datos numéricos** de las 3 categorías y las 8 referencias Riovalle (supuestos ilustrativos, como el resto) → `data/memoria_trabajo_portafolio_difusa.csv`. Deben ser coherentes con el Sprint 2: Bebidas debe salir con nota alta y Alquería con vida útil corta.
6. Tolerancia de empate para 4B.

## 7. Cómo se ve en la app
- **Página 3 (Viabilidad):** pestaña "Versión difusa": sliders por variable; gráficas de las funciones de pertenencia con la línea del valor actual (como la celda 21 del notebook de clase); diagrama de la jerarquía con el valor de cada nodo; tabla de reglas activas por subsistema; salida agregada con el centroide; tabla que compara el veredicto Sí/No del Sprint 2 con la nota difusa.
- **Página 6 (Desempate difuso):** toma los empates de `st.session_state["empates"]` y muestra la inferencia de 4B para cada uno.
- **Página 4 (Qué lanzar):** opción "Solo candidatos con nota difusa ≥ X".
- Colores de las etiquetas iguales a los de clase: baja `#64748B`, media `#F59E0B`, alta `#16A34A`.

## 8. Pruebas
- **Paridad con clase:** `inferencia_mamdani` generalizada con los datos de Mercado Libre → 70.1672721768 para (65, 7); grados r=65 → (0, 0.25, 0.75).
- Entradas fuera del universo se rechazan con `ValueError` (como `inferencia_mamdani(105, 4)` en clase).
- Cada tabla de reglas tiene exactamente 9 reglas y cubre todas las combinaciones.
- Casos borde: producto perfecto → nota alta; margen 0 → nota baja; C2 = No → no viable sin importar lo demás.
- Monotonía: subir el margen (con lo demás fijo) nunca baja la nota.
- Reproducibilidad: los empates de la sección 3 producen siempre el mismo ganador.
