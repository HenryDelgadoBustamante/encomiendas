from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from envios.viewsets import EncomiendaViewSet, RutaViewSet
from envios.api_views import ClienteListView, RutaListView
from api.auth_views import EncomiendaTokenView

router = DefaultRouter()
router.register(r'encomiendas', EncomiendaViewSet, basename='encomienda')
router.register(r'rutas-v2', RutaViewSet, basename='ruta')

urlpatterns = [
    # Documentación de la API
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # Autenticación JWT
    path('token/', EncomiendaTokenView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Router Automático
    path('<str:version>/', include(router.urls)),
    
    # Vistas Genéricas Manuales
    path('<str:version>/clientes/', ClienteListView.as_view(), name='cliente-list'),
    path('<str:version>/rutas/', RutaListView.as_view(), name='ruta-list'),
]
