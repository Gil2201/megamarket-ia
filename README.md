# MegaMarket IA

App en Streamlit que reúne el proyecto de **Fundamentos de Inteligencia Artificial** (Universidad EIA)
sobre el caso **MegaMarket SAS**: búsqueda A*, sistemas expertos, algoritmo genético y teoría de juegos,
y lógica difusa.

> Proyecto académico — Universidad EIA. **No es un sitio oficial de Megamarket.** Las cifras operativas
> (clientes, costos, utilidades, erosión) son ilustrativas.

**App publicada:** _pendiente de despliegue en Streamlit Community Cloud_.

## Qué hace

La navegación sigue dos cadenas de decisión del negocio:

| Cadena | Página | Sprint | Pregunta |
|---|---|---|---|
| Logística | 1. Clientes de la semana | Sprint 2 · Sistema experto | ¿A quién visitamos y con qué prioridad? |
| Logística | 2. Ruta óptima | Sprint 1 · A* | ¿En qué orden y cuántos km? |
| Portafolio | 3. Viabilidad de productos | Sprint 2 · Sistema experto + Sprint 4 · Lógica difusa | ¿Cumple los 7 criterios? ¿Con qué nota de 0 a 100? |
| Portafolio | 4. Qué lanzar | Sprint 3A · Algoritmo genético | ¿Qué referencias caben y dejan más utilidad? |
| Portafolio | 5. Competidor | Sprint 3B · Teoría de juegos + Minimax | ¿Y si un rival reacciona? |
| Portafolio | 6. Desempate difuso | Sprint 4 · Lógica difusa | ¿Cuál elegimos entre portafolios empatados? |
| Asistente | Asistente MegaMarket | Fase 6 · Agente con herramientas | Preguntas en lenguaje natural que se responden corriendo los algoritmos |

Las páginas se pasan resultados: el sistema experto le entrega sus clientes a la ruta, y el AG le entrega
su portafolio al análisis del competidor. Cada página muestra cómo razonó el algoritmo, el código real
de las funciones clave y sus supuestos y límites.

## Cómo correrla

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Probada con Python 3.14.

## Asistente (opcional)

El asistente usa Gemini en su capa gratuita a través de una API compatible con OpenAI. Para activarlo,
crea `.streamlit/secrets.toml` (está en `.gitignore`) con:

```toml
GEMINI_API_KEY = "tu-clave-de-google-ai-studio"
APP_PASSWORD = "opcional: contraseña para el asistente"
```

En Streamlit Cloud, el mismo contenido va en *Settings → Secrets*. Sin clave, el resto de la app funciona igual.
El modelo **no decide**: interpreta la pregunta y llama herramientas (`agente/herramientas.py`) que envuelven los
algoritmos de `megamarket/`; cada respuesta muestra qué herramientas usó.

## Pruebas

```bash
pytest -q
```

Las pruebas verifican que los resultados sean **idénticos** a los de los notebooks de `referencia/`
(SPEC §8): 16,8 y 18,0 km con todos los clientes, 9,9 y 14,9 km con el sistema experto, $122 M con
2 portafolios óptimos, $95,0 M en el peor caso con Minimax, y 70,17 en el ejemplo de lógica difusa de clase, entre otros. También hay pruebas de humo
que abren cada página.

## Estructura

```
app.py              navegación y estado compartido
megamarket/         lógica pura (sin Streamlit), portada de los notebooks
megamarket_app/     interfaz: páginas, tema, mapas, gráficas
agente/             asistente: herramientas, ciclo del agente y proveedor (sin Streamlit)
evaluacion_agente/  19 preguntas de prueba, evaluador y calificador del asistente
data/               memorias de trabajo del Sprint 2 (CSV)
referencia/         notebooks originales de cada sprint (solo lectura)
docs/               SPEC.md y diseño del Sprint 4
tests/              pruebas de paridad y de la interfaz
```

## Equipo

Jacobo Argote, Andrés Cardona, Miguel Valencia y Juan José Gil.
Código desarrollado con apoyo de Claude.
