"""
URLs de l'app irrigation
"""
from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),

    # Données capteurs
    path('get_data/', views.get_data, name='get_data'),
    path('update_sensor/', views.update_sensor, name='update_sensor'),  # Pour ESP32

    # Contrôle pompe
    path('get_pump/', views.get_pump, name='get_pump'),
    path('control_pump/', views.control_pump, name='control_pump'),

    path('ai_chat/', views.ai_chat, name='ai_chat'),
]