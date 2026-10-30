# CLAUDE.md — MegaMarket IA

App en Streamlit que unifica el proyecto de **Fundamentos de Inteligencia Artificial (EIA)** sobre el caso Megamarket (empresa real, datos ilustrativos): A* (Sprint 1), sistemas expertos (Sprint 2), algoritmo genético + teoría de juegos (Sprint 3) y, después, lógica difusa (Sprint 4) y un agente.

## Antes de cualquier cosa
- Lee `docs/SPEC.md` completo. Es el diseño acordado.
- Para el Sprint 4 lee `docs/SPRINT4_LOGICA_DIFUSA.md` y `docs/SPRINT4_DECISIONES.md` (decisiones de la sección 6 cerradas como propuesta para validar con el profesor; ya está construido en `megamarket/difuso.py`).
- Los notebooks de `referencia/` son la **fuente de verdad** del comportamiento. Son de solo lectura: nunca los edites.
- Trabaja por las fases de la sección 7 del SPEC. Al empezar cada fase, propón un plan y espera aprobación.

## Reglas que no se negocian
1. **El código se debe poder sustentar oralmente.** El profesor exige que sea cercano a lo visto en clase. Porta funciones de los notebooks con los mismos nombres, variables y comentarios en español. Solo se permiten las adaptaciones de SPEC §5.2.
2. **Lógica separada de la interfaz.** `megamarket/` es Python puro y nunca importa `streamlit`. `megamarket_app/` y `app.py` son la interfaz.
3. **Paridad con los notebooks.** Los valores de SPEC §8 deben salir idénticos. `pytest` debe pasar antes de cerrar cualquier fase. Si cambias lógica y un test falla, el bug es tuyo, no del test.
4. **No mejores los algoritmos** (heurística, reparación, selección, umbrales, reglas) aunque veas algo "mejorable". Si crees que algo está mal, dilo y pregunta.
5. **Honestidad de alcance.** Las cifras son ficticias; la coordenada de la Plataforma Logística es estimada; el Minimax es simplificado. La app lo dice donde corresponde (expander "Supuestos y límites").
6. **Nada de machine learning.** El curso es de IA simbólica/clásica.
7. **Todo en español:** interfaz, comentarios, docstrings, mensajes de commit.
8. **Nunca subas secretos.** `.streamlit/secrets.toml` va en `.gitignore`.

## Comandos
- Correr la app: `streamlit run app.py`
- Pruebas: `pytest -q`
- Instalar: `pip install -r requirements.txt`

## Estilo
- Colores solo en `.streamlit/config.toml` y `megamarket_app/tema.py`, con la paleta de marca de SPEC §4.4 (azul noche `#001B33`, azul rey `#2E448D`, Montserrat).
- Megamarket es una empresa real: el pie de página siempre dice que es un proyecto académico y no un sitio oficial.
- Diseño limpio y profesional; misma plantilla de página en todas (SPEC §4.2).
- Formatos con los helpers de `megamarket_app/formato.py` (COP, km, %).

## Quiénes somos
Equipo: Jacobo Argote, Andrés Cardona, Miguel Valencia y Juan José Gil. Repo: `github.com/Gil2201/megamarket-ia`. Despliegue: Streamlit Community Cloud.
