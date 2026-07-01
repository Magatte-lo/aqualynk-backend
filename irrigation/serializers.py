"""
Serializers Aqualynk
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import SystemState


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        return user


class SystemStateSerializer(serializers.ModelSerializer):
    """Serializer de l'état système"""
    class Meta:
        model = SystemState
        fields = [
            'humidity', 'temperature', 'pump_status',
            'esp32_connected', 'mode', 'threshold', 'last_update'
        ]