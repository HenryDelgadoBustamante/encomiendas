from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'

class EmpleadoRateThrottle(UserRateThrottle):
    scope = 'empleado'

class CambioEstadoThrottle(UserRateThrottle):
    scope = 'cambio_estado'
