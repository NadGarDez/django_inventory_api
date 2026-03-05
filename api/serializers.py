from rest_framework import serializers
from .models import Producto, Existencia, Transaccion


class ProductoSerializer(serializers.ModelSerializer):
    # Mostramos el stock actual directamente al consultar el producto
    stock_actual = serializers.IntegerField(source='stock.cantidad', read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'sku', 'stock_actual']

class ExistenciaSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')

    class Meta:
        model = Existencia
        fields = ['producto', 'nombre_producto', 'cantidad', 'ultima_actualizacion']

class ExistenciaConsolidadaSerializer(serializers.ModelSerializer):
    # Traemos campos específicos del modelo Existencia relacionado
    cantidad = serializers.IntegerField(source='stock.cantidad', read_only=True)
    ultima_actualizacion = serializers.DateTimeField(source='stock.ultima_actualizacion', read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'sku', 'nombre', 'cantidad', 'ultima_actualizacion']

class TransaccionSerializer(serializers.ModelSerializer):
    nombre_producto = serializers.ReadOnlyField(source='producto.nombre')
    class Meta:
        model = Transaccion
        fields = ['id', 'producto', 'tipo', 'cantidad', 'fecha', 'observacion', 'nombre_producto']

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