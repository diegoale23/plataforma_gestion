# ai_engine/logic/predictions.py
from sklearn.linear_model import LinearRegression
from market_analysis.models import MarketTrend
import numpy as np

def get_future_skills_predictions():
    trends = MarketTrend.objects.order_by('analysis_date')
    if not trends.exists():
        return {}

    skill_data = {}
    for trend in trends:
        for skill, data in trend.skill_trends.items():
            if skill not in skill_data:
                skill_data[skill] = {'dates': [], 'scores': []}
            skill_data[skill]['dates'].append(trend.analysis_date.toordinal())
            skill_data[skill]['scores'].append(data['score'])

    predictions = {}
    last_date = trends.last().analysis_date.toordinal()
    future_date = last_date + 30  # 1 mes adelante
    for skill, data in skill_data.items():
        X = np.array(data['dates']).reshape(-1, 1)
        y = np.array(data['scores'])
        if len(X) > 1:  # Necesitamos al menos 2 puntos para una regresión
            model = LinearRegression().fit(X, y)
            predicted_score = max(0, model.predict([[future_date]])[0])  # Evitar scores negativos
            predictions[skill] = {
                'total_occurrences': sum(data['scores']),
                'predicted_score': predicted_score,
            }
    
    return predictions