# Cómo arrancar con Claude Code

1. Crea el repo vacío `megamarket-ia` en github.com/Gil2201 (público) y clónalo en tu Mac (o usa GitHub Desktop).
2. Copia **todo el contenido de este kit** dentro de la carpeta del repo (CLAUDE.md, docs/, data/, referencia/).
3. Haz un primer commit: "Kit inicial: spec y referencias de los sprints 1–3".
4. Abre Claude Code en esa carpeta y pega este primer mensaje:

```
Lee CLAUDE.md y docs/SPEC.md completos, y revisa los notebooks de referencia/.
Antes de escribir código:
1) Resúmeme en tus palabras qué vamos a construir y cómo se conectan los sprints.
2) Dime si ves contradicciones o huecos en el SPEC.
3) Propón el plan detallado de la Fase 0 y la Fase 1.
No escribas código hasta que yo apruebe el plan.
```

5. Avanza fase por fase (SPEC §7). Al final de cada una: `pytest -q`, `streamlit run app.py`, revisa, y commit.
6. Para el Sprint 4, cuando el equipo cierre las decisiones de `docs/SPRINT4_LOGICA_DIFUSA.md` §6, dile a Claude Code:
   `Lee docs/SPRINT4_LOGICA_DIFUSA.md. Estas son nuestras decisiones: [...]. Propón el plan de la Fase 5.`

Este archivo se puede borrar del repo una vez arranquen.
