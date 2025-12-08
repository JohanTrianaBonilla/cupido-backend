# notificacion_app/models.py
from django.db import models
from django.conf import settings

# settings.AUTH_USER_MODEL puede ser 'auth.User' o tu custom user model (cadena).
# Usamos la cadena a través de settings en los ForeignKey para máxima compatibilidad.


class notificacion(models.Model):
    EVENT_LIKE = 'like'
    EVENT_MATCH = 'match'
    EVENT_CHAT = 'chat'
    EVENT_REPORT = "Reporte"
    EVENT_CHOICES = [
        (EVENT_LIKE, 'Like'),
        (EVENT_MATCH, 'Match'),
        (EVENT_CHAT, "Chat"),
        (EVENT_REPORT, "Reporte"),
    ]

    STATUS_PENDING = 'pendiente'
    STATUS_SENT = 'enviado'
    STATUS_READ = 'leido'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendiente'),
        (STATUS_SENT, 'Enviado'),
        (STATUS_READ, 'Leido'),
    ]

    tipo = models.CharField(max_length=20, choices=EVENT_CHOICES)
    mensaje = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)

    usuario_destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    
    # Campo opcional para relacionar notificación con un chat específico
    # Esto permite actualizar la notificación existente en lugar de crear duplicados
    chat_relacionado = models.ForeignKey(
        'chat_app.Chat',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notificaciones'
    )

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fecha_envio']

#cambiar aca por el tipo correcto si es username o nombre
    def __str__(self):
        return f"Notificacion(to={self.usuario_destino.username}, tipo={self.tipo})"

