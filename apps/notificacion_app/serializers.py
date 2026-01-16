# notificacion_app/serializers.py
from rest_framework import serializers
from .models import notificacion

class NotificacionSerializer(serializers.ModelSerializer):
    usuario_destino = serializers.StringRelatedField()
    chat_id = serializers.SerializerMethodField()
    from_user_id = serializers.SerializerMethodField()
    usuario_match_id = serializers.SerializerMethodField()

    class Meta:
        model = notificacion
        fields = ('id', 'tipo', 'mensaje', 'fecha_envio', 'estado', 'usuario_destino', 'chat_id', 'from_user_id', 'usuario_match_id')
        read_only_fields = ('id', 'fecha_envio', 'chat_id', 'from_user_id', 'usuario_match_id')
    
    def get_chat_id(self, obj):
        """Retorna el ID del chat relacionado o None si no existe"""
        return obj.chat_relacionado_id if obj.chat_relacionado_id else None

    def get_from_user_id(self, obj):
        """Retorna el ID del usuario que originó la notificación"""
        return obj.usuario_origen_id if obj.usuario_origen_id else None

    def get_usuario_match_id(self, obj):
        """
        Para notificaciones de MATCH, retorna el ID del otro usuario.
        En este modelo, usuario_origen es quien disparó la notificación (el otro usuario).
        """
        if obj.tipo == notificacion.EVENT_MATCH:
            return obj.usuario_origen_id
        return None
