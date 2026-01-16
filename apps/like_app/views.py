# apps/like_app/views.py (Código final)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError # Para capturar errores del servicio

# IMPORTACIÓN CLAVE: Llama a la lógica de negocio
from .services import process_user_interaction 

class UserInteractionView(APIView):
    """
    Endpoint para registrar una interacción (Like/Dislike).
    La lógica de negocio reside en services.py.
    """
    def post(self, request, format=None):
        try:
            # 1. Extracción de Input
            emisor_id = request.user.usuario_id 
            receptor_id = request.data.get('receptor_id')
            accion = request.data.get('accion', 'LIKE').upper() 
            
            # 2. LLAMADA AL SERVICIO DE LÓGICA (El trabajo pesado)
            result = process_user_interaction(emisor_id, receptor_id, accion)
            
            # 3. Respuesta HTTP (Solo dar formato al resultado del servicio)
            return Response(
                {
                    "match_found": result["match_found"], 
                    "message": result["message"],
                    **({"usuario_match": receptor_id} if result["match_found"] else {}) 
                }, 
                status=result["status_code"]
            )
        
        except ValidationError as e:
            # Captura errores de validación (400 Bad Request)
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            # Captura errores internos del servicio (500 Internal Server Error)
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)