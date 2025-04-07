# ai_engine/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .logic.recommendations import get_task_recommendations
from .logic.predictions import get_future_skills_predictions

@login_required
def recommendations_view(request):
    user = request.user
    recommended_tasks = get_task_recommendations(user)
    context = {
        'recommendations': recommended_tasks,
    }
    return render(request, 'ai_engine/recommendations.html', context)

@login_required
def skill_trends_view(request):
    skill_trends = get_future_skills_predictions()
    sorted_trends = dict(sorted(skill_trends.items(), key=lambda item: item[1]['predicted_score'], reverse=True))
    context = {
        'skill_trends': sorted_trends,
    }
    return render(request, 'ai_engine/skill_trends.html', context)