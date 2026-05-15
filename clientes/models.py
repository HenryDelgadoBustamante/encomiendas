from django.db import models
from config.choices import TipoDocumento, EstadoGeneral
from envios.querysets import ClienteQuerySet

class Cliente(models.Model):
    tipo_doc = models.CharField(
        max_length=3, 
        choices=TipoDocumento.choices, 
        default=TipoDocumento.DNI, 
        verbose_name='Tipo de Documento'
    )
    nro_doc = models.CharField(max_length=15, unique=True, verbose_name='Número de Documento')
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    direccion = models.TextField(verbose_name='Dirección')
    estado = models.CharField(
        max_length=3, 
        choices=EstadoGeneral.choices, 
        default=EstadoGeneral.ACTIVO, 
        verbose_name='Estado'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    objects = ClienteQuerySet.as_manager()

    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def esta_activo(self):
        return self.estado == EstadoGeneral.ACTIVO

    @property
    def total_encomiendas_enviadas(self):
        if hasattr(self, 'envios_como_remitente'):
            return self.envios_como_remitente.count()
        return 0
