from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from envios.models import Empleado

from api.throttles import LoginRateThrottle

class EncomiendaTokenSerializer(TokenObtainPairSerializer):
    """
    Serializer personalizado para incluir datos del empleado en el payload del JWT.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Añadir claims personalizados basados en el modelo Empleado
        try:
            empleado = Empleado.objects.get(email=user.email)
            token['codigo_empleado'] = empleado.codigo
            token['nombre_completo'] = f"{empleado.nombres} {empleado.apellidos}"
            token['cargo'] = empleado.cargo
            token['es_activo'] = (empleado.estado == 'ACT')
        except Empleado.DoesNotExist:
            token['error'] = 'Usuario no vinculado a un registro de empleado'

        return token

class EncomiendaTokenView(TokenObtainPairView):
    """
    Vista personalizada para obtener el token JWT.
    """
    serializer_class = EncomiendaTokenSerializer
    throttle_classes = [LoginRateThrottle]
