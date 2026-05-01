from django.urls import path
from . import views

app_name = 'envios'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.encomienda_list, name='lista'),
    path('crear/', views.encomienda_create, name='crear'),
    path('<int:pk>/', views.encomienda_detail, name='detalle'),
    path('<int:pk>/cambiar-estado/', views.encomienda_cambiar_estado, name='cambiar_estado'),
    path('<int:pk>/editar/', views.encomienda_update, name='editar'),
    path('<int:pk>/eliminar/', views.encomienda_delete, name='eliminar'),
]
