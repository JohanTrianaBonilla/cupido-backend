# apps/auth_app/serializers/usuario_serializer.py

from rest_framework import serializers
from apps.auth_app.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializa los datos básicos del usuario para respuestas JSON.
    Se usa en LoginView, SessionInfoView y cualquier endpoint que devuelva info del usuario.
    """
    class Meta:
        model = Usuario
        fields = ["usuario_id", "nombres", "apellidos", "email", "is_superuser"]
