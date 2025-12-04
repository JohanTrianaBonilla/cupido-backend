# config/routing.py
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import apps.notificacion_app.routing
import apps.chat_app.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            apps.notificacion_app.routing.websocket_urlpatterns +
            apps.chat_app.routing.websocket_urlpatterns  
        )
    ),
})