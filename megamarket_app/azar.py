"""Candado para el generador aleatorio global.

Los AG de los notebooks usan `random.seed(...)` y el módulo `random` global.
En Streamlit Cloud varios usuarios comparten el mismo proceso: si dos
corridas se cruzan, se mezclarían sus números aleatorios y la semilla 42 ya
no daría el resultado del notebook. Toda corrida con semilla se hace dentro
de `with CANDADO_AZAR:` para que sea reproducible. La lógica no cambia.
"""

import threading

CANDADO_AZAR = threading.Lock()
