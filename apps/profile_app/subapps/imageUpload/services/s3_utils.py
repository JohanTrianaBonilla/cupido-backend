"""
Utilidades para generar presigned URLs de MinIO/S3.

Como las imágenes ahora son privadas, necesitamos generar URLs firmadas
temporalmente para que el frontend pueda acceder a ellas.
"""
import boto3
from django.conf import settings
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Crea y retorna un cliente S3/MinIO configurado.

    Returns:
        boto3.client: Cliente S3 configurado para MinIO
    """
    return boto3.client(
        's3',
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name=settings.MINIO_REGION if settings.MINIO_REGION else None,
        config=boto3.session.Config(signature_version='s3v4')
    )


def generate_presigned_url(image_key: str, expiration: int = 3600) -> str | None:
    """
    Genera una presigned URL temporal para una imagen en MinIO.

    Args:
        image_key: Ruta del archivo en MinIO
                  (ej: 'imagenes/usuarios/49/49_imagen_69.jpg')
        expiration: Segundos de validez de la URL (default: 1 hora = 3600s)

    Returns:
        str: URL firmada temporal o None si falla

    Ejemplo:
        >>> url = generate_presigned_url('imagenes/usuarios/49/49_imagen_69.jpg')
        >>> print(url)
        'https://multimedia.cupidocol.com/multimediacupido/imagenes/usuarios/49/49_imagen_69.jpg?X-Amz-...'
    """
    if not image_key:
        return None

    try:
        s3_client = get_s3_client()

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.MINIO_BUCKET_NAME,
                'Key': image_key
            },
            ExpiresIn=expiration
        )

        return url

    except ClientError as e:
        logger.error(f"Error generando presigned URL para {image_key}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado generando presigned URL: {e}")
        return None


def generate_presigned_urls_batch(image_keys: list[str], expiration: int = 3600) -> dict[str, str]:
    """
    Genera presigned URLs para múltiples imágenes de forma eficiente.

    Args:
        image_keys: Lista de rutas de archivos en MinIO
        expiration: Segundos de validez de las URLs

    Returns:
        dict: Diccionario con {image_key: presigned_url}

    Ejemplo:
        >>> keys = ['imagenes/usuarios/49/49_imagen_1.jpg', 'imagenes/usuarios/49/49_imagen_2.jpg']
        >>> urls = generate_presigned_urls_batch(keys)
        >>> print(urls)
        {
            'imagenes/usuarios/49/49_imagen_1.jpg': 'https://...',
            'imagenes/usuarios/49/49_imagen_2.jpg': 'https://...'
        }
    """
    if not image_keys:
        return {}

    s3_client = get_s3_client()
    urls = {}

    for key in image_keys:
        if not key:
            continue

        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.MINIO_BUCKET_NAME,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            urls[key] = url
        except Exception as e:
            logger.error(f"Error generando URL para {key}: {e}")
            urls[key] = None

    return urls
