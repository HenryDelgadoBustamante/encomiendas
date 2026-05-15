from django.db import models
from config.choices import EstadoGeneral
from envios.querysets import RutaQuerySet

class Ruta(models.Model):
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    origen = models.CharField(max_length=100, verbose_name='Origen')
    destino = models.CharField(max_length=100, verbose_name='Destino')
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')
    precio_base = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Precio Base')
    dias_entrega = models.PositiveIntegerField(verbose_name='Días de Entrega')
    estado = models.CharField(
        max_length=3, 
        choices=EstadoGeneral.choices, 
        default=EstadoGeneral.ACTIVO, 
        verbose_name='Estado'
    )

    objects = RutaQuerySet.as_manager()

    class Meta:
        db_table = 'rutas'
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'

    def __str__(self):
        return f"{self.origen} - {self.destino}"
