"""
URLs para el panel de administración.
Todos los endpoints requieren permisos de superusuario.
"""
from django.urls import path
from .views import (
    GetUserByEmailView,
    BanUserView,
    DeleteUserView,
    UpdateGenderPreferenceView,
)

urlpatterns = [
    path('user-by-email/', GetUserByEmailView.as_view(), name='admin-user-by-email'),
    path('ban-user/', BanUserView.as_view(), name='admin-ban-user'),
    path('delete-user/', DeleteUserView.as_view(), name='admin-delete-user'),
    path('update-gender-pref/', UpdateGenderPreferenceView.as_view(), name='admin-update-gender-pref'),
]
