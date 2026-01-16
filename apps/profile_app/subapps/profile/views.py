from rest_framework import generics, permissions, status,viewsets
from rest_framework.response import Response
from apps.profile_app.subapps.profile.models import Perfil
from apps.profile_app.subapps.profile.serializer import *
from apps.profile_app.subapps.profile.utils import get_or_create_user_profile


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Permite al usuario autenticado obtener o actualizar su propio perfil.
    """
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]  # permissions.IsAuthenticated para exigir token de autenticacion

    def get_object(self):
        # Crea el perfil si no existe
        return get_or_create_user_profile(self.request.user)

    def patch(self, request, *args, **kwargs):
        perfil = self.get_object()
        serializer = self.get_serializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        perfil = self.get_object()
        serializer = self.get_serializer(perfil)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class PerfilDetailView(generics.RetrieveAPIView):
    """
    Permite obtener información de un perfil específico por ID.
    Ideal para mostrar el perfil de otro usuario.
    """
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [permissions.AllowAny]  # puedes cambiar a IsAuthenticated si prefieres

    def get_object(self):
        pk = self.kwargs.get('pk')
        # 1. Intentar buscar por usuario_id (prioridad para OtherProfilePage)
        try:
            return Perfil.objects.get(usuario__usuario_id=pk)
        except (Perfil.DoesNotExist, ValueError):
            # 2. Fallback: Buscar por perfil_id (comportamiento estándar)
            # ValueError captura casos donde pk no es un entero válido para una de las búsquedas
            return super().get_object()

    def get(self, request, *args, **kwargs):
        perfil = self.get_object()
        
        # 1. Serializar Perfil
        perfil_data = self.get_serializer(perfil).data
        
        # 2. Serializar Usuario
        # Usamos el usuario asociado al perfil
        usuario = perfil.usuario
        if usuario:
            from apps.auth_app.serializers.user_get_serializer import UserGetSerializer
            user_data = UserGetSerializer(usuario).data
        else:
            user_data = None
            
        # 3. Serializar Imágenes
        # Las imágenes están asociadas al usuario
        imagenes_data = []
        if usuario:
            from apps.profile_app.subapps.imageUpload.models import Imagen
            from apps.profile_app.subapps.imageUpload.serializers import ImagenSerializer
            # Obtener imágenes del usuario
            imagenes = Imagen.objects.filter(usuario=usuario)
            imagenes_data = ImagenSerializer(imagenes, many=True).data

        # 4. Construir respuesta final
        response_data = {
            **perfil_data,        # Datos del perfil en la raíz (para compatibilidad)
            "usuario": user_data, # Datos del usuario anidados
            "images": imagenes_data # Lista de imágenes
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class PerfilAdminUpdateView(generics.RetrieveUpdateAPIView):
    """
    Permite a un administrador ver o actualizar un perfil específico por ID.
    """
    queryset = Perfil.objects.all()
    serializer_class = PerfilSerializer
    permission_classes = [permissions.AllowAny]  # permissions.IsAdminUser para exigir token de autenticacion de administrador

    def patch(self, request, *args, **kwargs):
        perfil = self.get_object()
        serializer = self.get_serializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProgramaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Programa.objects.all()
    serializer_class = ProgramaSerializer


class UbicacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ubicacion.objects.all()
    serializer_class = UbicacionSerializer