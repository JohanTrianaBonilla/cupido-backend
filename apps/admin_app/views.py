"""
Vistas administrativas para gestión de usuarios.
Invocan funciones PostgreSQL existentes en la base de datos.
"""
import logging
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .permissions import IsSuperUser

logger = logging.getLogger(__name__)


class GetUserByEmailView(APIView):
    """
    GET /admin/user-by-email/?email=<email>
    Invoca: obtener_usuario_id_por_email(email)
    Retorna el ID y datos básicos del usuario.
    """
    permission_classes = [IsSuperUser]

    def get(self, request):
        email = request.query_params.get('email', '').strip()
        
        if not email:
            return Response(
                {"error": "El parámetro 'email' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT obtener_usuario_id_por_email(%s)",
                    [email]
                )
                result = cursor.fetchone()
                
                if result and result[0]:
                    usuario_id = result[0]
                    
                    # Obtener datos adicionales del usuario
                    cursor.execute("""
                        SELECT usuario_id, nombres, apellidos, email, estadocuenta, is_superuser
                        FROM usuario
                        WHERE usuario_id = %s
                    """, [usuario_id])
                    user_data = cursor.fetchone()
                    
                    if user_data:
                        return Response({
                            "usuario_id": user_data[0],
                            "nombres": user_data[1],
                            "apellidos": user_data[2],
                            "email": user_data[3],
                            "estadocuenta": user_data[4],
                            "is_superuser": user_data[5],
                        }, status=status.HTTP_200_OK)
                
                return Response(
                    {"error": "Usuario no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Error al buscar usuario por email: {e}")
            return Response(
                {"error": f"Error al buscar usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BanUserView(APIView):
    """
    POST /admin/ban-user/
    Body: { "usuario_id": int, "confirmar": bool }
    Invoca: banear_usuario(usuario_id, confirmar)
    """
    permission_classes = [IsSuperUser]

    def post(self, request):
        usuario_id = request.data.get('usuario_id')
        confirmar = request.data.get('confirmar', False)

        if not usuario_id:
            return Response(
                {"error": "El campo 'usuario_id' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not confirmar:
            return Response(
                {"error": "Debe confirmar la acción estableciendo 'confirmar' en true."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT banear_usuario(%s, %s)",
                    [usuario_id, confirmar]
                )
                result = cursor.fetchone()
                
                logger.info(f"Usuario {usuario_id} baneado por admin {request.user.email}")
                
                return Response({
                    "message": f"Usuario {usuario_id} ha sido baneado exitosamente.",
                    "resultado": result[0] if result else None
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error al banear usuario {usuario_id}: {e}")
            return Response(
                {"error": f"Error al banear usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DeleteUserView(APIView):
    """
    POST /admin/delete-user/
    Body: { "usuario_id": int, "confirmar": bool }
    Invoca: eliminar_usuario(usuario_id, confirmar)
    """
    permission_classes = [IsSuperUser]

    def post(self, request):
        usuario_id = request.data.get('usuario_id')
        confirmar = request.data.get('confirmar', False)

        if not usuario_id:
            return Response(
                {"error": "El campo 'usuario_id' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not confirmar:
            return Response(
                {"error": "Debe confirmar la acción estableciendo 'confirmar' en true."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT eliminar_usuario(%s, %s)",
                    [usuario_id, confirmar]
                )
                result = cursor.fetchone()
                
                logger.info(f"Usuario {usuario_id} eliminado por admin {request.user.email}")
                
                return Response({
                    "message": f"Usuario {usuario_id} ha sido eliminado exitosamente.",
                    "resultado": result[0] if result else None
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error al eliminar usuario {usuario_id}: {e}")
            return Response(
                {"error": f"Error al eliminar usuario: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateGenderPreferenceView(APIView):
    """
    POST /admin/update-gender-pref/
    Body: { "email": str, "genero_preferido": str }
    Invoca: actualizar_genero_preferido(email, genero_preferido)
    """
    permission_classes = [IsSuperUser]

    def post(self, request):
        email = request.data.get('email', '').strip()
        genero_preferido = request.data.get('genero_preferido', '').strip()

        if not email:
            return Response(
                {"error": "El campo 'email' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not genero_preferido:
            return Response(
                {"error": "El campo 'genero_preferido' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT actualizar_genero_preferido(%s, %s)",
                    [email, genero_preferido]
                )
                result = cursor.fetchone()
                
                logger.info(f"Género preferido actualizado para {email} por admin {request.user.email}")
                
                return Response({
                    "message": f"Género preferido actualizado exitosamente para {email}.",
                    "resultado": result[0] if result else None
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error al actualizar género preferido para {email}: {e}")
            return Response(
                {"error": f"Error al actualizar género preferido: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
