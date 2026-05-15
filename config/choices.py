from django.db import models

class EstadoGeneral(models.TextChoices):
    ACTIVO = 'ACT', 'Activo'
    INACTIVO = 'INA', 'Inactivo'

class EstadoEnvio(models.TextChoices):
    PENDIENTE = 'PEN', 'Pendiente'
    EN_TRANSITO = 'TRA', 'En tránsito'
    ENTREGADO = 'ENT', 'Entregado'
    DEVUELTO = 'DEV', 'Devuelto'

class TipoDocumento(models.TextChoices):
    DNI = 'DNI', 'DNI'
    RUC = 'RUC', 'RUC'
    CE = 'CE', 'Carné de Extranjería'
    PASAPORTE = 'PAS', 'Pasaporte'
