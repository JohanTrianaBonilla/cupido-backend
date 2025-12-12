"""
Permisos personalizados para el panel de administración.
"""
from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """
    Permite acceso solo a usuarios con is_superuser=True.
    """
    message = "Acceso denegado. Se requieren permisos de superusuario."

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_superuser
        )
