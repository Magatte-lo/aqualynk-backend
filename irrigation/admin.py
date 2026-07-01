"""
Admin Django
"""
from django.contrib import admin
from .models import SystemState, SensorReading


@admin.register(SystemState)
class SystemStateAdmin(admin.ModelAdmin):
    list_display = ['id', 'humidity', 'temperature', 'pump_status', 'mode', 'esp32_connected', 'last_update']


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'humidity', 'temperature']
    list_filter = ['timestamp']