from django.db import models
from django.core.validators import MinValueValidator
from config.choices import EstadoGeneral, EstadoEnvio
from .validators import validar_peso_positivo, validar_codigo_encomienda
from .querysets import EncomiendaQuerySet

class Empleado(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name='Código')
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    cargo = models.CharField(max_length=100, verbose_name='Cargo')
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')
    telefono = models.CharField(max_length=15, verbose_name='Teléfono')
    estado = models.CharField(
        max_length=3,
        choices=EstadoGeneral.choices,
        default=EstadoGeneral.ACTIVO,
        verbose_name='Estado'
    )
    fecha_ingreso = models.DateField(verbose_name='Fecha de Ingreso')
    rutas_asignadas = models.ManyToManyField('rutas.Ruta', verbose_name='Rutas Asignadas', blank=True)

    class Meta:
        db_table = 'empleados'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

class Encomienda(models.Model):
    codigo = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='Código',
        validators=[validar_codigo_encomienda]
    )
    descripcion = models.TextField(verbose_name='Descripción')
    peso_kg = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name='Peso (kg)',
        validators=[validar_peso_positivo]
    )
    volumen_cm3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Volumen (cm³)')
    remitente = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.RESTRICT, 
        related_name='envios_como_remitente',
        verbose_name='Remitente'
    )
    destinatario = models.ForeignKey(
        'clientes.Cliente', 
        on_delete=models.RESTRICT, 
        related_name='envios_como_destinatario',
        verbose_name='Destinatario'
    )
    ruta = models.ForeignKey(
        'rutas.Ruta',
        on_delete=models.RESTRICT,
        verbose_name='Ruta'
    )
    empleado_registro = models.ForeignKey(
        Empleado,
        on_delete=models.RESTRICT,
        verbose_name='Empleado que Registra'
    )
    estado = models.CharField(
        max_length=3,
        choices=EstadoEnvio.choices,
        default=EstadoEnvio.PENDIENTE,
        verbose_name='Estado'
    )
    costo_envio = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name='Costo de Envío',
        validators=[MinValueValidator(0)]
    )
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')
    fecha_entrega_est = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Entrega Estimada')
    fecha_entrega_real = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de Entrega Real')
    observaciones = models.TextField(blank=True, null=True, verbose_name='Observaciones')

    objects = EncomiendaQuerySet.as_manager()

    class Meta:
        db_table = 'encomiendas'
        verbose_name = 'Encomienda'
        verbose_name_plural = 'Encomiendas'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.codigo} - {self.descripcion[:50]}"

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        errors = {}

        if hasattr(self, 'remitente') and hasattr(self, 'destinatario') and self.remitente == self.destinatario:
            errors['destinatario'] = 'El remitente y destinatario no pueden ser iguales.'

        if self.fecha_entrega_est and self.fecha_entrega_est < timezone.now():
            errors['fecha_entrega_est'] = 'La fecha de entrega estimada no puede ser una fecha pasada.'

        if self.fecha_entrega_real and self.fecha_entrega_est and self.fecha_entrega_real < self.fecha_entrega_est:
            errors['fecha_entrega_real'] = 'La fecha de entrega real no puede ser antes de la fecha estimada.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def esta_entregada(self):
        return self.estado == EstadoEnvio.ENTREGADO

    @property
    def esta_en_transito(self):
        return self.estado == EstadoEnvio.EN_TRANSITO

    @property
    def dias_en_transito(self):
        from django.utils import timezone
        if not self.fecha_registro:
            return 0
        fecha_fin = self.fecha_entrega_real if self.fecha_entrega_real else timezone.now()
        return (fecha_fin - self.fecha_registro).days

    @property
    def tiene_retraso(self):
        from django.utils import timezone
        if not self.fecha_entrega_est:
            return False
        if self.esta_entregada and self.fecha_entrega_real:
            return self.fecha_entrega_real > self.fecha_entrega_est
        return timezone.now() > self.fecha_entrega_est

    @property
    def descripcion_corta(self):
        if self.descripcion and len(self.descripcion) > 50:
            return f"{self.descripcion[:50]}..."
        return self.descripcion

    def cambiar_estado(self, nuevo_estado, empleado, observacion=''):
        from django.utils import timezone
        
        estado_anterior = self.estado
        self.estado = nuevo_estado
        
        if nuevo_estado == EstadoEnvio.ENTREGADO:
            self.fecha_entrega_real = timezone.now()
            
        self.save()
        
        HistorialEstado.objects.create(
            encomienda=self,
            estado_anterior=estado_anterior,
            estado_nuevo=nuevo_estado,
            observacion=observacion,
            empleado=empleado
        )

    def calcular_costo(self):
        if hasattr(self, 'ruta') and self.ruta and self.peso_kg is not None:
            self.costo_envio = self.ruta.precio_base * self.peso_kg
        else:
            self.costo_envio = 0

    @classmethod
    def crear_con_costo_calculado(cls, **kwargs):
        from django.utils import timezone
        import datetime
        import random
        import string
        
        encomienda = cls(**kwargs)
        
        fecha_str = timezone.now().strftime('%Y%m%d')
        sufijo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        encomienda.codigo = f"ENC-{fecha_str}-{sufijo}"
        
        if hasattr(encomienda, 'ruta') and encomienda.ruta and encomienda.ruta.dias_entrega:
            encomienda.fecha_entrega_est = timezone.now() + datetime.timedelta(days=encomienda.ruta.dias_entrega)
            
        encomienda.calcular_costo()
        encomienda.save()
        
        return encomienda

class HistorialEstado(models.Model):
    encomienda = models.ForeignKey(
        Encomienda, 
        on_delete=models.CASCADE, 
        related_name='historial_estados',
        verbose_name='Encomienda'
    )
    estado_anterior = models.CharField(
        max_length=3, 
        choices=EstadoEnvio.choices,
        verbose_name='Estado Anterior'
    )
    estado_nuevo = models.CharField(
        max_length=3, 
        choices=EstadoEnvio.choices,
        verbose_name='Estado Nuevo'
    )
    observacion = models.TextField(blank=True, null=True, verbose_name='Observación')
    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.RESTRICT,
        verbose_name='Empleado que registra'
    )
    fecha_cambio = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Cambio')

    class Meta:
        db_table = 'historial_estados'
        verbose_name = 'Historial de Estado'
        verbose_name_plural = 'Historiales de Estado'

    def __str__(self):
        return f"{self.encomienda.codigo} - {self.get_estado_anterior_display()} a {self.get_estado_nuevo_display()}"
