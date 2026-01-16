from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db.models import Q, Max, F, Subquery, OuterRef, Count, Value # AGREGAR IMPORTS NECESARIOS
from django.db.models.functions import Coalesce
from django.utils import timezone
from .models import Chat, Mensaje

from .serializers import ChatListSerializer # <--- ¡Nuevo Serializador!

# 🟢 SOLUCIÓN: IMPORTAR EL MÓDULO DE MODELOS DE DJANGO
from django.db import models # <--- ¡AÑADE ESTA LÍNEA!

# Para notificar por WebSocket desde REST API
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# --- VISTA PARA OBTENER LA LISTA DE CHATS ---
@api_view(['GET'])  # Esta vista solo acepta peticiones GET
@permission_classes([IsAuthenticated])  # ¡SOLO usuarios logueados pueden ver!
def obtener_lista_chats(request):
    """
    Devuelve la lista de chats activos del usuario, con el último mensaje y conteo de no leídos.
    """
    user = request.user

    # Subquery OPTIMIZADA para obtener los datos del último mensaje (contenido y fechaHora)
    # ⚠️ Esto es un truco para pasar el objeto completo del último mensaje al serializador:
    ultimo_mensaje_subquery = Mensaje.objects.filter(
        chat=OuterRef('pk')
    ).order_by('-fechaHora').values('contenido', 'fechaHora')[:1]


    # 1. Filtra los chats del usuario activo
    chats = Chat.objects.filter(
        activo=True
    ).filter(
        Q(match__usuarioA=user) | Q(match__usuarioB=user)
    )
    
    # 2. Anota los campos agregados (latest_message_data y no_leidos)
    chats_anotados = chats.annotate(
        # Anotamos el conteo de mensajes no leídos (no enviados por mí)
        no_leidos=Count(
        'mensajes', 
        # Aseguramos que se cumpla: (no_leido=False) Y NO (remitente=user)
        filter=Q(mensajes__leido=False) & ~Q(mensajes__remitente=user)
    ),
        
        # Anotamos el contenido y fecha del último mensaje
        latest_message_contenido=Subquery(ultimo_mensaje_subquery.values('contenido')),
        latest_message_fechaHora=Subquery(ultimo_mensaje_subquery.values('fechaHora')),
        
        # ⚠️ Paso clave: Creamos un campo virtual que el serializador usará
        # para emular el objeto 'UltimoMensajeSerializer'.
        # Es un diccionario que agrupa los campos anotados:
        latest_message_data=Value({}, output_field=models.JSONField()) 
        # NOTA: El serializer ChatListSerializer deberá rellenar latest_message_data
        # con los valores de latest_message_contenido y latest_message_fechaHora.
        # En DRF es más fácil usar SerializerMethodField, pero para mantener la estructura, 
        # usamos el truco de pasar el objeto como un diccionario.
        # MANTENDRÉ la implementación simple en el serializer para usar los campos directamente.
        
    ).order_by(
        # 3. Ordena por la fecha del último mensaje (los NULL van al final)
        F('latest_message_fechaHora').desc(nulls_last=True)
    ).select_related(
        # 4. Optimizaciones N+1: Cargamos Match y los dos Usuarios del Match en una sola consulta
        'match__usuarioA', 
        'match__usuarioB'
    )
    
    # Adaptación para que el serializador funcione con los campos anotados:
    # Creamos manualmente el diccionario que el UltimoMensajeSerializer esperaría
    for chat in chats_anotados:
        if chat.latest_message_contenido:
             # Creamos la estructura esperada por UltimoMensajeSerializer
            chat.latest_message_data = {
                'contenido': chat.latest_message_contenido,
                'fechaHora': chat.latest_message_fechaHora
            }
        else:
            chat.latest_message_data = None


    # 5. Serializamos y devolvemos la data
    serializer = ChatListSerializer(
        chats_anotados, many=True, context={'request': request}
    )

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_mensajes_chat(request, chat_id):
    """
    Devuelve todos los mensajes de un chat específico.
    """
    user = request.user
    try:
        # 1. Buscamos el chat, optimizando para acceder al Match y sus usuarios
        chat = Chat.objects.select_related(
            'match',
            'match__usuarioA',
            'match__usuarioB',
        ).get(
            id=chat_id,
            activo=True,  # Solo chats activos
        )

        # 2. VALIDACIÓN DE SEGURIDAD (¡Importante!)
        # Verificamos que el usuario que hace la petición (request.user)
        # realmente pertenezca a este chat (sea usuarioA o usuarioB del match)
        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response(
                {"error": "No tienes permiso para ver este chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 3. MARCAR MENSAJES COMO LEÍDOS (los que no son del usuario actual)
        Mensaje.objects.filter(
            chat=chat,
            leido=False,
            remitente__isnull=False,  # <--- ASEGURAMOS QUE EL REMITENTE NO ES NULL
        ).exclude(
            remitente=user,  # Excluimos los mensajes que el propio usuario envió
        ).update(leido=True)

        # 4. Obtenemos los mensajes optimizando también el remitente
        mensajes = (
            Mensaje.objects.select_related('remitente')
            .filter(chat_id=chat.id)
            .order_by('fechaHora')
        )

        # 5. Los convertimos a un formato JSON simple para enviar al frontend
        data = []
        for m in mensajes:
            # Toleramos problemas con el remitente/email para evitar 500
            try:
                remitente_email = m.remitente.email if m.remitente else "Sistema"
            except Exception:
                remitente_email = "Sistema"

            try:
                fecha_dt = timezone.localtime(m.fechaHora) if m.fechaHora else None
                fecha_str = fecha_dt.strftime("%Y-%m-%d %H:%M:%S") if fecha_dt else ""
            except Exception:
                fecha_str = ""

            data.append(
                {
                    "id": m.id,
                    "contenido": m.contenido,
                    "remitente_email": remitente_email,
                    "es_mio": m.remitente_id == user.id,
                    "fecha": fecha_str,
                    "leido": bool(getattr(m, "leido", False)),
                }
            )

        return Response(data, status=status.HTTP_200_OK)

    except Chat.DoesNotExist:
        return Response(
            {"error": "Chat no encontrado."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        # Útil loguear el error 'e' en el servidor para debugging
        print(f"ERROR 500 AL CARGAR MENSAJES (FALLA INTERNA): {e}")
        return Response(
            {"error": "Error interno al cargar el historial del chat."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_mensaje(request, chat_id):
    """
    Endpoint REST para enviar mensajes cuando el WebSocket no está disponible.
    Permite enviar mensajes incluso si el otro usuario no está conectado.
    """
    user = request.user
    
    # Validar que se envió el contenido del mensaje
    contenido = request.data.get('contenido', '').strip()
    if not contenido:
        return Response(
            {"error": "El contenido del mensaje no puede estar vacío."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # 1. Buscar el chat y validar permisos
        chat = Chat.objects.select_related(
            'match', 'match__usuarioA', 'match__usuarioB'
        ).get(id=chat_id, activo=True)

        # 2. Validar que el usuario pertenece al chat
        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response(
                {"error": "No tienes permiso para enviar mensajes en este chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 3. Crear el mensaje
        mensaje = Mensaje.objects.create(
            chat=chat,
            remitente=user,
            contenido=contenido
        )

        # 4. Notificar por WebSocket si hay usuarios conectados
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                room_group_name = f'chat_{chat_id}'
                try:
                    remitente_email = user.email
                except Exception:
                    remitente_email = "Sistema"

                try:
                    fecha_dt = timezone.localtime(mensaje.fechaHora) if mensaje.fechaHora else None
                    fecha_str = fecha_dt.strftime("%Y-%m-%d %H:%M:%S") if fecha_dt else ""
                except Exception:
                    fecha_str = ""

                # Enviar el mensaje al grupo del chat para que los usuarios conectados lo reciban
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'chat_message',
                        'message_data': {
                            'id': mensaje.id,
                            'contenido': mensaje.contenido,
                            'remitente_email': remitente_email,
                            'es_mio': False,  # Se ajustará en el frontend según el usuario
                            'fecha': fecha_str,
                            'leido': False,
                        }
                    }
                )
        except Exception as e:
            # Si falla la notificación WebSocket, no es crítico, el mensaje ya está guardado
            print(f"Advertencia: No se pudo notificar por WebSocket: {e}")

        # 5. Formatear la respuesta similar al formato del WebSocket
        try:
            remitente_email = user.email
        except Exception:
            remitente_email = "Sistema"

        try:
            fecha_dt = timezone.localtime(mensaje.fechaHora) if mensaje.fechaHora else None
            fecha_str = fecha_dt.strftime("%Y-%m-%d %H:%M:%S") if fecha_dt else ""
        except Exception:
            fecha_str = ""

        return Response(
            {
                "id": mensaje.id,
                "contenido": mensaje.contenido,
                "remitente_email": remitente_email,
                "es_mio": True,
                "fecha": fecha_str,
                "leido": False,  # Recién enviado, aún no leído
            },
            status=status.HTTP_201_CREATED
        )

    except Chat.DoesNotExist:
        return Response(
            {"error": "Chat no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"ERROR al enviar mensaje en chat {chat_id}: {e}")
        return Response(
            {"error": "Error interno al enviar el mensaje."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def vaciar_chat(request, chat_id):
    user = request.user
    try:
        chat = Chat.objects.select_related(
            'match', 'match__usuarioA', 'match__usuarioB'
        ).get(id=chat_id, activo=True)

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response({"error": "No tienes permiso para esta acción."}, status=status.HTTP_403_FORBIDDEN)

        deleted_count, _ = Mensaje.objects.filter(chat_id=chat.id).delete()
        return Response({"eliminados": deleted_count}, status=status.HTTP_200_OK)

    except Chat.DoesNotExist:
        return Response({"error": "Chat no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"ERROR al vaciar chat {chat_id}: {e}")
        return Response({"error": "Error interno al vaciar el chat."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# ENDPOINTS PARA GESTIONAR EL ESTADO "CHAT ABIERTO"
# Esto evita que se envíen notificaciones cuando el usuario
# está activamente viendo el chat.
# ============================================================
from django.core.cache import cache

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def abrir_chat(request, chat_id):
    """
    Marca que el usuario tiene el chat abierto.
    Mientras esté abierto, no recibirá notificaciones de ese chat.
    """
    user = request.user
    try:
        # Validar que el chat existe y el usuario pertenece a él
        chat = Chat.objects.select_related(
            'match', 'match__usuarioA', 'match__usuarioB'
        ).get(id=chat_id, activo=True)

        if chat.match.usuarioA != user and chat.match.usuarioB != user:
            return Response(
                {"error": "No tienes permiso para este chat."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Guardar en cache que el usuario tiene este chat abierto
        # Expira en 30 minutos por si el usuario no cierra correctamente
        cache_key = f"chat_abierto_usuario_{user.id}"
        cache.set(cache_key, chat.id, timeout=1800)  # 30 minutos
        
        print(f"✅ Usuario {user.id} abrió chat {chat.id}")
        
        return Response(
            {"message": "Chat marcado como abierto", "chat_id": chat.id},
            status=status.HTTP_200_OK
        )

    except Chat.DoesNotExist:
        return Response(
            {"error": "Chat no encontrado."},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"ERROR al marcar chat {chat_id} como abierto: {e}")
        return Response(
            {"error": "Error interno."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cerrar_chat(request, chat_id):
    """
    Marca que el usuario cerró el chat.
    Volverá a recibir notificaciones de ese chat.
    """
    user = request.user
    try:
        # No es necesario validar permisos aquí, simplemente limpiamos el cache
        cache_key = f"chat_abierto_usuario_{user.id}"
        current_chat_id = cache.get(cache_key)
        
        # Solo limpiar si el chat que se cierra es el mismo que está abierto
        if current_chat_id == int(chat_id):
            cache.delete(cache_key)
            print(f"✅ Usuario {user.id} cerró chat {chat_id}")
        
        return Response(
            {"message": "Chat marcado como cerrado"},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        print(f"ERROR al marcar chat {chat_id} como cerrado: {e}")
        return Response(
            {"error": "Error interno."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

