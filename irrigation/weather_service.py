import requests
from datetime import datetime

def get_weather_data(latitude=14.6928, longitude=-17.4467):
    """
    Récupère la température actuelle et la prévision de pluie via Open-Meteo
    Pas de clé API requise !
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,precipitation",
            "hourly": "precipitation_probability",
            "forecast_days": 1,
            "timezone": "auto",
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Données actuelles
            current_temp = data["current"]["temperature_2m"]
            current_humidity_air = data["current"]["relative_humidity_2m"]
            current_precip = data["current"]["precipitation"]
            
            # Prévision pluie : est-ce qu'il va pleuvoir dans les 3 prochaines heures ?
            rain_probabilities = data["hourly"]["precipitation_probability"][:3]
            rain_expected = any(prob > 60 for prob in rain_probabilities)
            
            return {
                "success": True,
                "temperature": current_temp,
                "humidity_air": current_humidity_air,
                "is_raining": current_precip > 0,
                "rain_expected": rain_expected,
                "rain_probabilities_3h": rain_probabilities,
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}