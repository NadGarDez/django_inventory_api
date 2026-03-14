from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Producto, Transaccion


class InventarioValorTests(TestCase):
	def setUp(self):
		self.client = APIClient()

	def test_producto_expone_precios_y_valores_actuales_de_inventario(self):
		producto = Producto.objects.create(
			nombre='Teclado',
			sku='TEC-001',
			precio_compra_actual=Decimal('25.50'),
			precio_venta_actual=Decimal('40.00'),
		)

		Transaccion.objects.create(producto=producto, tipo='ENTRADA', cantidad=3)

		response = self.client.get(f'/api/productos/{producto.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['precio_compra_actual'], '25.50')
		self.assertEqual(response.data['precio_venta_actual'], '40.00')
		self.assertEqual(response.data['stock_actual'], 3)
		self.assertEqual(response.data['valor_inventario_compra'], '76.50')
		self.assertEqual(response.data['valor_inventario_venta'], '120.00')

	def test_transaccion_entrada_guarda_precio_de_compra_historico(self):
		producto = Producto.objects.create(
			nombre='Mouse',
			sku='MOU-001',
			precio_compra_actual=Decimal('10.00'),
			precio_venta_actual=Decimal('15.00'),
		)

		transaccion_inicial = Transaccion.objects.create(producto=producto, tipo='ENTRADA', cantidad=2)
		producto.precio_compra_actual = Decimal('12.00')
		producto.save(update_fields=['precio_compra_actual', 'updated_at'])
		transaccion_nueva = Transaccion.objects.create(producto=producto, tipo='ENTRADA', cantidad=1)

		transaccion_inicial.refresh_from_db()
		transaccion_nueva.refresh_from_db()

		self.assertEqual(transaccion_inicial.precio_unitario_historico, Decimal('10.00'))
		self.assertEqual(transaccion_inicial.valor_movimiento, Decimal('20.00'))
		self.assertEqual(transaccion_nueva.precio_unitario_historico, Decimal('12.00'))
		self.assertEqual(transaccion_nueva.valor_movimiento, Decimal('12.00'))

		response = self.client.get(f'/api/transacciones/{transaccion_inicial.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['precio_unitario_historico'], '10.00')
		self.assertEqual(response.data['valor_movimiento'], '20.00')

	def test_transaccion_salida_guarda_precio_de_venta_historico(self):
		producto = Producto.objects.create(
			nombre='Webcam',
			sku='WEB-001',
			precio_compra_actual=Decimal('18.00'),
			precio_venta_actual=Decimal('30.00'),
		)

		Transaccion.objects.create(producto=producto, tipo='ENTRADA', cantidad=5)
		transaccion_salida = Transaccion.objects.create(producto=producto, tipo='SALIDA', cantidad=2)

		self.assertEqual(transaccion_salida.precio_unitario_historico, Decimal('30.00'))
		self.assertEqual(transaccion_salida.valor_movimiento, Decimal('60.00'))

		response = self.client.get(f'/api/transacciones/{transaccion_salida.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['precio_unitario_historico'], '30.00')
		self.assertEqual(response.data['valor_movimiento'], '60.00')

	def test_resumen_de_existencias_calcula_valores_totales_compra_y_venta(self):
		producto_a = Producto.objects.create(
			nombre='Monitor',
			sku='MON-001',
			precio_compra_actual=Decimal('100.00'),
			precio_venta_actual=Decimal('150.00'),
		)
		producto_b = Producto.objects.create(
			nombre='Cable HDMI',
			sku='CAB-001',
			precio_compra_actual=Decimal('5.00'),
			precio_venta_actual=Decimal('8.00'),
		)

		Transaccion.objects.create(producto=producto_a, tipo='ENTRADA', cantidad=2)
		Transaccion.objects.create(producto=producto_b, tipo='ENTRADA', cantidad=4)

		response = self.client.get('/api/existencias/resumen/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['total_productos'], 2)
		self.assertEqual(response.data['total_unidades'], 6)
		self.assertEqual(response.data['valor_total_inventario_compra'], '220.00')
		self.assertEqual(response.data['valor_total_inventario_venta'], '332.00')

	def test_no_se_permite_editar_ni_eliminar_transacciones(self):
		producto = Producto.objects.create(
			nombre='Router',
			sku='ROU-001',
			precio_compra_actual=Decimal('50.00'),
			precio_venta_actual=Decimal('75.00'),
		)

		transaccion = Transaccion.objects.create(producto=producto, tipo='ENTRADA', cantidad=2)

		put_response = self.client.put(
			f'/api/transacciones/{transaccion.id}/',
			{
				'producto': producto.id,
				'tipo': 'ENTRADA',
				'cantidad': 10,
				'observacion': 'Intento de edicion',
			},
			format='json',
		)
		patch_response = self.client.patch(
			f'/api/transacciones/{transaccion.id}/',
			{'cantidad': 10},
			format='json',
		)
		delete_response = self.client.delete(f'/api/transacciones/{transaccion.id}/')

		transaccion.refresh_from_db()

		self.assertEqual(put_response.status_code, 405)
		self.assertEqual(patch_response.status_code, 405)
		self.assertEqual(delete_response.status_code, 405)
		self.assertEqual(transaccion.cantidad, 2)
