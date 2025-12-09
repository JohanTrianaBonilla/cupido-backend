# --- cupido-backend/apps/chat_app/middleware.py ---

from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from urllib.parse import parse_qs

User = get_user_model() # Obtiene tu modelo 'Usuario'

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Función asíncrona para validar el token y obtener el usuario.
    """
    try:
        # 1. Validar el token y obtener el ID de usuario
        token = AccessToken(token_key)
        # El claim en el token es 'usuario_id' según SIMPLE_JWT settings
        user_id = token.get('usuario_id') or token.get('user_id')
        
        if not user_id:
            return AnonymousUser()
        
        # 2. Obtener el usuario desde la base de datos usando usuario_id
        return User.objects.get(usuario_id=user_id)
        
    except (TokenError, User.DoesNotExist, KeyError) as e:
        # 3. Si el token es inválido o el usuario no existe,
        # devolvemos un "Usuario Anónimo".
        print(f"Error validando token WS: {e}")
        return AnonymousUser()

class JwtAuthMiddleware:
    """
    Middleware de autenticación JWT para Channels.
    Lee el token de la query string (ej: ?token=...).
    """
    def __init__(self, inner):
        # 'inner' es el siguiente paso en el proceso (en nuestro caso, el URLRouter)
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # 'scope' es como la 'request' de los WebSockets
        
        # 1. Busca la 'query_string' (la parte ?token=...)
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        if token_key:
            # 2. Si encontramos un token, obtenemos el usuario
            scope['user'] = await get_user_from_token(token_key)
        else:
            # 3. Si no hay token, el usuario es Anónimo
            scope['user'] = AnonymousUser()
        
        # 4. Continuamos con el siguiente paso (pasamos el 'scope' actualizado)
        return await self.inner(scope, receive, send)