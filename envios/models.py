from django.db import models


class Encomienda(models.Model):
    """Modelo para gestionar encomiendas."""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_transito', 'En tránsito'),
        ('entregado', 'Entregado'),
        ('devuelto', 'Devuelto'),
    ]

    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    descripcion = models.TextField(verbose_name='Descripción')
    peso_kg = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Peso (kg)'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de envío'
    )
    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de entrega'
    )

    class Meta:
        verbose_name = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering = ['-fecha_envio']

    def __str__(self):
        return f'{self.codigo} - {self.descripcion[:50]}'
