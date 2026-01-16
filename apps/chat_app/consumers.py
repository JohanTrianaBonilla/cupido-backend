import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Chat, Mensaje

# Ya no necesitamos importar User ni Match para crear falsos
# Usaremos el usuario real que viene del Token.

@database_sync_to_async
def save_message(chat_id, user, message_content):
    """
    Guarda el mensaje usando el usuario REAL.
    """
    try:
        # 1. Buscar el Chat
        # (Asumimos que el chat ya existe porque hubo un match previo)
        # Si quieres ser estricto, aquí deberías validar que 'user' 
        # sea parte de ese chat (usuarioA o usuarioB).
        chat_obj = Chat.objects.get(id=chat_id)
        
        if chat_obj.match.usuarioA != user and chat_obj.match.usuarioB != user:
            print(f"ERROR: El usuario {user} no pertenece al chat {chat_id}")
            return None # El usuario no pertenece a este chat

        # 2. Crear el mensaje con el usuario REAL como remitente
        mensaje = Mensaje.objects.create(
            chat=chat_obj,
            remitente=user, 
            contenido=message_content
        )
        return mensaje
        
    except Chat.DoesNotExist:
        print(f"ERROR: El chat {chat_id} no existe en la BD.")
        return None


@database_sync_to_async
def touch_user_last_login(user):
    """
    Actualiza last_login del usuario para aproximar su 'última vez en línea'.
    """
    try:
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
    except Exception as e:
        print(f"ERROR actualizando last_login para {user}: {e}")
    except Exception as e:
        print(f"ERROR AL GUARDAR: {e}")
        return None


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # --- 1. SEGURIDAD: VERIFICAR USUARIO ---
        self.user = self.scope['user']

        if self.user.is_anonymous:
            # Si el guardia (middleware) no encontró un token válido,
            # rechazamos la conexión inmediatamente.
            print("Conexión rechazada: Usuario anónimo o Token inválido.")
            await self.close(code=4003)
            return

        # Si el usuario es real, seguimos...
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'

        # Marcamos al usuario como recientemente activo
        await touch_user_last_login(self.user)

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print(f"¡Usuario {self.user.email} conectado al chat {self.chat_id}!")


    async def disconnect(self, close_code):
        # Solo intentamos salir del grupo si llegamos a entrar
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        # Al desconectarse, actualizamos también su última vez en línea
        if not self.user.is_anonymous:
            await touch_user_last_login(self.user)
            print(f"Usuario {self.user.email} desconectado (código: {close_code})")


    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Verificar nuevamente que tengamos usuario
        if self.user.is_anonymous:
            return

        # --- 2. GUARDAR USANDO USUARIO REAL ---
        # Pasamos 'self.user' a la función de guardado
        mensaje_obj = await save_message(self.chat_id, self.user, message)

        if mensaje_obj:
            # ¡AHORA ENVIAMOS EL OBJETO COMPLETO!
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message', # Llama a la función 'chat_message'
                    'message_data': {
                        'id': mensaje_obj.id,
                        'contenido': mensaje_obj.contenido,
                        'remitente_email': self.user.email,
                        'es_mio': True, # (Se ajustará en el frontend)
                        'fecha': mensaje_obj.fechaHora.strftime("%Y-%m-%d %H:%M:%S"),
                        # Nuevo: por defecto, al crear el mensaje aún no está leído
                        'leido': False,
                    }
                }
            )

    # ESTA FUNCIÓN AHORA REENVÍA EL OBJETO COMPLETO
    async def chat_message(self, event):
        message_data = event['message_data']
        
        # Ajustamos 'es_mio' para CADA usuario que recibe el mensaje
        # Si el email del remitente es el mío, 'es_mio' es true
        message_data['es_mio'] = (self.user.email == message_data['remitente_email'])

        await self.send(text_data=json.dumps({
            'message': message_data # Enviamos el objeto completo
        }))