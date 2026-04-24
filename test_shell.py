from django.core.exceptions import ValidationError
from django.utils import timezone
from clientes.models import Cliente
from rutas.models import Ruta
from envios.models import Empleado, Encomienda, HistorialEstado
from config.choices import TipoDocumento, EstadoGeneral, EstadoEnvio
import datetime

print("\n--- INICIANDO PRUEBAS DE LA SESIÓN 03 ---")

print("1. Creando Cliente, Ruta y Empleado...")
cliente = Cliente.objects.create(
    tipo_doc=TipoDocumento.DNI,
    nro_doc='12345678',
    nombres='Carlos',
    apellidos='Ramirez',
    email='carlos.ramirez@example.com',
    telefono='987654321',
    direccion='Av. Siempre Viva 123'
)

cliente_dest = Cliente.objects.create(
    tipo_doc=TipoDocumento.DNI,
    nro_doc='87654321',
    nombres='Maria',
    apellidos='Gomez',
    email='maria.gomez@example.com',
    telefono='912345678',
    direccion='Av. Los Alamos 456'
)

ruta = Ruta.objects.create(
    codigo='RUT-01',
    origen='Lima',
    destino='Arequipa',
    precio_base=15.50,
    dias_entrega=2
)

empleado = Empleado.objects.create(
    codigo='EMP-001',
    nombres='Juan',
    apellidos='Perez',
    cargo='Despachador',
    email='juan.perez@empresa.com',
    telefono='999888777',
    fecha_ingreso=datetime.date.today()
)

print("2. Creando Encomienda con validaciones correctas...")
encomienda = Encomienda.crear_con_costo_calculado(
    descripcion='Paquete de prueba válido',
    peso_kg=10.5,
    remitente=cliente,
    destinatario=cliente_dest,
    ruta=ruta,
    empleado_registro=empleado
)
print(f"✅ Encomienda creada con éxito: {encomienda.codigo} | Costo calculado: {encomienda.costo_envio}")

print("\n3. Lanzando ValidationError con datos incorrectos (peso negativo)...")
encomienda_invalida = Encomienda(
    codigo='ENC-FAIL-01',
    descripcion='Paquete inválido',
    peso_kg=-5,  # ESTO DEBE FALLAR
    costo_envio=10.0,
    remitente=cliente,
    destinatario=cliente_dest,
    ruta=ruta,
    empleado_registro=empleado
)
try:
    encomienda_invalida.full_clean()
    print("❌ ERROR: El validador falló y permitió un peso negativo.")
except ValidationError as e:
    print(f"✅ Se capturó ValidationError correctamente: {e}")

print("\n4. Lanzando ValidationError (remitente y destinatario iguales)...")
encomienda_invalida2 = Encomienda(
    codigo='ENC-FAIL-02',
    descripcion='Paquete inválido',
    peso_kg=5,
    costo_envio=10.0,
    remitente=cliente,
    destinatario=cliente,  # ESTO DEBE FALLAR POR EL clean()
    ruta=ruta,
    empleado_registro=empleado
)
try:
    encomienda_invalida2.full_clean()
    print("❌ ERROR: El validador falló y permitió remitente=destinatario.")
except ValidationError as e:
    print(f"✅ Se capturó ValidationError correctamente: {e}")

print("\n5. Usar cambiar_estado() y verificar HistorialEstado...")
encomienda.cambiar_estado(EstadoEnvio.EN_TRANSITO, empleado, "Salió de almacén")
print(f"Estado de encomienda ahora es: {encomienda.get_estado_display()}")
historial_count = HistorialEstado.objects.filter(encomienda=encomienda).count()
print(f"✅ Registros en HistorialEstado: {historial_count}")

print("\n6. Usar Cliente.objects.activos()...")
activos = Cliente.objects.activos()
print(f"Clientes activos encontrados: {activos.count()} (Ej: {activos.first()})")

print("\n7. Usar Cliente.objects.buscar('rami')...")
encontrados = Cliente.objects.buscar('rami')
print(f"Clientes con 'rami' encontrados: {encontrados.count()} (Ej: {encontrados.first()})")

print("\n8. Usar Encomienda.objects.pendientes()...")
print(f"Encomiendas pendientes: {Encomienda.objects.pendientes().count()}")

print("\n9. Usar Encomienda.objects.activas()...")
print(f"Encomiendas activas: {Encomienda.objects.activas().count()}")

print("\n10. Usar Encomienda.objects.con_retraso()...")
print(f"Encomiendas con retraso: {Encomienda.objects.con_retraso().count()}")

print("\n11. Usar Encomienda.objects.activas().por_ruta(r).count()...")
count_rutas = Encomienda.objects.activas().por_ruta(ruta).count()
print(f"Encomiendas activas en ruta {ruta}: {count_rutas}")

print("\n12. Test de propieades en modelo Cliente...")
print(f"Cliente {cliente.nombre_completo} tiene esta_activo: {cliente.esta_activo} y total enviadas: {cliente.total_encomiendas_enviadas}")

print("\n13. Test de propiedades en modelo Encomienda...")
print(f"Encomienda {encomienda.codigo} - Entregada: {encomienda.esta_entregada}, Retraso: {encomienda.tiene_retraso}, Días Transito: {encomienda.dias_en_transito}, Desc Corta: {encomienda.descripcion_corta}")

print("\n--- PRUEBAS FINALIZADAS EXITOSAMENTE ---")
