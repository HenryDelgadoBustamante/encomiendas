from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from envios.models import Encomienda, Empleado
from rutas.models import Ruta
from envios.serializers import (
    EncomiendaSerializer, 
    EncomiendaDetailSerializer,
    EncomiendaV2Serializer,
    EncomiendaListSerializer,
    RutaSerializer
)
from api.pagination import EncomiendaPagination
from api.filters import EncomiendaFilter
from api.permissions import EsEmpleadoActivo, EsPropietarioOAdmin
from api.throttles import EmpleadoRateThrottle, CambioEstadoThrottle

@extend_schema_view(
    list=extend_schema(description="Obtener lista paginada de encomiendas."),
    retrieve=extend_schema(description="Obtener detalle completo de una encomienda."),
    create=extend_schema(description="Registrar una nueva encomienda en el sistema."),
    update=extend_schema(description="Actualización total de una encomienda."),
    partial_update=extend_schema(description="Actualización parcial de una encomienda."),
    destroy=extend_schema(description="Eliminar permanentemente una encomienda.")
)
class EncomiendaViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para la gestión de encomiendas.
    Incluye acciones personalizadas para flujo de estados y filtros.
    """
    queryset = Encomienda.objects.all()
    pagination_class = EncomiendaPagination
    
    def get_permissions(self):
        """
        Asignación dinámica de permisos según la acción.
        """
        if self.action in ['update', 'partial_update', 'destroy', 'cambiar_estado']:
            # Solo el creador o admin puede modificar o cambiar estado
            return [EsPropietarioOAdmin()]
        return [EsEmpleadoActivo()]

    def get_throttles(self):
        """
        Asignación de límites de peticiones según la acción.
        """
        if self.action == 'cambiar_estado':
            return [CambioEstadoThrottle()]
        return [EmpleadoRateThrottle()]
    
    # Configuración de Filtros
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_class = EncomiendaFilter
    search_fields = ['codigo', 'descripcion', 'remitente__nombres', 'destinatario__nombres']
    ordering_fields = ['fecha_registro', 'costo_envio', 'peso_kg', 'estado']
    ordering = ['-fecha_registro'] # Orden por defecto

    def get_serializer_class(self):
        # Lógica de Versión
        version = self.request.version
        if version == 'v2':
            return EncomiendaV2Serializer
            
        # Lógica por Acción (v1 por defecto)
        if self.action == 'list':
            return EncomiendaListSerializer
        if self.action in ['retrieve', 'cambiar_estado']:
            return EncomiendaDetailSerializer
        return EncomiendaSerializer

    def get_queryset(self):
        # Usamos el manager personalizado con select_related y prefetch_related
        qs = Encomienda.objects.con_relaciones()
        if self.action == 'list':
            # Optimización de campos solo para el listado
            # NOTA: Se deben incluir las FKs que están en select_related
            return qs.only(
                'id', 'codigo', 'estado', 'costo_envio', 'fecha_registro',
                'remitente_id', 'destinatario_id', 'ruta_id', 'empleado_registro_id'
            )
        return qs

    def perform_update(self, serializer):
        # Invalida cache de estadísticas al actualizar
        cache.delete('encomiendas_stats')
        serializer.save()

    def perform_destroy(self, instance):
        # Invalida cache de estadísticas al eliminar
        cache.delete('encomiendas_stats')
        instance.delete()

    @extend_schema(
        request=EncomiendaSerializer,
        responses={200: EncomiendaDetailSerializer},
        description="Cambia el estado de una encomienda y genera un registro en el historial."
    )
    @action(detail=True, methods=['post'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None, **kwargs):
        """
        Acción para cambiar el estado de una encomienda y registrar en el historial.
        """
        encomienda = self.get_object()
        nuevo_estado = request.data.get('nuevo_estado')
        empleado_id = request.data.get('empleado_id')
        observacion = request.data.get('observacion', '')

        if not nuevo_estado or not empleado_id:
            return Response(
                {'error': 'Debe proporcionar nuevo_estado y empleado_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            empleado = Empleado.objects.get(pk=empleado_id)
        except Empleado.DoesNotExist:
            return Response({'error': 'Empleado no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        try:
            encomienda.cambiar_estado(nuevo_estado, empleado, observacion)
            # Invalida cache al cambiar estado
            cache.delete('encomiendas_stats')
            serializer = EncomiendaDetailSerializer(encomienda)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(description="Lista las encomiendas que han superado su fecha de entrega estimada.")
    @action(detail=False, methods=['get'])
    def con_retraso(self, request, **kwargs):
        """
        Listar encomiendas que superaron la fecha de entrega estimada.
        """
        encomiendas = self.get_queryset().con_retraso()
        
        page = self.paginate_queryset(encomiendas)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(encomiendas, many=True)
        return Response(serializer.data)

    @extend_schema(description="Lista las encomiendas que aún no han sido procesadas.")
    @action(detail=False, methods=['get'])
    def pendientes(self, request, **kwargs):
        """
        Listar encomiendas en estado PENDIENTE.
        """
        encomiendas = self.get_queryset().pendientes()
        
        page = self.paginate_queryset(encomiendas)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(encomiendas, many=True)
        return Response(serializer.data)

    @extend_schema(description="Resumen estadístico de las encomiendas por estado.")
    @action(detail=False, methods=['get'])
    def estadisticas(self, request, **kwargs):
        """
        Retornar estadísticas generales de las encomiendas (con Cache).
        """
        cached_data = cache.get('encomiendas_stats')
        if cached_data:
            return Response(cached_data)

        qs = self.get_queryset()
        data = {
            'total': qs.count(),
            'pendientes': qs.pendientes().count(),
            'en_transito': qs.en_transito().count(),
            'entregadas': qs.entregadas().count(),
            'con_retraso': qs.con_retraso().count(),
            'ultimo_cambio': timezone.now()
        }
        
        # Cache por 15 minutos
        cache.set('encomiendas_stats', data, 60 * 15)
        return Response(data)

    @extend_schema(
        request=EncomiendaSerializer(many=True),
        description="Creación masiva de encomiendas."
    )
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Actualización masiva de estado para una lista de IDs.",
        request={'type': 'object', 'properties': {'ids': {'type': 'array', 'items': {'type': 'integer'}}, 'nuevo_estado': {'type': 'string'}}}
    )
    @action(detail=False, methods=['post'], url_path='bulk-estado')
    def bulk_estado(self, request, **kwargs):
        ids = request.data.get('ids', [])
        nuevo_estado = request.data.get('nuevo_estado')
        
        if not ids or not nuevo_estado:
            return Response({'error': 'Debe proporcionar ids y nuevo_estado'}, status=status.HTTP_400_BAD_REQUEST)
            
        updated_count = Encomienda.objects.filter(id__in=ids).update(estado=nuevo_estado)
        cache.delete('encomiendas_stats')
        return Response({'message': f'Se actualizaron {updated_count} encomiendas.'})

class RutaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para rutas con cache de página.
    """
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 15)) # Cache de 15 minutos
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
