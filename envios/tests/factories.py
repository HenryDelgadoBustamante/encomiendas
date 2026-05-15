import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from envios.models import Empleado, Encomienda, HistorialEstado
from clientes.models import Cliente
from rutas.models import Ruta
from faker import Faker

fake = Faker()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user_{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@encomiendas.com')
    is_staff = False

class ClienteFactory(DjangoModelFactory):
    class Meta:
        model = Cliente
    
    nombres = factory.Faker('first_name')
    apellidos = factory.Faker('last_name')
    nro_doc = factory.Sequence(lambda n: f'DNI{n:08d}')
    email = factory.Faker('email')
    telefono = factory.Sequence(lambda n: f'9{n:08d}')
    direccion = factory.Faker('address')

class RutaFactory(DjangoModelFactory):
    class Meta:
        model = Ruta
    
    codigo = factory.Sequence(lambda n: f'R{n:03d}')
    origen = factory.Faker('city')
    destino = factory.Faker('city')
    precio_base = factory.Faker('random_int', min=10, max=100)
    dias_entrega = factory.Faker('random_int', min=1, max=5)

class EmpleadoFactory(DjangoModelFactory):
    class Meta:
        model = Empleado
    
    codigo = factory.Sequence(lambda n: f'EMP{n:04d}')
    nombres = factory.Faker('first_name')
    apellidos = factory.Faker('last_name')
    cargo = 'Agente'
    email = factory.LazyAttribute(lambda o: f'{o.codigo.lower()}@encomiendas.com')
    telefono = factory.Sequence(lambda n: f'8{n:08d}')
    fecha_ingreso = factory.Faker('date_this_decade')

class EncomiendaFactory(DjangoModelFactory):
    class Meta:
        model = Encomienda
    
    codigo = factory.Sequence(lambda n: f'ENC-2024-{n:06d}')
    descripcion = factory.Faker('sentence')
    peso_kg = factory.Faker('random_int', min=1, max=50)
    remitente = factory.SubFactory(ClienteFactory)
    destinatario = factory.SubFactory(ClienteFactory)
    ruta = factory.SubFactory(RutaFactory)
    empleado_registro = factory.SubFactory(EmpleadoFactory)
    costo_envio = factory.Faker('random_int', min=50, max=500)
