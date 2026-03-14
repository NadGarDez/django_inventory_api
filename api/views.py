from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Producto, Transaccion
from .serializers import TransaccionSerializer, ExistenciaConsolidadaSerializer, ProductoSerializer

class ProductoViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para productos.
    """
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class ExistenciaViewSet(viewsets.ModelViewSet):
    """
    CRUD para productos con información de stock integrada.
    """
    # Usamos select_related para que la consulta sea eficiente y no sature la DB
    queryset = Producto.objects.select_related('stock').all()
    serializer_class = ExistenciaConsolidadaSerializer

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        valor_compra_expression = ExpressionWrapper(
            F('stock__cantidad') * F('precio_compra_actual'),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        valor_venta_expression = ExpressionWrapper(
            F('stock__cantidad') * F('precio_venta_actual'),
            output_field=DecimalField(max_digits=18, decimal_places=2),
        )
        resumen = self.get_queryset().aggregate(
            total_productos=Count('id'),
            total_unidades=Coalesce(Sum('stock__cantidad'), 0),
            valor_total_inventario_compra=Coalesce(
                Sum(valor_compra_expression),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            valor_total_inventario_venta=Coalesce(
                Sum(valor_venta_expression),
                Value(0),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )
        resumen['valor_total_inventario_compra'] = str(
            Decimal(resumen['valor_total_inventario_compra']).quantize(Decimal('0.01'))
        )
        resumen['valor_total_inventario_venta'] = str(
            Decimal(resumen['valor_total_inventario_venta']).quantize(Decimal('0.01'))
        )

        return Response(resumen)

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

    def update(self, request, *args, **kwargs):
        """
        Regla de negocio: No se deben editar transacciones para preservar
        el histórico de stock y precios.
        """
        return Response(
            {"detail": "No se permite editar movimientos de inventario registrados."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def partial_update(self, request, *args, **kwargs):
        """
        Regla de negocio: No se deben editar parcialmente transacciones para preservar
        el histórico de stock y precios.
        """
        return Response(
            {"detail": "No se permite editar movimientos de inventario registrados."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )