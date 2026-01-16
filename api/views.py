from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from .models import Producto, Existencia, Transaccion
from .serializers import ProductoSerializer, ExistenciaSerializer, TransaccionSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para productos.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class ExistenciaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo lectura para consultar el stock actual. 
    No permitimos POST/PUT aquí; el stock cambia vía Transacciones.
    """
    queryset = Existencia.objects.all()
    serializer_class = ExistenciaSerializer

class TransaccionViewSet(viewsets.ModelViewSet):
    """
    Gestión de movimientos de inventario.
    """
    queryset = Transaccion.objects.all().order_by('-fecha')
    serializer_class = TransaccionSerializer

    def get_queryset(self):
        """
        Opcional: Filtrar historial si se pasa un producto_id en la URL
        o filtrar por tipo (ENTRADA/SALIDA) mediante parámetros ?tipo=
        """
        queryset = self.queryset
        producto_id = self.request.query_params.get('producto_id')
        tipo = self.request.query_params.get('tipo')

        if producto_id:
            queryset = queryset.filter(producto_id=producto_id)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
            
        return queryset

    def destroy(self, request, *args, **kwargs):
        """
        Regla de negocio: No se deben borrar transacciones para mantener 
        la integridad del historial.
        """
        return Response(
            {"detail": "No se permite eliminar movimientos de inventario registrados."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )