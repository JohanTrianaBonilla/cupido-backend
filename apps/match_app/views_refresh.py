"""
Vista para refrescar presigned URLs cuando expiran.

Endpoint: POST /api/v1/match/refresh-images/
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.profile_app.subapps.imageUpload.models import Imagen
from apps.profile_app.subapps.imageUpload.services import generate_presigned_url


class RefreshImageURLsView(APIView):
    """
    Regenera presigned URLs para imágenes específicas.

    Útil cuando las URLs han expirado y el frontend necesita nuevas.

    POST /api/v1/match/refresh-images/
    Body:
    {
        "image_ids": [69, 70, 71]  // IDs de las imágenes a refrescar
    }

    Response:
    {
        "urls": {
            "69": "https://multimedia.cupidocol.com/...",
            "70": "https://multimedia.cupidocol.com/...",
            "71": "https://multimedia.cupidocol.com/..."
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        image_ids = request.data.get('image_ids', [])

        if not image_ids:
            return Response(
                {"detail": "Se requiere el campo 'image_ids'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener imágenes
        imagenes = Imagen.objects.filter(id__in=image_ids)

        # Generar nuevas presigned URLs
        urls = {}
        for img in imagenes:
            if img.imagen:
                presigned_url = generate_presigned_url(
                    img.imagen.name,
                    expiration=3600  # 1 hora
                )
                if presigned_url:
                    urls[str(img.id)] = presigned_url

        return Response({"urls": urls}, status=status.HTTP_200_OK)


class RefreshMatchImagesView(APIView):
    """
    Regenera presigned URLs para imágenes de un perfil específico.

    Más conveniente para el sistema de matching - regenera todas las imágenes
    de un usuario específico.

    POST /api/v1/match/refresh-profile-images/
    Body:
    {
        "usuario_id": 124
    }

    Response:
    {
        "main_image": "https://...",
        "secondary_images": ["https://...", "https://..."]
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usuario_id = request.data.get('usuario_id')

        if not usuario_id:
            return Response(
                {"detail": "Se requiere el campo 'usuario_id'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener imágenes del usuario
        imagenes = Imagen.objects.filter(
            usuario_id=usuario_id
        ).order_by('-es_principal', 'fecha_subida')

        # Generar presigned URLs
        main_image = None
        secondary_images = []

        if imagenes.exists():
            # Imagen principal
            if imagenes[0].imagen:
                main_image = generate_presigned_url(
                    imagenes[0].imagen.name,
                    expiration=3600
                )

            # Imágenes secundarias
            for img in imagenes[1:3]:
                if img.imagen:
                    url = generate_presigned_url(
                        img.imagen.name,
                        expiration=3600
                    )
                    if url:
                        secondary_images.append(url)

        return Response({
            "main_image": main_image,
            "secondary_images": secondary_images
        }, status=status.HTTP_200_OK)
