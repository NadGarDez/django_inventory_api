from rest_framework import serializers
from .models import Producto, Existencia, Transaccion


class ProductoSerializer(serializers.ModelSerializer):
    stock_actual = serializers.IntegerField(read_only=True)
    valor_inventario_compra = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    valor_inventario_venta = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'sku',
            'precio_compra_actual',
            'precio_venta_actual',
            'stock_actual',
            'valor_inventario_compra',
            'valor_inventario_venta',
            'created_at',
            'updated_at',
        ]

class ExistenciaSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')
    precio_compra_actual = serializers.DecimalField(source='producto.precio_compra_actual', max_digits=12, decimal_places=2, read_only=True)
    precio_venta_actual = serializers.DecimalField(source='producto.precio_venta_actual', max_digits=12, decimal_places=2, read_only=True)
    valor_inventario_compra = serializers.DecimalField(source='producto.valor_inventario_compra', max_digits=12, decimal_places=2, read_only=True)
    valor_inventario_venta = serializers.DecimalField(source='producto.valor_inventario_venta', max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Existencia
        fields = [
            'producto',
            'nombre_producto',
            'precio_compra_actual',
            'precio_venta_actual',
            'cantidad',
            'valor_inventario_compra',
            'valor_inventario_venta',
            'ultima_actualizacion',
        ]

class ExistenciaConsolidadaSerializer(serializers.ModelSerializer):
    cantidad = serializers.IntegerField(source='stock_actual', read_only=True)
    ultima_actualizacion = serializers.SerializerMethodField()
    precio_compra_actual = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    precio_venta_actual = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    valor_inventario_compra = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    valor_inventario_venta = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Producto
        fields = [
            'id',
            'sku',
            'nombre',
            'precio_compra_actual',
            'precio_venta_actual',
            'cantidad',
            'valor_inventario_compra',
            'valor_inventario_venta',
            'ultima_actualizacion',
        ]

    def get_ultima_actualizacion(self, obj):
        if hasattr(obj, 'stock'):
            return obj.stock.ultima_actualizacion
        return None

class TransaccionSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')
    valor_movimiento = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Transaccion
        fields = [
            'id',
            'producto',
            'tipo',
            'cantidad',
            'precio_unitario_historico',
            'valor_movimiento',
            'fecha',
            'observacion',
            'nombre_producto',
        ]
        read_only_fields = ['precio_unitario_historico', 'valor_movimiento']

    def validate(self, data):
        """
        Validación para evitar stock negativo en salidas.
        """
        if data['tipo'] == 'SALIDA':
            try:
                existencia = Existencia.objects.get(producto=data['producto'])
                if existencia.cantidad < data['cantidad']:
                    raise serializers.ValidationError({
                        "cantidad": f"Stock insuficiente. Disponible: {existencia.cantidad}"
                    })
            except Existencia.DoesNotExist:
                raise serializers.ValidationError({
                    "producto": "Este producto no tiene registro de existencias."
                })
        return data