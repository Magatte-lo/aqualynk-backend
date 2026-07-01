"""
Modèles Aqualynk
"""
from django.db import models
from django.contrib.auth.models import User


class SystemState(models.Model):
    """
    État actuel du système d'irrigation (pattern Singleton).
    Un seul enregistrement existe en base de données.
    """
    humidity = models.FloatField(default=0)
    temperature = models.FloatField(default=0)
    pump_status = models.BooleanField(default=False)
    esp32_connected = models.BooleanField(default=False)
    mode = models.CharField(
        max_length=10,
        choices=[('auto', 'Auto'), ('manual', 'Manuel')],
        default='auto'
    )

    # === DOUBLE SEUIL ===
    threshold_min = models.FloatField(
        default=30,
        help_text="Seuil minimum d'humidité — la pompe se déclenche en dessous"
    )
    threshold_max = models.FloatField(
        default=60,
        help_text="Seuil maximum d'humidité — la pompe s'arrête au dessus"
    )

    # === LOCALISATION POUR API MÉTÉO ===
    city = models.CharField(
        max_length=100,
        default="Dakar",
        help_text="Ville pour la météo"
    )
    latitude = models.FloatField(default=14.6928)   # Dakar
    longitude = models.FloatField(default=-17.4467)  # Dakar

    # === MÉTÉO ===
    rain_expected = models.BooleanField(default=False)

    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State - {self.humidity}% - Pump {self.pump_status}"

    @classmethod
    def get_instance(cls):
        """
        Pattern Singleton : retourne toujours le même état système.
        Si aucun n'existe, en crée un nouveau avec id=1.
        """
        state, created = cls.objects.get_or_create(id=1)
        return state


class SensorReading(models.Model):
    """
    Historique des relevés capteurs (envoyés par l'ESP32).
    Chaque appel à update_sensor crée une nouvelle ligne.
    """
    humidity = models.FloatField()
    temperature = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - H:{self.humidity}% T:{self.temperature}°C"