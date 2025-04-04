# ai_engine/logic/recommendations.py

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.contrib.auth.models import User
from projects.models import Task  # Asumiendo modelos en 'projects'
from typing import List # Para type hinting

# Umbral mínimo de similitud para considerar una recomendación
MIN_SIMILARITY_THRESHOLD = 0.1

def get_task_recommendations(user: User, max_recommendations: int = 5) -> List[Task]:
    """
    Recomienda tareas a un usuario basándose en la similitud coseno
    entre las habilidades del usuario y las habilidades requeridas por las tareas.

    Args:
        user: El objeto User de Django para el cual generar recomendaciones.
        max_recommendations: El número máximo de tareas a recomendar.

    Returns:
        Una lista de objetos Task recomendados, ordenados por relevancia (similitud).
        Retorna una lista vacía si no se pueden generar recomendaciones.
    """
    try:
        # 1. Obtener perfil y habilidades del usuario
        profile = user.profile # Asume que la relación OneToOne se llama 'profile'
        user_skills = list(profile.skills.values_list('name', flat=True))

        if not user_skills:
            print(f"Usuario {user.username} no tiene habilidades definidas. No se pueden generar recomendaciones.")
            return []

        # Habilidades del usuario como un solo string
        user_skills_text = " ".join(skill.lower() for skill in user_skills) # Convertir a minúsculas

    except AttributeError:
        print(f"Usuario {user.username} no tiene perfil ('profile'). No se pueden generar recomendaciones.")
        return []
    except Exception as e:
        print(f"Error obteniendo perfil/habilidades para {user.username}: {e}")
        return []

    try:
        # 2. Obtener tareas candidatas (pendientes o en progreso, no asignadas al usuario, y que requieran habilidades)
        available_tasks = Task.objects.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        ).exclude(
            assigned_to=user
        ).filter(
            required_skills__isnull=False # Asegura que la tarea tenga al menos una habilidad requerida
        ).prefetch_related(
            'required_skills' # Optimización: precarga las habilidades
        ).distinct() # Evita duplicados si una tarea coincide por múltiples razones

        if not available_tasks.exists():
            print("No hay tareas disponibles para recomendar.")
            return []

        # 3. Preparar los "documentos" de habilidades para cada tarea
        task_skills_texts = []
        task_map = [] # Mapea índice de la lista de textos al objeto Task
        for task in available_tasks:
            skills = list(task.required_skills.values_list('name', flat=True))
            if skills: # Doble check por si acaso
                task_skills_texts.append(" ".join(skill.lower() for skill in skills)) # Convertir a minúsculas
                task_map.append(task)

        if not task_skills_texts:
            print("Ninguna tarea disponible tiene habilidades asociadas después del filtrado.")
            return []

        # 4. Calcular similitud usando TF-IDF
        # El primer documento es el perfil del usuario
        all_texts = [user_skills_text] + task_skills_texts

        vectorizer = TfidfVectorizer(stop_words='english') # Puedes añadir stop words en español si es relevante
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Calcular similitud coseno entre el vector del usuario (índice 0) y los vectores de las tareas
        cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # 5. Crear pares (similitud, tarea) y ordenar
        # Asegurarse de que la longitud de similaridades coincida con task_map
        if len(cosine_similarities) != len(task_map):
             print(f"Error: Discrepancia en longitud entre similaridades ({len(cosine_similarities)}) y task_map ({len(task_map)})")
             # Aquí podrías investigar por qué ocurrió esto, pero por ahora retornamos vacío
             return []

        task_similarity_pairs = list(zip(cosine_similarities, task_map))

        # Filtrar por umbral y ordenar de mayor a menor similitud
        relevant_tasks_pairs = [pair for pair in task_similarity_pairs if pair[0] >= MIN_SIMILARITY_THRESHOLD]
        relevant_tasks_pairs.sort(key=lambda x: x[0], reverse=True)

        # 6. Devolver las N tareas más recomendadas
        recommended_tasks = [task for similarity, task in relevant_tasks_pairs[:max_recommendations]]

        print(f"Recomendaciones generadas para {user.username}: {len(recommended_tasks)} tareas.")
        return recommended_tasks

    except Exception as e:
        print(f"Error durante el cálculo de recomendaciones TF-IDF para {user.username}: {e}")
        # Considerar logging más detallado aquí
        return []