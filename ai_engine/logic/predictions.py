# ai_engine/logic/predictions.py

import pandas as pd
from django.utils import timezone
from datetime import timedelta
from market_analysis.models import JobOffer, Skill # Asumiendo modelos en 'market_analysis'
from sklearn.linear_model import LinearRegression
import numpy as np
from typing import Dict, Any # Para type hinting

# Número de meses hacia atrás para considerar en el análisis de tendencias
MONTHS_HISTORY = 12
# Número mínimo de ocurrencias de una habilidad para considerarla en la predicción
MIN_SKILL_OCCURRENCES = 10

def get_future_skills_predictions() -> Dict[str, Dict[str, Any]]:
    """
    Analiza la frecuencia histórica de habilidades en ofertas de empleo
    y predice tendencias futuras simples (sube, baja, estable) usando regresión lineal.

    Returns:
        Un diccionario donde las claves son nombres de habilidades y los valores
        son diccionarios con la 'tendencia' ('up', 'down', 'stable') y
        posiblemente otras métricas como la 'pendiente' de la regresión.
        Ej: {'Python': {'trend': 'up', 'slope': 1.5}, 'Java': {'trend': 'stable', 'slope': 0.1}}
    """
    print(f"Iniciando análisis de tendencias de habilidades (últimos {MONTHS_HISTORY} meses)...")
    predictions = {}
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=MONTHS_HISTORY * 30) # Aproximación

    try:
        # 1. Obtener datos relevantes de la base de datos
        # Seleccionamos ofertas con fecha de publicación en el rango deseado
        # y que tengan habilidades asociadas. Values() es más eficiente.
        offers_with_skills = JobOffer.objects.filter(
            publication_date__isnull=False,
            publication_date__gte=start_date,
            publication_date__lte=end_date,
            required_skills__isnull=False
        ).values(
            'id', # Necesario para distinguir ofertas
            'publication_date',
            'required_skills__name' # Obtenemos directamente el nombre de la habilidad
        ).distinct() # Evita duplicados si una oferta tiene la misma habilidad listada múltiples veces (?) - Revisar si es necesario

        if not offers_with_skills:
            print("No hay suficientes datos de ofertas con habilidades y fechas en el rango especificado.")
            return {}

        # 2. Convertir a DataFrame de Pandas
        df = pd.DataFrame.from_records(offers_with_skills)
        df['publication_date'] = pd.to_datetime(df['publication_date'])
        df.rename(columns={'required_skills__name': 'skill_name'}, inplace=True)

        print(f"DataFrame inicial creado con {len(df)} registros de habilidades.")

        # 3. Resample: Contar habilidades por mes
        # Agrupamos por mes ('ME' para fin de mes) y habilidad, contamos ocurrencias
        # Unstack convierte las habilidades en columnas, fill_value=0 rellena meses sin ocurrencias
        monthly_skill_counts = df.set_index('publication_date') \
                                 .groupby([pd.Grouper(freq='ME'), 'skill_name']) \
                                 .size() \
                                 .unstack(fill_value=0)

        if monthly_skill_counts.empty:
             print("DataFrame vacío después de agrupar por mes.")
             return {}

        print(f"Datos agrupados por mes. Matriz de habilidades: {monthly_skill_counts.shape}")
        # print(monthly_skill_counts.head()) # Descomentar para depurar

        # 4. Analizar tendencia para cada habilidad usando Regresión Lineal
        for skill in monthly_skill_counts.columns:
            skill_data = monthly_skill_counts[skill]

            # Filtrar habilidades con pocas ocurrencias totales
            if skill_data.sum() < MIN_SKILL_OCCURRENCES:
                # print(f"Skipping skill '{skill}' due to low occurrence ({skill_data.sum()}).")
                continue

            # Preparar datos para regresión
            # X: índice de tiempo (0, 1, 2...)
            # y: conteo mensual de la habilidad
            X = np.arange(len(skill_data)).reshape(-1, 1)
            y = skill_data.values

            # Evitar ajuste si hay muy pocos puntos de datos (meses)
            if len(y) < 3:
                 # print(f"Skipping skill '{skill}' due to insufficient data points ({len(y)} months).")
                 continue

            try:
                # Entrenar modelo de regresión lineal simple
                model = LinearRegression()
                model.fit(X, y)

                # La pendiente indica la tendencia
                slope = model.coef_[0]

                # Determinar tendencia basada en la pendiente
                # Ajustar umbrales según sea necesario
                if slope > 0.5: # Tendencia al alza significativa
                    trend = 'up'
                elif slope < -0.5: # Tendencia a la baja significativa
                    trend = 'down'
                else: # Tendencia relativamente estable
                    trend = 'stable'

                predictions[skill] = {
                    'trend': trend,
                    'slope': round(slope, 2), # Guardar pendiente para info adicional
                    'total_occurrences': int(skill_data.sum()) # Info útil
                }
                # print(f"  -> Skill: {skill}, Trend: {trend}, Slope: {slope:.2f}, Total: {skill_data.sum()}")

            except Exception as e_reg:
                print(f"Error durante la regresión para la habilidad '{skill}': {e_reg}")

        print(f"Análisis de tendencias completado. Predicciones generadas para {len(predictions)} habilidades.")
        return predictions

    except Exception as e:
        print(f"Error general durante la predicción de tendencias de habilidades: {e}")
        # Considerar logging más detallado
        return {}