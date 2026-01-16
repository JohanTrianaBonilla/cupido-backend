from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class DetallesLike(models.Model):
    # Restricciones para los estados
    ESTADO_CHOICES = [
        ('LIKE', 'Me Gusta'),
        ('DISLIKE', 'No Me Gusta'),
    ]

    usuarioEmisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_hechos')
    usuarioReceptor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_recibidos')
    fechaInteraccion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=7, choices=ESTADO_CHOICES)
    esMutuo = models.BooleanField(default=False)
    
    class Meta:
        # Asegura que un emisor solo pueda interactuar una vez con un receptor
        db_table = 'detalles_like'
        unique_together = ('usuarioEmisor', 'usuarioReceptor')
        verbose_name = "Detalle de Interacción"
        verbose_name_plural = "Detalles de Interacciones"

    def __str__(self):
        return f'{self.usuarioEmisor.email} -> {self.usuarioReceptor.email} ({self.estado})'