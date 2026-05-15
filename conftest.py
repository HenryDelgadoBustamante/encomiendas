import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, db):
    user = User.objects.create_user(username='testuser', email='test@encomiendas.com', password='password123')
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def admin_client(api_client, db):
    user = User.objects.create_superuser(username='admin', email='admin@encomiendas.com', password='password123')
    api_client.force_authenticate(user=user)
    return api_client
