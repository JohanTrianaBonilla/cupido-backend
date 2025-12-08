# notificacion_app/serializers.py
from rest_framework import serializers
from .models import notificacion

class NotificacionSerializer(serializers.ModelSerializer):
    usuario_destino = serializers.StringRelatedField() 
    chat_id = serializers.SerializerMethodField()

    class Meta:
        model = notificacion
        fields = ('id', 'tipo', 'mensaje', 'fecha_envio', 'estado', 'usuario_destino', 'chat_id')
        read_only_fields = ('id', 'fecha_envio', 'chat_id')
    

    def get_usuario_origen(self, obj):
        """Retorna el ID del usuario origen o None si no existe"""
        return obj.usuario_origen_id if obj.usuario_origen_id else Nonev

    def get_chat_id(self, obj):
        """Retorna el ID del chat relacionado o None si no existe"""
        return obj.chat_relacionado_id if obj.chat_relacionado_id else None
