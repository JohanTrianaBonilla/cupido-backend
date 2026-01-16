"""
Script de prueba para verificar la generación de presigned URLs con MinIO.

Uso:
    python test_minio_presigned.py
"""
import os
import django
from dotenv import load_dotenv

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.profile_app.subapps.imageUpload.services import (
    get_s3_client,
    generate_presigned_url,
    generate_presigned_urls_batch
)
from apps.profile_app.subapps.imageUpload.models import Imagen


def test_s3_connection():
    """Prueba 1: Verificar conexión a MinIO"""
    print("=" * 80)
    print("PRUEBA 1: Verificar conexión a MinIO")
    print("=" * 80)

    try:
        s3 = get_s3_client()

        # Listar buckets
        response = s3.list_buckets()
        print("\n✅ Conexión exitosa!")
        print(f"\n📦 Buckets disponibles:")
        for bucket in response['Buckets']:
            print(f"  - {bucket['Name']}")

        return True
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        return False


def test_list_images():
    """Prueba 2: Listar imágenes en el bucket"""
    print("\n" + "=" * 80)
    print("PRUEBA 2: Listar imágenes en el bucket")
    print("=" * 80)

    try:
        s3 = get_s3_client()
        from django.conf import settings

        response = s3.list_objects_v2(
            Bucket=settings.MINIO_BUCKET_NAME,
            Prefix='imagenes/usuarios/',
            MaxKeys=10
        )

        if 'Contents' in response:
            print(f"\n✅ Se encontraron {len(response['Contents'])} archivos:")
            for obj in response['Contents']:
                size_kb = obj['Size'] / 1024
                print(f"  - {obj['Key']} ({size_kb:.2f} KB)")
            return True
        else:
            print("\n⚠️  No se encontraron archivos en el bucket")
            return False

    except Exception as e:
        print(f"\n❌ Error listando archivos: {e}")
        return False


def test_presigned_url():
    """Prueba 3: Generar presigned URL para una imagen existente"""
    print("\n" + "=" * 80)
    print("PRUEBA 3: Generar presigned URL")
    print("=" * 80)

    try:
        # Obtener la primera imagen de la base de datos
        imagen = Imagen.objects.first()

        if not imagen:
            print("\n⚠️  No hay imágenes en la base de datos")
            return False

        print(f"\n📸 Imagen encontrada:")
        print(f"  - ID: {imagen.id}")
        print(f"  - Usuario ID: {imagen.usuario_id}")
        print(f"  - Ruta: {imagen.imagen.name}")
        print(f"  - Es principal: {imagen.es_principal}")

        # Generar presigned URL
        url = generate_presigned_url(imagen.imagen.name, expiration=3600)

        if url:
            print(f"\n✅ Presigned URL generada (válida por 1 hora):")
            print(f"\n{url}")
            print(f"\n💡 Copia esta URL en tu navegador para verificar que funciona")
            return True
        else:
            print("\n❌ No se pudo generar la presigned URL")
            return False

    except Exception as e:
        print(f"\n❌ Error generando presigned URL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_presigned_urls():
    """Prueba 4: Generar múltiples presigned URLs"""
    print("\n" + "=" * 80)
    print("PRUEBA 4: Generar presigned URLs en lote")
    print("=" * 80)

    try:
        # Obtener las primeras 5 imágenes
        imagenes = Imagen.objects.all()[:5]

        if not imagenes:
            print("\n⚠️  No hay imágenes en la base de datos")
            return False

        print(f"\n📸 Se encontraron {len(imagenes)} imágenes")

        # Obtener las rutas de las imágenes
        image_keys = [img.imagen.name for img in imagenes if img.imagen]

        print(f"\n🔄 Generando presigned URLs para {len(image_keys)} imágenes...")

        # Generar presigned URLs en lote
        urls = generate_presigned_urls_batch(image_keys, expiration=3600)

        print(f"\n✅ Se generaron {len(urls)} URLs:")
        for i, (key, url) in enumerate(urls.items(), 1):
            status = "✅" if url else "❌"
            print(f"\n  {i}. {status} {key}")
            if url:
                print(f"     URL: {url[:100]}...")

        return True

    except Exception as e:
        print(f"\n❌ Error generando presigned URLs en lote: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "=" * 80)
    print("PRUEBAS DE PRESIGNED URLs CON MINIO")
    print("=" * 80)

    from django.conf import settings
    print(f"\n⚙️  Configuración:")
    print(f"  - Endpoint: {settings.MINIO_ENDPOINT}")
    print(f"  - Bucket: {settings.MINIO_BUCKET_NAME}")
    print(f"  - Access Key: {settings.MINIO_ACCESS_KEY[:10]}...")
    print(f"  - Use SSL: {settings.MINIO_USE_SSL}")

    results = {
        "Conexión a MinIO": test_s3_connection(),
        "Listar imágenes": test_list_images(),
        "Generar presigned URL": test_presigned_url(),
        "Generar URLs en lote": test_batch_presigned_urls()
    }

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    total_passed = sum(results.values())
    total_tests = len(results)

    print(f"\n📊 Total: {total_passed}/{total_tests} pruebas pasaron")

    if total_passed == total_tests:
        print("\n🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración de MinIO.")


if __name__ == '__main__':
    main()
