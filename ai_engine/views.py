# En alguna vista (ej: ai_engine/views.py o market_analysis/views.py)

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .logic.recommendations import get_task_recommendations
from .logic.predictions import get_future_skills_predictions

@login_required
def recommendations_view(request):
    user = request.user
    # Llama a la función de lógica para obtener recomendaciones
    recommended_tasks = get_task_recommendations(user)
    context = {
        'recommendations': recommended_tasks
    }
    # Renderiza una plantilla que muestre las tareas recomendadas
    return render(request, 'ai_engine/recommendations.html', context)

@login_required
def skill_trends_view(request): # O integrar en el dashboard de mercado
    # Llama a la función de lógica para obtener predicciones
    skill_trends = get_future_skills_predictions()

    # Puedes ordenar por alguna métrica si quieres, ej: ocurrencias totales
    sorted_trends = dict(sorted(skill_trends.items(), key=lambda item: item[1].get('total_occurrences', 0), reverse=True))

    context = {
        'skill_trends': sorted_trends
    }
    # Renderiza una plantilla que muestre las tendencias
    return render(request, 'ai_engine/skill_trends.html', context)