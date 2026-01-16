# apps/match_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Match

logger = logging.getLogger(__name__)

# Importar Chat de forma segura
try:
    from apps.chat_app.models import Chat
except ImportError as e:
    logger.warning(f"No se pudo importar Chat: {e}")
    Chat = None


@receiver(post_save, sender=Match)
def crear_chat_automatico(sender, instance, created, **kwargs):
    """
    Crea automáticamente un Chat cuando se crea un nuevo Match.
    
    Flujo:
    1. Usuario A da LIKE a Usuario B
    2. Si Usuario B ya había dado LIKE a Usuario A -> Match mutuo
    3. Se crea el Match (en like_app/services.py)
    4. Este signal detecta el nuevo Match y crea el Chat automáticamente
    """
    if not created:
        return
    
    if Chat is None:
        logger.error("No se puede crear Chat: modelo Chat no disponible")
        return
    
    logger.info(f"Signal: Creando Chat automático para Match id={instance.id}")
    
    try:
        # Verificar que no exista ya un Chat para este Match
        if hasattr(instance, 'chat'):
            logger.info(f"Ya existe un Chat para Match id={instance.id}")
            return
        
        # Crear el Chat
        chat = Chat.objects.create(
            match=instance,
            activo=True
        )
        
        logger.info(f"Chat id={chat.id} creado automáticamente para Match id={instance.id}")
        
    except Exception as e:
        logger.error(f"Error al crear Chat automático: {e}")
