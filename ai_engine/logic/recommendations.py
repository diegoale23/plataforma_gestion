# ai_engine/logic/recommendations.py
from sklearn.metrics.pairwise import cosine_similarity
from projects.models import Task
from users.models import UserProfile

def get_task_recommendations(user):
    user_skills = set(user.profile.skills.values_list('name', flat=True))
    tasks = Task.objects.filter(status='PENDING')
    recommendations = []

    for task in tasks:
        task_skills = set(task.required_skills.values_list('name', flat=True))
        if task_skills:  # Evitar división por cero
            similarity = len(user_skills.intersection(task_skills)) / len(task_skills)
            if similarity >= 0.5:  # Umbral ajustable
                recommendations.append({
                    'task': task,
                    'similarity': similarity,
                    'matching_skills': list(user_skills.intersection(task_skills)),
                })

    return sorted(recommendations, key=lambda x: x['similarity'], reverse=True)[:5]