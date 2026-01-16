from django.urls import re_path

# Importamos el archivo "consumers" que crearemos en el siguiente paso
from . import consumers 

# Esta es la lista de URLs de WebSocket
websocket_urlpatterns = [
    # Esta es la URL que tu React usará para conectarse.
    # Donde 123 es el ID del chat.
    re_path(r'^ws/chat/(?P<chat_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
