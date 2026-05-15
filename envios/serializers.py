from rest_framework import serializers
from envios.models import Encomienda, HistorialEstado, Empleado
from clientes.models import Cliente
from rutas.models import Ruta

class EncomiendaBulkSerializer(serializers.ListSerializer):
    """
    Serializer para operaciones masivas (Bulk Create y Bulk Update).
    """
    def create(self, validated_data):
        encomiendas = [Encomienda(**item) for item in validated_data]
        return Encomienda.objects.bulk_create(encomiendas)

    def update(self, instance, validated_data):
        # Mapeo de instancias por ID para actualización masiva
        instance_mapping = {obj.id: obj for obj in instance}
        ret = []
        for item in validated_data:
            obj = instance_mapping.get(item.get('id'))
            if obj:
                # Actualizar campos
                for attr, value in item.items():
                    setattr(obj, attr, value)
                ret.append(obj)
        
        # Realizar bulk_update especificando campos si es necesario
        fields = ['estado', 'observaciones', 'costo_envio'] # Ejemplo de campos a actualizar
        Encomienda.objects.bulk_update(ret, fields)
        return ret

class ClienteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.ReadOnlyField()
    esta_activo = serializers.ReadOnlyField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'tipo_doc', 'nro_doc', 'nombres', 'apellidos', 
            'nombre_completo', 'email', 'telefono', 'direccion', 
            'estado', 'esta_activo', 'fecha_registro'
        ]

class RutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ruta
        fields = '__all__'

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = ['id', 'codigo', 'nombres', 'apellidos', 'cargo', 'email']

class HistorialEstadoSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.ReadOnlyField(source='empleado.nombres')
    estado_anterior_display = serializers.CharField(source='get_estado_anterior_display', read_only=True)
    estado_nuevo_display = serializers.CharField(source='get_estado_nuevo_display', read_only=True)

    class Meta:
        model = HistorialEstado
        fields = [
            'id', 'encomienda', 'estado_anterior', 'estado_anterior_display',
            'estado_nuevo', 'estado_nuevo_display', 'observacion',
            'empleado', 'empleado_nombre', 'fecha_cambio'
        ]

class EncomiendaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encomienda
        fields = '__all__'
        list_serializer_class = EncomiendaBulkSerializer

    def validate_peso_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser un valor positivo.")
        return value

    def validate_codigo(self, value):
        if not value.startswith('ENC-'):
            raise serializers.ValidationError("El código debe empezar con 'ENC-'.")
        return value

    def validate_costo_envio(self, value):
        if value < 0:
            raise serializers.ValidationError("El costo de envío no puede ser negativo.")
        return value

    def validate(self, data):
        from django.utils import timezone
        
        # 1. Validación cruzada: Remitente != Destinatario
        remitente = data.get('remitente')
        destinatario = data.get('destinatario')
        if remitente and destinatario and remitente == destinatario:
            raise serializers.ValidationError({
                "destinatario": "El remitente y el destinatario no pueden ser la misma persona."
            })

        # 2. Validación de fecha: No en el pasado
        fecha_entrega_est = data.get('fecha_entrega_est')
        if fecha_entrega_est and fecha_entrega_est < timezone.now():
            raise serializers.ValidationError({
                "fecha_entrega_est": "La fecha de entrega estimada no puede ser en el pasado."
            })

        # 3. Validación de costo mínimo por ruta
        ruta = data.get('ruta')
        peso = data.get('peso_kg')
        costo = data.get('costo_envio')
        
        if ruta and peso and costo:
            costo_minimo = ruta.precio_base * peso
            if costo < costo_minimo:
                raise serializers.ValidationError({
                    "costo_envio": f"El costo de envío es insuficiente para esta ruta y peso. Mínimo: {costo_minimo}"
                })

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # 1. Campos calculados de ruta
        if instance.ruta:
            representation['ruta_nombre'] = f"{instance.ruta.origen} -> {instance.ruta.destino}"
            representation['tiempo_estimado'] = f"{instance.ruta.dias_entrega} días"

        # 2. costo_display
        representation['costo_display'] = f"S/ {instance.costo_envio:,.2f}"

        # 3. estado_color
        colores = {
            'PEN': '#FFC107', # Ámbar
            'TRA': '#2196F3', # Azul
            'ENT': '#4CAF50', # Verde
            'DEV': '#F44336'  # Rojo
        }
        representation['estado_color'] = colores.get(instance.estado, '#757575')

        # 4. Seguridad: Ocultar campos para no-staff
        request = self.context.get('request')
        if request and not request.user.is_staff:
            representation.pop('observaciones', None)
            representation.pop('empleado_registro', None)

        return representation

    def to_internal_value(self, data):
        # Asegurar que los datos sean mutables (QueryDict)
        if hasattr(data, 'copy'):
            data = data.copy()
        
        # 1. Normalización de código (Mayúsculas y trim)
        if 'codigo' in data:
            data['codigo'] = data['codigo'].strip().upper()
        
        # 2. Normalización de descripción (Capitalize)
        if 'descripcion' in data:
            data['descripcion'] = data['descripcion'].strip().capitalize()
            
        # 3. Normalización de costo (Asegurar valor absoluto/positivo)
        if 'costo_envio' in data:
            try:
                data['costo_envio'] = abs(float(data['costo_envio']))
            except (ValueError, TypeError):
                pass

        return super().to_internal_value(data)

class EncomiendaDetailSerializer(serializers.ModelSerializer):
    remitente = ClienteSerializer(read_only=True)
    destinatario = ClienteSerializer(read_only=True)
    ruta = RutaSerializer(read_only=True)
    empleado_registro = EmpleadoSerializer(read_only=True)
    historial_estados = serializers.SerializerMethodField()
    
    # Uso de @property del modelo
    esta_entregada = serializers.BooleanField(read_only=True)
    esta_en_transito = serializers.BooleanField(read_only=True)
    dias_en_transito = serializers.IntegerField(read_only=True)
    tiene_retraso = serializers.BooleanField(read_only=True)
    descripcion_corta = serializers.CharField(read_only=True)
    
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Encomienda
        fields = [
            'id', 'codigo', 'descripcion', 'descripcion_corta', 'peso_kg', 
            'volumen_cm3', 'remitente', 'destinatario', 'ruta', 
            'empleado_registro', 'estado', 'estado_display', 'costo_envio',
            'fecha_registro', 'fecha_entrega_est', 'fecha_entrega_real', 
            'observaciones', 'esta_entregada', 'esta_en_transito', 
            'dias_en_transito', 'tiene_retraso', 'historial_estados'
        ]

    def get_historial_estados(self, obj):
        # Obtener los últimos 5 cambios de estado ordenados por fecha descendente
        historial = obj.historial_estados.all().order_by('-fecha_cambio')[:5]
        return HistorialEstadoSerializer(historial, many=True).data

class EncomiendaV2Serializer(EncomiendaDetailSerializer):
    """
    Versión 2 del serializador de encomiendas con campo meta adicional.
    """
    meta = serializers.SerializerMethodField()

    class Meta(EncomiendaDetailSerializer.Meta):
        fields = EncomiendaDetailSerializer.Meta.fields + ['meta']

    def get_meta(self, obj):
        from django.utils import timezone
        return {
            'version': 'v2',
            'timestamp': timezone.now(),
            'api_status': 'stable',
            'support': 'soporte@encomiendas.com'
        }

class EncomiendaListSerializer(serializers.ModelSerializer):
    """
    Serializer ligero para listados masivos.
    """
    class Meta:
        model = Encomienda
        fields = ['id', 'codigo', 'estado', 'costo_envio', 'fecha_registro']
