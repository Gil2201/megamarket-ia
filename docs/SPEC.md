# SPEC — App MegaMarket IA (Streamlit)

> Documento de diseño para construir con Claude Code. Léelo completo antes de escribir código.
> Proyecto de la materia **Fundamentos de Inteligencia Artificial** (Universidad EIA).
> Equipo: Jacobo Argote, Andrés Cardona, Miguel Valencia y Juan José Gil.
> Repositorio destino: `https://github.com/Gil2201/megamarket-ia` (nombre propuesto).

---

## 0. Resumen en una página

**Qué es:** una app web en Streamlit que reúne en un solo lugar todo lo que el equipo construyó en el semestre para MegaMarket SAS: búsqueda A* (Sprint 1), sistemas expertos (Sprint 2), algoritmo genético + teoría de juegos (Sprint 3) y, más adelante, lógica difusa (Sprint 4) y un agente conversacional.

**Para qué:** que el profesor (y cualquier usuario) pueda *usar* los algoritmos con datos editables, ver cómo razonan paso a paso y entender cómo se conectan entre sí, en vez de leer cuatro notebooks separados.

**Las cinco decisiones que definen el proyecto:**

1. **La lógica se separa de la interfaz.** Todo el código de los notebooks va a un paquete `megamarket/` en Python puro (sin Streamlit). Las páginas solo llaman esas funciones y muestran resultados. Esto hace el código defendible en la sustentación, testeable, y reutilizable por el agente del futuro.
2. **El código de los notebooks se porta casi literal.** Mismos nombres de funciones y variables, mismos comentarios en español, misma lógica. Solo se permiten las adaptaciones listadas en la sección 5.2. Si un resultado de la app no coincide con el notebook, es un bug.
3. **La navegación sigue el flujo del negocio, no el orden cronológico de los sprints.** Hay dos cadenas de decisión: *Logística* (¿a quién visito? → ¿en qué orden?) y *Portafolio* (¿es viable? → ¿cuáles lanzo? → ¿y si el rival reacciona?). Cada página muestra una etiqueta con el sprint del que viene.
4. **Las páginas se pasan resultados entre sí.** El sistema experto de logística le entrega sus clientes a la página de rutas; el AG le entrega su portafolio a la página del competidor. Así se ve que los sprints son un sistema, no ejercicios sueltos.
5. **Se construye por fases con pruebas de paridad.** Primero se porta la lógica y se verifica contra los resultados de los notebooks (sección 8); después la interfaz; después el despliegue. El Sprint 4 y el agente quedan con espacio reservado en la arquitectura, sin construirse todavía.

---

## 1. Contexto del negocio

**Megamarket** (megamarket.com.co) es una empresa colombiana real, fundada en 1997 en Medellín, que vende marcas propias (**Riovalle**, Padrísimo, Megamarket, Saudé) y representa otras marcas de consumo masivo ante cadenas de supermercado y retail. Su lema: *"Acercamos el mundo a las personas para una vida mejor"*. El proyecto toma a Megamarket como caso, pero **los datos operativos (clientes semanales, costos, utilidades, erosión) son ilustrativos**. El producto central del caso es la **Uva Pasa Riovalle**.

Como se usa la marca de una empresa real, la app debe decir en el pie de página de todas las páginas: *"Proyecto académico — Universidad EIA. No es un sitio oficial de Megamarket."*

- **Bodega:** Bodega Olaya Herrera (cerca del aeropuerto Olaya Herrera, Medellín).
- **Destino final de los camiones:** Plataforma Logística (parqueadero en Guayabal, Cra. 51C #12B Sur-76). Coordenada **estimada** por nomenclatura vial (±200–400 m); la app debe decirlo.
- **Dos rutas de reparto:**
  - **Poblado:** 8 clientes (Fruver del Río, Fruver Visitación, Five Sisters, Supermercado Merka 10, Hotel Four Points, Mercados Verona, EAFIT La Bodeguita, Redetrans). Acceso vial: Aguacatala.
  - **Valle de Aburrá (Sur):** 4 CEDIs (Vaquita Itagüí, Euro La Estrella, Merkepaisa, Supermú). Acceso vial: Itagüí Centro.
- **Portafolio:** MegaMarket evalúa nuevas categorías (aseo, lácteos Alquería, bebidas) con los 7 criterios del gerente general, y nuevas referencias de marca Riovalle (higo, mix de frutos secos, barra, granola, jugo, snack de plátano, compota, café) bajo restricción de presupuesto y bodega.
- **Cifras:** costos, utilidades, erosión y pagos del rival son **ficticios/ilustrativos**. La app debe decirlo donde aparezcan (igual que los notebooks).

**Restricción académica importante:** el curso es de IA simbólica/clásica (búsqueda, sistemas expertos, algoritmos evolutivos, teoría de juegos, lógica difusa). **No** se usa machine learning. El profesor pide que el código sea cercano a lo visto en clase y completamente explicable.

---

## 2. Lo que ya existe (sprints 1–3)

Los archivos originales están en `referencia/`. **Son la fuente de verdad.** No se modifican.

### Sprint 1 — Rutas con A* (`referencia/sprint1/`)
- `COORDENADAS` (lat, lon) de bodega, accesos, 12 clientes y plataforma.
- `heuristica(nodo, destino)`: haversine en km (admisible).
- `conectar(red, a, b, costo)`: aristas bidireccionales. Grafos `red_poblado` y `red_valle_aburra` (estrella desde el acceso vial + conexiones directas entre clientes a menos de `UMBRAL_CERCANIA_KM = 1.5`). La plataforma se conecta al acceso de cada zona con costo = haversine redondeado.
- `a_estrella(red, origen, destino)`: cola de prioridad `(f, g, camino)` con `heapq`, `visitados` revisado al extraer.
- `recorrido_completo(red, origen, clientes, destino_final)`: vecino más cercano usando A* en cada tramo; termina en la Plataforma Logística.
- `megamarket_mapa_rutas.html`: mapa Folium de referencia visual (tiles CartoDB light, capas conmutables grafo/ruta, panel resumen). Sirve como guía de estilo del mapa; en la app el mapa se **regenera desde Python**, no se incrusta este HTML.

### Sprint 2 — Sistemas expertos (`referencia/sprint2/`)
Arquitectura clásica: **base de conocimiento + memoria de trabajo + motor de inferencia** (encadenamiento hacia adelante, una pasada por elemento).

**Sistema 1 — Logística: ¿qué clientes entran en la ruta de esta semana?**
- Base de conocimiento: umbrales (`dias_sin_entrega = 15`, `flete_sobre_factura = 0.04`), política H1 (entrega 48–72 h, documental), atributos fijos por cliente (`ruta`, `rotacion_producto`).
- Memoria de trabajo: `data/memoria_trabajo_logistica.csv` (separador `;`, UTF-8 con BOM, valores "Sí"/"No"/"No hubo visita").
- Reglas: R1–R3 de inclusión (basta una), R4–R5 vetos (flete > 4 % de la factura; PVP no actualizado), R6 exclusión por defecto. Prioridad ALTA/MEDIA/BAJA; se queda la más alta.
- Salida → `recorrido_completo(..., prioridad=...)`, que atiende por **tandas** (ALTA → MEDIA → BAJA), vecino más cercano dentro de cada tanda.

**Sistema 2 — Portafolio: ¿una nueva categoría es viable?**
- 7 criterios C1–C7 (afinidad, legal, operativa, calidad/presentación, complementariedad, vida útil ≥ 6 meses, precio/margen ≥ 12 %).
- Memoria de trabajo: `data/memoria_trabajo_portafolio.csv` (Sí/No por criterio). Viable solo si cumple los 7 (AND).
- **Versión de datos:** se usa la **primera versión** del CSV (Bebidas viable; Alquería falla C6). Existió una segunda versión ("CON LOS CAMBIOS", con C6 intercambiado) que el equipo hizo solo para comprobar que el motor detectaba cambios en los datos; no se usa. El código del notebook es el mismo en ambas.

### Sprint 3 — Algoritmo genético + teoría de juegos (`referencia/sprint3/`)
**3A — ¿Qué referencias lanzamos?** (`MegaMarket_Sprint3A_AG_Portafolio.ipynb`)
- 8 candidatos `CANDIDATOS` con `costo_lanzamiento`, `espacio_bodega`, `utilidad_esperada_anual`. Restricciones: `PRESUPUESTO_TOTAL = 70_000_000`, `ESPACIO_BODEGA_TOTAL = 25`.
- Cromosoma binario de 8 genes. Reparación: retira el producto con peor utilidad/costo hasta que quepa. Fitness = utilidad + 1. Selección por ruleta, cruce de un punto, mutación (voltear un gen, p = 0.10), elitismo 1. Población 10, 15 generaciones, semilla 42.
- Validación con fuerza bruta (2⁸ = 256). Hay **dos portafolios óptimos empatados** en $122M.

**3B — ¿Y si un competidor reacciona?** (`MegaMarket_Sprint3B_AG_Minimax_Competidor.ipynb`)
- `EROSION` por producto (supuesto), `K_ATAQUES = 1`.
- Juego 2×2 de un producto (Jugo Natural): matriz de pagos, Nash puro, inducción hacia atrás (casos A, B, C).
- Minimax de dos niveles del portafolio: MAX elige portafolio, MIN ataca el producto que más daño hace. `utilidad_peor_caso = utilidad_total − perdida_maxima`.
- AG con `criterio` configurable (`"esperada"` / `"peor_caso"`), ruleta con fitness escalado, desempate `+ 0.001 × utilidad_total`. Población 30, 40 generaciones, semilla 42.
- Robustez (20 semillas) y sensibilidad (factor de erosión 0.5–1.5; k = 1, 2).
- `MegaMarket_Sprint3_Interactivo.html`: versión web interactiva ya hecha (candidatos editables, AG animado, Minimax). **Es la mejor referencia de UX que tenemos**: la página de Streamlit de este sprint debe ofrecer al menos lo mismo.

### Sprint 4 — Lógica difusa (pendiente)
Ver `docs/SPRINT4_LOGICA_DIFUSA.md`. **No se construye en las fases 0–4.** Solo se reserva el espacio.
El notebook de clase está en `referencia/clase/09_Logica_Difusa_Mercado_Libre.ipynb` (Mamdani hecho a mano con `numpy`: `trimf`, `trapmf`, `pertenencia_en`, `centroide`, `inferencia_mamdani`). El Sprint 4 debe seguir ese estilo.

---

## 3. Cómo se conectan los sprints (el hilo de la app)

```
CADENA LOGÍSTICA
  [Sprint 2 · SE logística] ¿A quién visitamos esta semana y con qué prioridad?
            │  clientes incluidos + prioridad
            ▼
  [Sprint 1 · A*] ¿En qué orden y por dónde? → mapa + km

CADENA PORTAFOLIO
  [Sprint 2 · SE portafolio] ¿Esta categoría/producto es viable?
            │  (hoy: Sí/No · Sprint 4: nota difusa 0–100)
            ▼
  [Sprint 3A · AG] ¿Cuáles lanzamos con el presupuesto y la bodega?
            │  portafolio óptimo (+ empates)
            ▼
  [Sprint 3B · Teoría de juegos + Minimax] ¿Y si el rival reacciona?
            │  empates en utilidad / peor caso
            ▼
  [Sprint 4 · Lógica difusa] Desempate entre portafolios equivalentes
```

Nota honesta para la página de inicio: hoy los datos de la cadena de portafolio **no están conectados** — el SE del Sprint 2 evalúa 3 *categorías* (aseo, Alquería, bebidas) y el Sprint 3 parte de 8 *referencias Riovalle* "que ya pasaron los 7 criterios", sin que esa evaluación esté en los datos. El Sprint 4 es la oportunidad de cerrar ese hueco (evaluar con lógica difusa las 8 referencias y que esa nota alimente el AG y el desempate).

---

## 4. Experiencia de usuario

### 4.1 Navegación
Usar `st.navigation` con `st.Page` agrupadas en secciones (no la carpeta `pages/` automática), para controlar el orden, los nombres y los íconos.

| Sección | Página | Sprint | Pregunta de negocio |
|---|---|---|---|
| — | **Inicio** | — | ¿Qué es MegaMarket y qué hace esta app? |
| Logística | **1. Clientes de la semana** | Sprint 2 | ¿A quién visitamos y con qué prioridad? |
| Logística | **2. Ruta óptima** | Sprint 1 | ¿En qué orden y cuántos km? |
| Portafolio | **3. Viabilidad de productos** | Sprint 2 (→ Sprint 4) | ¿La categoría cumple los criterios? |
| Portafolio | **4. Qué lanzar** | Sprint 3A | ¿Qué referencias caben y dejan más utilidad? |
| Portafolio | **5. Competidor** | Sprint 3B | ¿Qué pasa si un rival entra? |
| Próximamente | **6. Desempate difuso** | Sprint 4 | (placeholder) |
| Próximamente | **Asistente MegaMarket** | Agente | (placeholder) |

### 4.2 Estructura común de cada página (misma plantilla en todas)
1. **Encabezado:** título = pregunta de negocio; chip con el sprint y la técnica (p. ej. "Sprint 1 · Búsqueda A*").
2. **"El problema" (2–4 líneas):** qué se decide y por qué no es trivial.
3. **Datos de entrada (editables):** `st.data_editor` / sliders, con botón "Restaurar datos originales".
4. **Botón principal de ejecución** (un solo botón primario por página).
5. **Resultado:** métricas clave (`st.metric`) + visual principal (mapa, gráfica, tabla).
6. **"Cómo razonó el algoritmo":** traza paso a paso (reglas disparadas, generaciones del AG, árbol Minimax).
7. **Expander "Ver el código":** muestra el código real de las funciones clave con `inspect.getsource(...)`. Pensado para la sustentación.
8. **Expander "Supuestos y límites":** las notas de honestidad de los notebooks (cifras ficticias, coordenada estimada, Minimax simplificado, etc.).

### 4.3 Detalle por página

**Inicio**
- Hero con nombre y logo de MegaMarket (si el equipo lo entrega), una frase de propósito.
- Diagrama de las dos cadenas (sección 3) — puede ser un gráfico simple hecho con columnas/tarjetas de Streamlit o un SVG en línea; nada pesado.
- Línea de tiempo de sprints (1 → 4) con estado: completado / en curso.
- Tarjetas que llevan a cada página (`st.page_link`).
- Equipo, materia, universidad, y una nota "Código desarrollado con apoyo de Claude" (los notebooks ya la tienen).

**1. Clientes de la semana (SE logística)**
- Selector de ruta (Poblado / Valle de Aburrá / Ambas).
- Tabla editable con la memoria de trabajo (columnas del CSV; booleanos como checkbox, "mercaderista_reporta_stock_bajo" como selectbox de 3 estados). Opción de subir un CSV propio con el mismo formato.
- Umbrales editables (días sin entrega, % flete) con valores por defecto de la base de conocimiento.
- Resultado: una tarjeta por cliente — ✅ Incluir (prioridad) / ❌ Excluir — con las razones (R1…R6) como lista. Vetos resaltados.
- Tabla de reglas R1–R6 + H1 visible (como en el notebook).
- Botón **"Calcular la ruta con estos clientes →"**: guarda incluidos y prioridades en `st.session_state` y navega a la página 2.

**2. Ruta óptima (A*)**
- Fuente de clientes: *Todos los clientes (Sprint 1)* / *Los del sistema experto (Sprint 2)* (por defecto si existe en `session_state`) / *Selección manual* (multiselect).
- Mapa Folium (`streamlit-folium`): bodega, plataforma, accesos, clientes con número de orden de visita, color por prioridad; capas conmutables "Grafo completo" y "Ruta óptima". Distinguir **paradas de entrega** de **nodos de paso** (la ruta puede pasar por un cliente sin entregarle; p. ej. con el SE, la ruta Poblado pasa por Hotel Four Points sin que esté incluido).
- Métricas: km totales, número de paradas, tandas de prioridad.
- Tabla de tramos: desde → hasta, camino A* del tramo, km.
- "Cómo razonó": para un tramo elegido, mostrar la exploración de A* (nodos extraídos con g, h, f). Esto requiere una variante instrumentada de `a_estrella` que **devuelva** la traza sin cambiar la lógica (sección 5.2).

**3. Viabilidad de productos (SE portafolio)**
- Matriz editable producto × C1–C7 (checkbox), con descripción de cada criterio (`CRITERIOS_DETALLE`).
- Resultado: tarjeta por producto con semáforo por criterio y veredicto; tabla resumen comparativa.
- Pestaña reservada "Versión difusa (Sprint 4)" deshabilitada con texto "Próximamente".

**4. Qué lanzar (AG — Sprint 3A)**
- Tabla editable de candidatos (agregar/quitar; mínimo 5, máximo ~20 para que la fuerza bruta siga siendo instantánea — 2²⁰ ≈ 1M es el límite razonable; por encima, desactivar fuerza bruta y decirlo).
- Restricciones: presupuesto y espacio (sliders/number inputs).
- Parámetros del AG: población, generaciones, p. de mutación, elitismo, semilla (valores por defecto = notebook).
- Gráfica de burbujas costo vs. utilidad (tamaño = espacio), como en el notebook.
- Ejecutar: evolución por generación (mejor y promedio; diversidad) en Plotly. Animación opcional con un slider de generación (no `time.sleep` en bucle).
- Resultado: productos elegidos, costo usado, espacio usado, utilidad.
- Validación: fuerza bruta; mostrar **todos** los portafolios óptimos empatados y un aviso claro: "Hay N portafolios con la misma utilidad → ver desempate (Sprint 4)".
- Guardar el resultado en `session_state` para la página 5.

**5. Competidor (Teoría de juegos + Minimax — Sprint 3B)**
- Pestaña A — **Juego de un producto:** selector de producto, sliders de erosión y de pagos del rival; matriz 2×2 con Nash resaltado; resultado de inducción hacia atrás; los tres casos del notebook como botones de "precarga".
- Pestaña B — **Portafolio vs. rival:** árbol Minimax de dos niveles del portafolio de la página 4 (o del Sprint 3 por defecto); AG con criterio "peor caso"; tabla comparativa esperada vs. peor caso; scatter "costo de protegerse" con los portafolios válidos.
- Pestaña C — **Sensibilidad:** factor de erosión y k ataques; tabla del notebook.
- Robustez (20 semillas) detrás de un botón (es lo único algo más lento).

**6. Desempate difuso (Sprint 4) y Asistente** — páginas placeholder con una explicación de lo que vendrá. Ver `docs/SPRINT4_LOGICA_DIFUSA.md` y sección 9.

### 4.4 Diseño visual
- Limpio y profesional: fondo claro, mucho espacio en blanco, tarjetas con borde sutil, sin degradados ni decoración innecesaria.
  **Excepción: la página de Inicio** funciona como landing (referencias: stripe.com y puygroup.com): titular grande en dos tonos, botones píldora, banda azul con cifras calculadas en vivo, tarjetas bento con miniaturas y un degradado suave solo en la decoración del hero. Su CSS vive en `tema.aplicar_css_inicio()`.
- **Colores de marca** (leídos del sitio megamarket.com.co):
  | Token | Hex | Uso en el sitio | Uso en la app |
  |---|---|---|---|
  | `azul_noche` | `#001B33` | barra superior, pie, franjas | encabezado/hero, barra lateral, texto de títulos |
  | `azul_rey` | `#2E448D` | botón "Contáctanos" | `primaryColor`: botones, enlaces, elementos activos |
  | `azul_medio` | `#0F487A` | acentos | series secundarias de gráficas, hover |
  | `amarillo_globo` | `#EDC443` *(medido en el PNG del logo)* | globo del logo | acento puntual (chips de sprint, destacados), nunca texto sobre blanco |
  | `texto` | `#212529` | cuerpo | `textColor` |
  | `gris` | `#636363` | texto secundario | leyendas, notas |
  | `fondo_suave` | `#F4F6F9` | — | `secondaryBackgroundColor`, tarjetas |
  | `blanco` | `#FFFFFF` | fondo | `backgroundColor` |
- **Tipografía:** el sitio usa **Montserrat** (títulos y texto). Usar Montserrat desde Google Fonts vía CSS (o `font = "sans serif"` en `config.toml` si falla la carga).
- **Logo:** versión blanca para fondo oscuro en `https://www.megamarket.com.co/wp-content/uploads/2024/02/logo-megamarket-logoblanco.png`. Guardarlo en `assets/` (descargarlo manualmente) y usarlo solo en el encabezado sobre `azul_noche`, con el aviso de proyecto académico del pie de página.
- Todos los colores en **un solo lugar**: `.streamlit/config.toml` (`[theme]`: `primaryColor`, `backgroundColor`, `secondaryBackgroundColor`, `textColor`, `font`) + `megamarket_app/tema.py` (paleta para Plotly/Folium y CSS mínimo). Cambiar la marca = editar esos dos archivos.
- Colores semánticos reservados (no son de marca, se usan solo para significado): verde `#16A34A` = incluir/viable/mejora, rojo `#DC2626` = excluir/veto/empeora, ámbar `#F59E0B` = prioridad media/advertencia. Sprint 3: `azul_rey` = criterio utilidad esperada, naranja `#EB6834` = Minimax (consistente con los notebooks). Lógica difusa: baja `#64748B`, media `#F59E0B`, alta `#16A34A` (los colores del notebook de clase).
- CSS personalizado mínimo (vía `st.markdown(..., unsafe_allow_html=True)` en un solo helper). No pelear contra Streamlit.
- Formato de números: pesos colombianos `$122.000.000` o `$122,0 M`; km con 1 decimal; porcentajes con 1 decimal. Un helper `formato.py` para todo.
- Todo el texto de la interfaz en **español**.

---

## 5. Arquitectura técnica

### 5.1 Estructura del repositorio
```
megamarket-ia/
├── CLAUDE.md                     # reglas para Claude Code (leer siempre)
├── README.md                     # qué es, cómo correrlo, link a la app
├── requirements.txt              # versiones fijadas
├── .streamlit/
│   └── config.toml               # tema (colores de marca)
├── app.py                        # punto de entrada: st.navigation
├── megamarket/                   # LÓGICA PURA (sin streamlit) — portada de los notebooks
│   ├── __init__.py
│   ├── datos.py                  # COORDENADAS, clientes, CANDIDATOS, EROSION, constantes
│   ├── busqueda.py               # Sprint 1: heuristica, conectar, redes, a_estrella, recorrido_completo
│   ├── sistema_experto_logistica.py   # Sprint 2 SE1
│   ├── sistema_experto_portafolio.py  # Sprint 2 SE2
│   ├── genetico.py               # Sprint 3A: AG de portafolio (fiel al notebook 3A)
│   ├── competidor.py             # Sprint 3B: matriz 2x2, Nash, Minimax, AG con criterio
│   └── difuso.py                 # Sprint 4 (vacío por ahora, con docstring de lo que vendrá)
├── megamarket_app/               # INTERFAZ (streamlit)
│   ├── tema.py                   # paleta, CSS, helpers visuales
│   ├── formato.py                # COP, km, %
│   ├── componentes.py            # encabezado de página, tarjeta, "ver código", "supuestos"
│   ├── mapas.py                  # construcción del mapa Folium
│   ├── graficas.py               # Plotly
│   └── paginas/
│       ├── inicio.py
│       ├── clientes_semana.py
│       ├── ruta_optima.py
│       ├── viabilidad.py
│       ├── que_lanzar.py
│       ├── competidor.py
│       ├── desempate_difuso.py   # placeholder
│       └── asistente.py          # placeholder
├── assets/
│   └── logo-megamarket-blanco.png   # se agrega a mano
├── data/
│   ├── memoria_trabajo_logistica.csv
│   └── memoria_trabajo_portafolio.csv
├── tests/
│   ├── test_sprint1.py
│   ├── test_sprint2.py
│   └── test_sprint3.py
├── docs/
│   ├── SPEC.md                   # este documento
│   └── SPRINT4_LOGICA_DIFUSA.md
└── referencia/                   # notebooks y HTML originales — SOLO LECTURA
    ├── sprint1/  sprint2/  sprint3/
    └── clase/                # notebook de lógica difusa visto en clase
```

### 5.2 Reglas para portar el código de los notebooks
Permitido (y nada más):
1. **Quitar `print`/`display` de las funciones de lógica y devolver datos.** Ej.: `decidir_clientes_de_la_ruta` devuelve `incluidos, prioridad_por_cliente, traza` (la traza es la lista de conclusiones con sus razones, que antes se imprimía).
2. **Convertir globales en parámetros con el mismo valor por defecto**, para que la interfaz pueda editarlos. Ej.: `es_portafolio_valido(individuo, candidatos=CANDIDATOS, presupuesto=PRESUPUESTO_TOTAL, espacio=ESPACIO_BODEGA_TOTAL)`. Con los valores por defecto el resultado debe ser idéntico.
3. **Variantes instrumentadas** que devuelven la traza (p. ej. `a_estrella_con_traza`) **al lado** de la original, nunca en su lugar.
4. **Lectura de CSV** desde ruta o desde un `DataFrame` ya cargado (la interfaz puede pasar el resultado del `data_editor`).
5. **Aleatoriedad:** mantener `random.seed(semilla)` y el mismo orden de llamadas a `random` que el notebook, para que con semilla 42 salga exactamente lo mismo.

Prohibido:
- Renombrar funciones o variables del notebook, "mejorar" algoritmos, cambiar la heurística, la reparación, la selección o los umbrales.
- Unificar el AG de 3A con el de 3B: son **dos versiones distintas** en los notebooks (3A: fitness +1 y ruleta simple; 3B: ruleta escalada y criterio configurable). Se mantienen ambas, cada una en su módulo, aunque haya duplicación. La fidelidad pesa más que el DRY.
- Importar `streamlit` dentro de `megamarket/`.

### 5.3 Estado compartido entre páginas (`st.session_state`)
| Clave | La escribe | La lee | Contenido |
|---|---|---|---|
| `memoria_logistica` | Clientes de la semana | misma | DataFrame editado |
| `seleccion_semana` | Clientes de la semana | Ruta óptima | `{ruta: {"incluidos": [...], "prioridad": {...}}}` |
| `candidatos` | Qué lanzar | Competidor | dict de candidatos editado |
| `resultado_ag` | Qué lanzar | Competidor, (Sprint 4) | mejor portafolio, historial, empates |
| `empates` | Qué lanzar / Competidor | Desempate difuso | lista de portafolios empatados por criterio |

Inicializar todo en un solo lugar (`app.py`) con los datos originales.

### 5.4 Librerías
- `streamlit` (≥ 1.40, por `st.navigation`/`st.Page`), `pandas`, `numpy`, `plotly`, `folium`, `streamlit-folium`, `pytest`.
- Sprint 4: **implementación propia con `numpy`**, igual que el notebook de clase (no `scikit-fuzzy`).
- Agente: `anthropic` — solo cuando se construya.
- Fijar versiones en `requirements.txt` y verificar que instalan en Streamlit Community Cloud.
- Usar `@st.cache_data` para fuerza bruta, validez de portafolios y construcción de grafos.

---

## 6. Despliegue

1. Repo en `github.com/Gil2201/megamarket-ia`. Recomendado **público** (lo más simple para Streamlit Community Cloud y para que el profesor lo vea). Agregar a Jacobo, Andrés y Miguel como colaboradores.
2. Streamlit Community Cloud (share.streamlit.io) → iniciar sesión con GitHub → *New app* → repo `Gil2201/megamarket-ia`, rama `main`, archivo `app.py`. Elegir versión de Python en *Advanced settings* (la misma que se usó localmente).
3. Secretos (solo cuando exista el agente): `ANTHROPIC_API_KEY` en *Settings → Secrets* de Streamlit Cloud y en `.streamlit/secrets.toml` local. **`secrets.toml` va en `.gitignore`. Nunca se sube una llave al repo.**
4. Cada `git push` a `main` redespliega automáticamente. Trabajar en ramas para cambios grandes (Sprint 4, agente).

---

## 7. Plan de construcción por fases

Cada fase empieza en **modo plan** de Claude Code (proponer antes de escribir) y termina cuando se cumplen sus criterios de aceptación. Hacer commit al cerrar cada fase.

**Fase 0 — Esqueleto**
- Crear estructura de carpetas, `requirements.txt`, `.gitignore`, `config.toml` con colores provisionales, `app.py` con `st.navigation` y todas las páginas como placeholders.
- ✅ `streamlit run app.py` abre y se puede navegar por todas las páginas.

**Fase 1 — Lógica portada + pruebas de paridad (sin interfaz)**
- Portar Sprint 1, 2 y 3 a `megamarket/` según 5.2.
- Escribir `tests/` con los valores de la sección 8.
- ✅ `pytest` pasa completo. Ningún módulo de `megamarket/` importa Streamlit.

**Fase 2 — Cadena logística (páginas 1 y 2)**
- Clientes de la semana + Ruta óptima + mapa + paso de `session_state`.
- ✅ Con los datos originales, la página muestra exactamente las decisiones y km de la sección 8; editar un dato del CSV cambia la decisión y la ruta.

**Fase 3 — Cadena portafolio (páginas 3, 4 y 5)**
- Viabilidad, Qué lanzar, Competidor.
- ✅ Con valores por defecto: $122M y los 2 empates; Minimax $95,0M; casos A/B/C del Jugo iguales al notebook.

**Fase 4 — Inicio, pulido visual y despliegue**
- Página de inicio, aplicar colores de marca reales, revisar en ancho de celular, README, desplegar.
- ✅ App pública funcionando en Streamlit Cloud; link en el README.

**Fase 5 — Sprint 4: lógica difusa** → seguir `docs/SPRINT4_LOGICA_DIFUSA.md` (después de que el equipo cierre las decisiones de diseño con el profesor).

**Fase 6 — Agente** → ver sección 9 (cuando el profesor dé los requisitos).

---

## 8. Resultados esperados (pruebas de paridad)

Obtenidos corriendo los notebooks de `referencia/` con los CSV de `data/`. La app y los tests deben reproducirlos exactamente.

**Sprint 1 — todos los clientes, destino Plataforma Logística**
- Poblado: **16,8 km**. Orden de clientes: EAFIT La Bodeguita → Hotel Four Points → Supermercado Merka 10 → Five Sisters → Redetrans → Mercados Verona → Fruver Visitación → Fruver del Río.
- Valle de Aburrá: **18,0 km**. Orden: CEDI Vaquita Itagüí → CEDI Merkepaisa → CEDI Supermú → CEDI Euro La Estrella.

**Sprint 2 — SE logística (CSV de `data/`)**
| Cliente | Decisión | Razones |
|---|---|---|
| Fruver del Río | ❌ | R1 (ALTA) + **veto R4** (flete 5,9 %) |
| Fruver Visitación | ❌ | R6 |
| Five Sisters | ✅ BAJA | R2 (sin visita, 18 días, rotación media) |
| Supermercado Merka 10 | ✅ ALTA | R3 |
| Hotel Four Points | ❌ | R6 |
| Mercados Verona | ✅ MEDIA | R1 |
| EAFIT La Bodeguita | ✅ ALTA | R3 |
| Redetrans | ❌ | R1 (BAJA) + **veto R5** (PVP) |
| CEDI Vaquita Itagüí | ✅ ALTA | R1 |
| CEDI Euro La Estrella | ❌ | R2 + **veto R4** (flete 5,3 %) |
| CEDI Merkepaisa | ❌ | R1 (MEDIA) + **veto R4** (flete 5,6 %) |
| CEDI Supermú | ✅ ALTA | R3 |

- Ruta Poblado con SE: **9,9 km**, orden EAFIT La Bodeguita → Supermercado Merka 10 → Mercados Verona → Five Sisters.
- Ruta Valle con SE: **14,9 km**, orden CEDI Vaquita Itagüí → CEDI Supermú.

**Sprint 2 — SE portafolio (primera versión del CSV):** Aseo ❌ (C1, C3) · Alquería ❌ (C6) · Bebidas ✅.

**Sprint 3A (semilla 42, población 10, 15 generaciones, mutación 0,10, elitismo 1)**
- AG: Higo Deshidratado + Jugo Natural + Café Molido · $70.000.000 · 22/25 posiciones · **$122.000.000**.
- Fuerza bruta: óptimo $122.000.000; 111 portafolios válidos; **2 óptimos**: {Higo, Jugo, Café} y {Mix de Frutos Secos, Barra Energética, Jugo}.

**Sprint 3B (semilla 42, población 30, 40 generaciones)**
- Portafolio del Sprint 3 en peor caso: **$90,8M** (el rival ataca Jugo Natural).
- AG Minimax: Higo + Mix + Barra + Snack · $119,0M esperada · **$95,0M peor caso**. Empate en peor caso con {Higo, Granola, Compota, Café} ($114M esperada).
- Jugo 2×2: Caso A (35 %, 6M/18M) → Nash (Lanzar, Entrar), Riovalle 3,8M. Caso B (50 %) → Nash (No lanzar, Entrar). Caso C (50 %, −3M/18M) → dos Nash; secuencial (Lanzar, No entrar), Riovalle 22,0M.
- Robustez: 19/20 en ambos criterios. Sensibilidad: ver tabla de la Parte 5 del notebook 3B (×0,5 → $107,0M; ×1,0 → $95,0M; ×1,5 → $85,5M; k = 2, ×1,0 → $85,4M vs. $71,8M).

---

## 9. Preparado para el agente (no construir todavía)

El profesor quiere un agente dentro de la app. La arquitectura ya lo facilita: **cada función pública de `megamarket/` es una herramienta potencial** (p. ej. `decidir_clientes_de_la_ruta`, `recorrido_completo`, `algoritmo_genetico_portafolio`, `utilidad_peor_caso`). Por eso:
- Toda función pública de `megamarket/` lleva docstring en español que diga qué recibe, qué devuelve y qué decisión de negocio responde.
- Las salidas son datos serializables (dicts, listas, números), no objetos de Streamlit ni texto impreso.
- Cuando se construya: página "Asistente MegaMarket" con `st.chat_input`/`st.chat_message`, API de Anthropic con *tool use*, llave en `st.secrets`, límite de tokens por mensaje para controlar costo, y respuestas que citen qué algoritmo se corrió y con qué datos.

---

## 10. Fuera de alcance (por ahora)
- Machine learning de cualquier tipo.
- Base de datos o login. Los datos viven en CSV + `session_state`; lo que el usuario edita se pierde al recargar (se puede descargar como CSV).
- Geocodificación real o rutas por calles reales (OSRM, Google Maps). Se usan los grafos de los notebooks.
- Cambiar los algoritmos de los sprints 1–3.

## 11. Decisiones pendientes del equipo
1. ~~Colores de marca~~ → resuelto (§4.4). Amarillo del logo medido: `#EDC443`.
2. ~~**Sprint 4**~~ → resuelto como propuesta: `docs/SPRINT4_DECISIONES.md` (4A opción A + 4B). Librería: `numpy` a mano, como en clase.
3. ~~**Datos numéricos de los productos**~~ → `data/memoria_trabajo_portafolio_difusa.csv` (ilustrativos, por validar).
4. **Requisitos del agente** que pida el profesor.
5. ~~Versión del CSV de portafolio~~ → resuelto: la primera. ~~Estrategia evolutiva de mercadeo~~ → no hace parte del proyecto.
