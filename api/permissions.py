from rest_framework import permissions
from envios.models import Empleado

class EsEmpleadoActivo(permissions.BasePermission):
    """
    Permiso que verifica si el usuario autenticado tiene un registro de empleado activo.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuario siempre tiene permiso
        if request.user.is_superuser:
            return True

        return Empleado.objects.filter(
            email=request.user.email, 
            estado='ACT' # EstadoGeneral.ACTIVO
        ).exists()

class EsPropietarioOAdmin(permissions.BasePermission):
    """
    Permiso que permite el acceso solo al creador del registro o a un administrador.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
            
        try:
            empleado = Empleado.objects.get(email=request.user.email)
            # En Encomienda, el propietario es 'empleado_registro'
            return obj.empleado_registro == empleado
        except (Empleado.DoesNotExist, AttributeError):
            return False
