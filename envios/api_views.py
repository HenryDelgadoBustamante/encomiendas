from api.pagination import ClientePagination, EncomiendaPagination
from rest_framework import mixins, generics
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from envios.models import Encomienda, Empleado
from clientes.models import Cliente
from rutas.models import Ruta
from envios.serializers import (
    EncomiendaSerializer, 
    EncomiendaDetailSerializer,
    ClienteSerializer,
    RutaSerializer
)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def encomienda_list(request):
    """
    Listar todas las encomiendas o crear una nueva.
    """
    if request.method == 'GET':
        encomiendas = Encomienda.objects.all()
        # Podríamos usar EncomiendaDetailSerializer si queremos info completa en la lista
        serializer = EncomiendaSerializer(encomiendas, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = EncomiendaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def encomienda_detail(request, pk):
    """
    Obtener, actualizar o eliminar una encomienda.
    """
    try:
        encomienda = Encomienda.objects.get(pk=pk)
    except Encomienda.DoesNotExist:
        return Response({'error': 'Encomienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EncomiendaDetailSerializer(encomienda)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = (request.method == 'PATCH')
        serializer = EncomiendaSerializer(encomienda, data=request.data, partial=partial)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        encomienda.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- Class Based Views (APIView) ---

class EncomiendaListAPIView(APIView):
    """
    Listar todas las encomiendas o crear una nueva (CBV).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        encomiendas = Encomienda.objects.all()
        serializer = EncomiendaSerializer(encomiendas, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EncomiendaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EncomiendaDetailAPIView(APIView):
    """
    Obtener, actualizar o eliminar una encomienda (CBV).
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Encomienda.objects.get(pk=pk)
        except Encomienda.DoesNotExist:
            return None

    def get(self, request, pk):
        encomienda = self.get_object(pk)
        if not encomienda:
            return Response({'error': 'Encomienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EncomiendaDetailSerializer(encomienda)
        return Response(serializer.data)

    def put(self, request, pk):
        encomienda = self.get_object(pk)
        if not encomienda:
            return Response({'error': 'Encomienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EncomiendaSerializer(encomienda, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        encomienda = self.get_object(pk)
        if not encomienda:
            return Response({'error': 'Encomienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EncomiendaSerializer(encomienda, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        encomienda = self.get_object(pk)
        if not encomienda:
            return Response({'error': 'Encomienda no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        encomienda.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- Generic Views (Concrete) ---

class EncomiendaListCreateView(generics.ListCreateAPIView):
    """
    Lista y creación de encomiendas usando Generic Views.
    """
    queryset = Encomienda.objects.all()
    serializer_class = EncomiendaSerializer
    permission_classes = [IsAuthenticated]

class EncomiendaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Detalle, actualización y eliminación de encomiendas usando Generic Views.
    """
    queryset = Encomienda.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EncomiendaSerializer
        return EncomiendaDetailSerializer

@extend_schema(description="Obtener lista de clientes registrados.")
class ClienteListView(generics.ListAPIView):
    """
    Lista de clientes (solo lectura).
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ClientePagination

@extend_schema(description="Obtener lista de rutas de transporte disponibles.")
class RutaListView(generics.ListAPIView):
    """
    Lista de rutas (solo lectura).
    """
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = EncomiendaPagination
