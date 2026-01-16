# apps/auth_app/serializers/login_serializer.py

from django.contrib.auth.hashers import check_password
from rest_framework import serializers
from apps.auth_app.models import Usuario

# Utilidades (implementarlas en apps.auth_app.utils)
from apps.auth_app.utils.recaptcha import verify_recaptcha_token


class LoginSerializer(serializers.Serializer):
    """
    Valida credenciales de inicio de sesión.
    - Comprueba existencia del usuario.
    - Verifica la contraseña (con hash).
    - Valida reCAPTCHA token.
    - Verifica estado de cuenta: permite "activa" e "incompleta", bloquea "inactiva" y "reportada".
    """

    # Campos en orden: reCAPTCHA primero para fail-fast
    #recaptcha_token = serializers.CharField(write_only=True, required=True, allow_blank=False)
    email = serializers.EmailField()
    contrasena = serializers.CharField(write_only=True)

    def validate_recaptcha_token(self, value):
        """
        Validar reCAPTCHA primero (fail-fast para mejor UX).
        Maneja específicamente tokens expirados.
        """
        try:
            success, details = verify_recaptcha_token(value)
            if not success:
                error_codes = details.get("error-codes", [])

                # Mensaje específico para token expirado
                if "timeout-or-duplicate" in error_codes:
                    raise serializers.ValidationError(
                        "El reCAPTCHA ha expirado. Por favor, completa el reCAPTCHA nuevamente."
                    )

                # Otros errores de reCAPTCHA
                raise serializers.ValidationError(f"reCAPTCHA inválido. Códigos: {error_codes}")
            return value
        except RuntimeError as e:
            raise serializers.ValidationError(str(e))

    def validate(self, attrs):
        email = attrs.get("email")
        contrasena = attrs.get("contrasena")

        # 1️⃣ Verificar existencia del usuario
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"email": "Usuario no encontrado."})

        # 2️⃣ Verificar estado de cuenta
        estadocuenta = user.estadocuenta
        if estadocuenta in ["-2", "-1"]:
            raise serializers.ValidationError(
                {"email": f"Cuenta {estadocuenta}. No se permite el acceso."}
            )
        elif estadocuenta not in ["0", "1" , "2", "3"]:
            raise serializers.ValidationError(
                {"email": "Estado de cuenta inválido."}
            )

        # 3️⃣ Validar contraseña (verificación segura con hash)
        if not check_password(contrasena, user.contrasena):
            raise serializers.ValidationError({"contrasena": "Contraseña incorrecta."})

        # 4️⃣ Si todo es correcto, adjuntar usuario validado
        attrs["user"] = user
        attrs["estadocuenta"] = estadocuenta  # Para usar en la vista
        return attrs
