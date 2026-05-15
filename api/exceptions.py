from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status

class EstadoInvalidoError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'El estado proporcionado no es válido para esta operación.'
    default_code = 'estado_invalido'

class EncomiendaYaEntregadaError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'No se puede modificar una encomienda que ya ha sido entregada.'
    default_code = 'encomienda_entregada'

def encomiendas_exception_handler(exc, context):
    """
    Handler personalizado para devolver siempre el mismo formato JSON.
    Formato: { "error": true, "code": "...", "message": "...", "detail": "..." }
    """
    # Llamar primero al handler por defecto de DRF para obtener la respuesta estándar
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            "error": True,
            "code": getattr(exc, 'default_code', 'error_api'),
            "message": str(exc.default_detail) if hasattr(exc, 'default_detail') else "Ocurrió un error en la solicitud",
            "detail": response.data
        }
        response.data = custom_data

    return response
