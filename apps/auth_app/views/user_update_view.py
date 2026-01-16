# apps/auth_app/views/user_update_view.py

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_app.serializers.user_update_serializer import UserUpdateSerializer
from apps.auth_app.utils.user_update import get_user_update_response_data


class UserUpdateView(APIView):
    """
    Gestiona el flujo de actualización de perfil.

    - PATCH: Actualiza el perfil con nombres, apellidos, género, fecha de nacimiento y descripción.
    """

    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UserUpdateSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Refrescar el usuario desde la BD
        user.refresh_from_db()

       
        def patch(self, request):
            logger.info(f"Usuario autenticado: {request.user.email}")

        # Generar respuesta estructurada
        response = get_user_update_response_data(user)
        return Response(response, status=status.HTTP_200_OK)


