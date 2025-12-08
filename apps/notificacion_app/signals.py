# notificacion_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.cache import cache
import logging

from .models import notificacion
from .utils import enviar_a_grupo

logger = logging.getLogger(__name__)

# ================================
# IMPORTS EXTERNOS (otras apps)
# ================================
try:
    from detallesLike.models import DetalleLike
except ImportError:
    DetalleLike = None

try:
    from match.models import Match
except ImportError:
    Match = None

try:
    from apps.chat_app.models import Mensaje
except ImportError:
    Mensaje = None

# --------------------------------------------------------
# Notificación cuando alguien da LIKE
# --------------------------------------------------------
if DetalleLike is not None:
    @receiver(post_save, sender=DetalleLike)
    def crear_notificacion_desde_like(sender, instance, created, **kwargs):
        if not created:
            return

        usuario_emisor = getattr(instance, 'usuarioEmisor', None)
        usuario_receptor = getattr(instance, 'usuarioReceptor', None)

        if usuario_receptor is None or usuario_emisor is None:
            return

        nombre_emisor = getattr(usuario_emisor, 'username', 'Alguien')
        mensaje = f"{nombre_emisor} te dio like"

        notif = notificacion.objects.create(
            tipo=notificacion.EVENT_LIKE,
            mensaje=mensaje,
            usuario_destino=usuario_receptor,
        )

        payload = {
            "id": notif.id,
            "tipo": notif.tipo,
            "mensaje": notif.mensaje,
            "fecha_envio": notif.fecha_envio.isoformat(),
            "from_user_id": usuario_emisor.id,
            "from_username": usuario_emisor.username,
        }

        transaction.on_commit(
            lambda: enviar_a_grupo(
                f"user_{usuario_receptor.id}",
                "notification_message",
                payload
            )
        )

# --------------------------------------------------------
# Notificación cuando hay MATCH
# --------------------------------------------------------
if Match is not None:
    @receiver(post_save, sender=Match)
    def crear_notificacion_desde_match(sender, instance, created, **kwargs):
        if not created:
            return

        logger.info(f"Signal match activado para Match id={instance.id}")

        user_a = instance.usuarioA
        user_b = instance.usuarioB

        # Obtener el chat asociado
        try:
            chat = instance.chat
        except:
            chat = None

        chat_id = chat.id if chat else None

        # Usuario A
        try:
            mensaje_a = f"Match. Tienes un nuevo match con {user_b.nombres if hasattr(user_b, 'nombres') else user_b.username}"
            notif_a = notificacion.objects.create(
                tipo=notificacion.EVENT_MATCH,
                mensaje=mensaje_a,
                usuario_destino=user_a
            )

            payload_a = {
                "id": notif_a.id,
                "tipo": notif_a.tipo,
                "mensaje": notif_a.mensaje,
                "fecha_envio": notif_a.fecha_envio.isoformat(),
                "usuario_match_id": user_b.id,
                "chat_id": chat_id,
            }

            transaction.on_commit(
                lambda: enviar_a_grupo(
                    f"user_{user_a.id}",
                    "notification_message",
                    payload_a
                )
            )
        except Exception as e:
            logger.error(f"Error al crear notificación de match para usuario A: {e}")

        # Usuario B
        try:
            mensaje_b = f"Match. Tienes un nuevo match con {user_a.nombres if hasattr(user_a, 'nombres') else user_a.username}"
            notif_b = notificacion.objects.create(
                tipo=notificacion.EVENT_MATCH,
                mensaje=mensaje_b,
                usuario_destino=user_b
            )

            payload_b = {
                "id": notif_b.id,
                "tipo": notif_b.tipo,
                "mensaje": notif_b.mensaje,
                "fecha_envio": notif_b.fecha_envio.isoformat(),
                "usuario_match_id": user_a.id,
                "chat_id": chat_id,
            }

            transaction.on_commit(
                lambda: enviar_a_grupo(
                    f"user_{user_b.id}",
                    "notification_message",
                    payload_b
                )
            )
        except Exception as e:
            logger.error(f"Error al crear notificación de match para usuario B: {e}")

# --------------------------------------------------------
# Notificación cuando llega un MENSAJE de chat
# --------------------------------------------------------
if Mensaje is not None:
    @receiver(post_save, sender=Mensaje)
    def notificar_mensaje_chat(sender, instance, created, **kwargs):
        if not created:
            return

        mensaje = instance
        chat = mensaje.chat
        remitente = mensaje.remitente

        usuarioA = chat.match.usuarioA
        usuarioB = chat.match.usuarioB

        # Identificar receptor
        receptor = usuarioB if remitente == usuarioA else usuarioA

        if receptor is None:
            return

        # Evitar notificación si el receptor tiene el chat abierto
        cache_key = f"chat_abierto_usuario_{receptor.id}"
        chat_abierto_id = cache.get(cache_key)

        if chat_abierto_id == chat.id:
            return

        texto = f"{remitente.nombres} te envió un mensaje"
        notif = notificacion.objects.create(
            tipo=notificacion.EVENT_CHAT,
            mensaje=texto,
            usuario_destino=receptor,
        )

        payload = {
            "id": notif.id,
            "tipo": notif.tipo,
            "mensaje": notif.mensaje,
            "fecha_envio": notif.fecha_envio.isoformat(),
        }

        transaction.on_commit(
            lambda: enviar_a_grupo(
                f"user_{receptor.id}",
                "notification_message",
                payload
            )
        )
