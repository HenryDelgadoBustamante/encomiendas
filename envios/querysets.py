from django.db import models
from django.utils import timezone
from django.db.models import Q
from config.choices import EstadoEnvio, EstadoGeneral, TipoDocumento

class EncomiendaQuerySet(models.QuerySet):
    def pendientes(self):
        return self.filter(estado=EstadoEnvio.PENDIENTE)

    def en_transito(self):
        return self.filter(estado=EstadoEnvio.EN_TRANSITO)

    def entregadas(self):
        return self.filter(estado=EstadoEnvio.ENTREGADO)

    def devueltas(self):
        return self.filter(estado=EstadoEnvio.DEVUELTO)

    def activas(self):
        return self.exclude(estado__in=[EstadoEnvio.ENTREGADO, EstadoEnvio.DEVUELTO])

    def por_ruta(self, ruta):
        return self.filter(ruta=ruta)

    def por_remitente(self, cliente):
        return self.filter(remitente=cliente)

    def por_destinatario(self, cliente):
        return self.filter(destinatario=cliente)

    def en_transito_por_ruta(self, ruta):
        return self.filter(estado=EstadoEnvio.EN_TRANSITO, ruta=ruta)

    def con_retraso(self):
        return self.exclude(estado=EstadoEnvio.ENTREGADO).filter(
            fecha_entrega_est__lt=timezone.now()
        )

    def con_relaciones(self):
        return self.select_related('remitente', 'destinatario', 'ruta', 'empleado_registro')

class ClienteQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(estado=EstadoGeneral.ACTIVO)

    def de_baja(self):
        return self.filter(estado=EstadoGeneral.INACTIVO)

    def con_dni(self):
        return self.filter(tipo_doc=TipoDocumento.DNI)

    def buscar(self, termino):
        return self.filter(
            Q(nombres__icontains=termino) | 
            Q(apellidos__icontains=termino) | 
            Q(nro_doc__icontains=termino) |
            Q(email__icontains=termino)
        )

class RutaQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(estado=EstadoGeneral.ACTIVO)

    def por_origen(self, ciudad):
        return self.filter(origen__icontains=ciudad)

    def por_destino(self, ciudad):
        return self.filter(destino__icontains=ciudad)
