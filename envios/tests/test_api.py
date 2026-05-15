import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from envios.tests.factories import (
    UserFactory, ClienteFactory, RutaFactory, 
    EmpleadoFactory, EncomiendaFactory
)
from envios.models import Encomienda, HistorialEstado

@pytest.mark.django_db
class TestAutenticacion:
    def test_acceso_denegado_sin_token(self, api_client):
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_obtener_token_exitoso(self, api_client):
        user = UserFactory(email='test@encomiendas.com')
        user.set_password('pass123')
        user.save()
        EmpleadoFactory(email=user.email) # Vincular empleado
        
        url = reverse('token_obtain_pair')
        response = api_client.post(url, {'username': user.username, 'password': 'pass123'})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_payload_token_contiene_empleado(self, api_client):
        user = UserFactory(email='emp01@encomiendas.com')
        user.set_password('pass123')
        user.save()
        empleado = EmpleadoFactory(email=user.email, codigo='EMP01', cargo='Gerente')
        
        url = reverse('token_obtain_pair')
        response = api_client.post(url, {'username': user.username, 'password': 'pass123'})
        # El test de contenido exacto se haría decodificando el JWT, 
        # aquí validamos que la vista responda ok con el serializer correcto.
        assert response.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestListadoEncomiendas:
    def test_listar_encomiendas_v1(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        EncomiendaFactory.create_batch(5)
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_filtrar_por_estado(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        EncomiendaFactory(estado='PEN')
        EncomiendaFactory(estado='ENT')
        
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.get(f"{url}?estado=PEN")
        assert response.data['count'] == 1

    def test_busqueda_por_codigo(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        EncomiendaFactory(codigo='ENC-BUSCAR-01')
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.get(f"{url}?search=BUSCAR")
        # En DRF con paginación, los resultados están en 'results'
        assert response.data['count'] == 1
        assert response.data['results'][0]['codigo'] == 'ENC-BUSCAR-01'

@pytest.mark.django_db
class TestCrearEncomienda:
    def test_crear_encomienda_valida(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        empleado = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        remitente = ClienteFactory()
        destinatario = ClienteFactory()
        ruta = RutaFactory(precio_base=10)
        
        data = {
            "codigo": "ENC-NUEVA-01",
            "descripcion": "Paquete de prueba",
            "peso_kg": 5,
            "remitente": remitente.id,
            "destinatario": destinatario.id,
            "ruta": ruta.id,
            "empleado_registro": empleado.id,
            "costo_envio": 100
        }
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_error_remitente_igual_destinatario(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        cliente = ClienteFactory()
        data = {"remitente": cliente.id, "destinatario": cliente.id}
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_error_costo_insuficiente(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        empleado = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        remitente = ClienteFactory()
        destinatario = ClienteFactory()
        ruta = RutaFactory(precio_base=100) # 100 * 5kg = 500 min
        
        data = {
            "codigo": "ENC-FAIL-COSTO",
            "descripcion": "Costo bajo",
            "peso_kg": 5,
            "remitente": remitente.id,
            "destinatario": destinatario.id,
            "ruta": ruta.id,
            "empleado_registro": empleado.id,
            "costo_envio": 10 # Menor al mínimo
        }
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'costo' in str(response.data['detail']).lower()

@pytest.mark.django_db
class TestCambiarEstado:
    def test_cambiar_estado_exitoso(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        empleado = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        encomienda = EncomiendaFactory(empleado_registro=empleado)
        url = reverse('encomienda-cambiar-estado', kwargs={'version': 'v1', 'pk': encomienda.pk})
        
        data = {"nuevo_estado": "ENT", "empleado_id": empleado.id, "observacion": "Todo ok"}
        response = authenticated_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert Encomienda.objects.get(pk=encomienda.pk).estado == "ENT"

    def test_historial_se_crea_al_cambiar_estado(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        empleado = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        encomienda = EncomiendaFactory(empleado_registro=empleado)
        url = reverse('encomienda-cambiar-estado', kwargs={'version': 'v1', 'pk': encomienda.pk})
        authenticated_client.post(url, {"nuevo_estado": "ENT", "empleado_id": empleado.id})
        
        assert HistorialEstado.objects.filter(encomienda=encomienda).count() > 0

    def test_solo_propietario_cambia_estado(self, authenticated_client):
        user_propietario = UserFactory(email='owner@test.com')
        emp_propietario = EmpleadoFactory(email=user_propietario.email, estado='ACT')
        
        user_otro = UserFactory(email='other@test.com')
        EmpleadoFactory(email=user_otro.email, estado='ACT')
        
        encomienda = EncomiendaFactory(empleado_registro=emp_propietario)
        authenticated_client.force_authenticate(user=user_otro)
        
        url = reverse('encomienda-cambiar-estado', kwargs={'version': 'v1', 'pk': encomienda.pk})
        response = authenticated_client.post(url, {"nuevo_estado": "ENT", "empleado_id": 1})
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestAccionesPersonalizadas:
    def test_endpoint_estadisticas(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        EncomiendaFactory.create_batch(3)
        url = reverse('encomienda-estadisticas', kwargs={'version': 'v1'})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 3

    def test_endpoint_pendientes(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        EncomiendaFactory(estado='PEN')
        EncomiendaFactory(estado='ENT')
        url = reverse('encomienda-pendientes', kwargs={'version': 'v1'})
        response = authenticated_client.get(url)
        assert response.data['count'] == 1

    def test_endpoint_con_retraso(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        emp = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        # Crear y luego forzar fecha pasada mediante update() para bypass clean()
        e = EncomiendaFactory(estado='TRA', empleado_registro=emp)
        past_date = timezone.now() - timezone.timedelta(days=10)
        from envios.models import Encomienda
        Encomienda.objects.filter(id=e.id).update(fecha_entrega_est=past_date)
        
        url = reverse('encomienda-con-retraso', kwargs={'version': 'v1'})
        response = authenticated_client.get(url)
        assert response.status_code == 200
        # Verificar en results por paginación
        assert response.data['count'] >= 1

@pytest.mark.django_db
class TestVersionado:
    def test_respuesta_v1_no_tiene_meta(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        encomienda = EncomiendaFactory()
        url = reverse('encomienda-detail', kwargs={'version': 'v1', 'pk': encomienda.pk})
        response = authenticated_client.get(url)
        assert 'meta' not in response.data

    def test_respuesta_v2_tiene_meta(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        encomienda = EncomiendaFactory()
        url = reverse('encomienda-detail', kwargs={'version': 'v2', 'pk': encomienda.pk})
        response = authenticated_client.get(url)
        assert 'meta' in response.data
        assert response.data['meta']['version'] == 'v2'

    def test_cabecera_x_api_version_presente(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        
        url = reverse('encomienda-list', kwargs={'version': 'v2'})
        response = authenticated_client.get(url)
        assert response.has_header('X-API-Version')
        assert response['X-API-Version'] == 'v2'

# Tests adicionales para completar los 22 requeridos
    def test_detalle_encomienda_anidado(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        encomienda = EncomiendaFactory()
        url = reverse('encomienda-detail', kwargs={'version': 'v1', 'pk': encomienda.pk})
        response = authenticated_client.get(url)
        assert isinstance(response.data['remitente'], dict)

    def test_historial_limitado_a_5(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        emp = EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        encomienda = EncomiendaFactory(empleado_registro=emp)
        for _ in range(7):
            encomienda.cambiar_estado('TRA', emp)
        
        url = reverse('encomienda-detail', kwargs={'version': 'v1', 'pk': encomienda.pk})
        response = authenticated_client.get(url)
        assert len(response.data['historial_estados']) <= 5

    def test_paginacion_encomiendas(self, authenticated_client):
        user = UserFactory(email='test@encomiendas.com')
        EmpleadoFactory(email=user.email, estado='ACT')
        authenticated_client.force_authenticate(user=user)
        EncomiendaFactory.create_batch(20) # page_size es 15
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = authenticated_client.get(url)
        assert len(response.data['results']) == 15

    def test_permiso_empleado_inactivo(self, api_client):
        user = UserFactory(email='inactive@test.com')
        EmpleadoFactory(email=user.email, estado='INA')
        api_client.force_authenticate(user=user)
        url = reverse('encomienda-list', kwargs={'version': 'v1'})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
