from django.urls import path
from . import views

urlpatterns = [
    # API Endpoint para obtener el historial:
    # GET /api/v1/chat/1/mensajes/
    path('<int:chat_id>/mensajes/', views.obtener_mensajes_chat, name='obtener-mensajes'),
    # API Endpoint para enviar mensajes (fallback cuando WebSocket no está disponible):
    # POST /api/v1/chat/1/enviar/
    path('<int:chat_id>/enviar/', views.enviar_mensaje, name='enviar-mensaje'),
    path('<int:chat_id>/vaciar/', views.vaciar_chat, name='vaciar-chat'),
    
    # Endpoints para gestionar estado "chat abierto" (evita notificaciones duplicadas)
    # POST /api/v1/chat/1/abrir/  - Marca que el usuario tiene el chat abierto
    path('<int:chat_id>/abrir/', views.abrir_chat, name='abrir-chat'),
    # POST /api/v1/chat/1/cerrar/  - Marca que el usuario cerró el chat
    path('<int:chat_id>/cerrar/', views.cerrar_chat, name='cerrar-chat'),

    path('', views.obtener_lista_chats, name='obtener_lista_chats'),
]
