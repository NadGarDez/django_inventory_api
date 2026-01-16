from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, TransaccionViewSet, ExistenciaViewSet

# Creamos el router y registramos los viewsets
router = DefaultRouter()
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'transacciones', TransaccionViewSet, basename='transaccion')
router.register(r'existencias', ExistenciaViewSet, basename='existencia')

urlpatterns = [
    path('', include(router.urls)),
    
    # Ruta adicional sugerida para historial por producto
    path('productos/<int:producto_id>/historial/', 
         TransaccionViewSet.as_view({'get': 'list'}), 
         name='producto-historial'),
]