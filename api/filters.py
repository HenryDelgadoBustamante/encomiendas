from django_filters import rest_framework as filters
from envios.models import Encomienda

class EncomiendaFilter(filters.FilterSet):
    # Filtros por rango de fechas
    fecha_desde = filters.DateTimeFilter(field_name="fecha_registro", lookup_expr='gte')
    fecha_hasta = filters.DateTimeFilter(field_name="fecha_registro", lookup_expr='lte')
    
    # Filtros por rango de costo
    costo_min = filters.NumberFilter(field_name="costo_envio", lookup_expr='gte')
    costo_max = filters.NumberFilter(field_name="costo_envio", lookup_expr='lte')
    
    # Filtro por búsqueda parcial en descripción
    descripcion = filters.CharFilter(field_name="descripcion", lookup_expr='icontains')

    class Meta:
        model = Encomienda
        fields = {
            'estado': ['exact'],
            'remitente': ['exact'],
            'destinatario': ['exact'],
            'ruta': ['exact'],
            'codigo': ['exact', 'icontains'],
        }
