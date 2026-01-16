from django.db import models
from django.conf import settings

class Match(models.Model):
    """
    Modelo principal de Match entre dos usuarios.
    Los usuarios se almacenan en orden de ID para asegurar la unicidad del par.
    """
    usuarioA = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matches_como_a'
    )
    usuarioB = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matches_como_b'
    )
    fechaMatch = models.DateTimeField(auto_now_add=True)
    afinidad = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    estadoMatch = models.CharField(max_length=10, default='ACTIVO')

    class Meta:
        db_table = 'match_app_match'
        unique_together = ('usuarioA', 'usuarioB')
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    def __str__(self):
        return f'Match entre {self.usuarioA} y {self.usuarioB}'