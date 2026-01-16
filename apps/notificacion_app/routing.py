from django.urls import re_path
from . import consumers

# Aquí definimos las rutas WebSocket específicas de esta app
websocket_urlpatterns = [
    # Cuando un cliente se conecte al WebSocket en esta URL:
    # ws://<tu_dominio>/ws/notificaciones/
    re_path(r'^ws/notificaciones/(?P<user_id>\d+)/$', consumers.NotificationConsumer.as_asgi()),
]
