# ai_engine/models.py
from django.db import models

# --- No se definen modelos específicos para el motor de IA por ahora ---
# La lógica de IA (recomendaciones, predicciones) opera sobre los modelos
# existentes en las otras apps (User, Task, JobOffer, Skill, MarketTrend).

# Si en el futuro necesitaras almacenar:
#   - Modelos de ML entrenados (aunque es mejor guardarlos en archivos/storage).
#   - Historial detallado de recomendaciones por usuario.
#   - Evaluaciones de la precisión de los modelos.
# podrías añadir modelos aquí.

# Por ahora, este archivo puede permanecer vacío o con comentarios.