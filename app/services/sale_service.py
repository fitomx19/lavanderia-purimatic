from typing import Dict, Any, Optional, List
from app.repositories.sale_repository import SaleRepository
from app.repositories.card_repository import CardRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.repositories.washer_repository import WasherRepository
from app.repositories.dryer_repository import DryerRepository
from app.schemas.sale_schema import (
    sale_schema,
    sale_update_schema,
    sale_response_schema,
    sales_response_schema
)
from marshmallow import ValidationError
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SaleService:
    """
    Servicio para manejo de ventas con lógica de negocio compleja
    """
    
    def __init__(self):
        self.sale_repository = SaleRepository()
        self.card_repository = CardRepository()
        self.product_repository = ProductRepository()
        self.service_cycle_repository = ServiceCycleRepository()
        self.washer_repository = WasherRepository()
        self.dryer_repository = DryerRepository()
    
    def create_sale(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nueva venta con validaciones completas
        
        Args:
            sale_data: Datos de la venta
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos básicos
            validated_data = sale_schema.load(sale_data)
            if not validated_data or not isinstance(validated_data, dict):
                return {
                    'success': False,
                    'message': 'Error en validación de datos'
                }
            
            # Enriquecer datos con precios y validaciones
            enriched_data = self._enrich_sale_data(validated_data)
            if not enriched_data['success']:
                return enriched_data
            
            sale_data_enriched = enriched_data['data']
            
            # Validar métodos de pago
            payment_validation = self._validate_payments(
                sale_data_enriched['payment_methods'], 
                float(sale_data_enriched['total_amount'])
            )
            if not payment_validation['valid']:
                return {
                    'success': False,
                    'message': payment_validation['message']
                }
            
            # Crear la venta
            sale = self.sale_repository.upsert(sale_data_enriched)
            
            if sale:
                # Procesar pagos (descontar saldos de tarjetas)
                payment_result = self._process_payments(sale['_id'], sale_data_enriched['payment_methods'])
                if not payment_result['success']:
                    # Revertir venta si falla el pago
                    self.sale_repository.update_sale_status(sale['_id'], 'cancelled')
                    return payment_result
                
                sale_response = sale_response_schema.dump(sale)
                return {
                    'success': True,
                    'message': 'Venta creada exitosamente',
                    'data': sale_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al crear la venta'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en venta: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de ventas: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def _enrich_sale_data(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquecer datos de venta con precios y validaciones
        
        Args:
            sale_data: Datos básicos de la venta
            
        Returns:
            Dict: Datos enriquecidos o error
        """
        try:
            items = sale_data.get('items', {})
            products = items.get('products', [])
            services = items.get('services', [])
            
            total_amount = 0
            
            # Procesar productos
            for product_item in products:
                product = self.product_repository.find_by_id(product_item['product_id'])
                if not product:
                    return {
                        'success': False,
                        'message': f"Producto {product_item['product_id']} no encontrado"
                    }
                
                if not product.get('is_active', False):
                    return {
                        'success': False,
                        'message': f"Producto {product.get('nombre', 'desconocido')} no está activo"
                    }
                
                # Verificar stock si existe
                if 'stock' in product and product['stock'] < product_item['quantity']:
                    return {
                        'success': False,
                        'message': f"Stock insuficiente para {product.get('nombre', 'producto')}"
                    }
                
                # Calcular precios
                unit_price = float(product.get('precio', 0))
                quantity = product_item['quantity']
                subtotal = unit_price * quantity
                
                # Actualizar item con precios calculados
                product_item['unit_price'] = float(unit_price)
                product_item['subtotal'] = float(subtotal)
                total_amount += subtotal
            
            # Procesar servicios
            for service_item in services:
                cycle = self.service_cycle_repository.find_by_id(service_item['service_cycle_id'])
                if not cycle:
                    return {
                        'success': False,
                        'message': f"Ciclo de servicio {service_item['service_cycle_id']} no encontrado"
                    }
                
                # Verificar máquina
                machine = self._get_machine_by_id(service_item['machine_id'])
                if not machine:
                    return {
                        'success': False,
                        'message': f"Máquina {service_item['machine_id']} no encontrada"
                    }
                
                if not machine.get('is_active', False):
                    return {
                        'success': False,
                        'message': f"Máquina {service_item['machine_id']} no está activa"
                    }
                
                # Verificar compatibilidad
                machine_type = machine.get('tipo', '')
                validation = self.service_cycle_repository.validate_cycle_for_machine(
                    service_item['service_cycle_id'], 
                    machine_type
                )
                if not validation['valid']:
                    return {
                        'success': False,
                        'message': validation['message']
                    }
                
                # Calcular precio y duración
                price = float(cycle.get('precio', 0))
                duration = cycle.get('duracion', 30)
                
                # Actualizar item con datos calculados
                service_item['price'] = float(price)
                service_item['duration'] = int(duration)
                service_item['machine_type'] = machine_type
                total_amount += price
            
            # Actualizar total si no fue proporcionado
            if not sale_data.get('total_amount'):
                sale_data['total_amount'] = float(total_amount)
            
            # Convertir Decimals en payment_methods a float
            for payment_method in sale_data.get('payment_methods', []):
                if 'amount' in payment_method:
                    payment_method['amount'] = float(payment_method['amount'])
            
            return {
                'success': True,
                'data': sale_data
            }
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos: {e}")
            return {
                'success': False,
                'message': 'Error al procesar datos de venta'
            }
    
    def complete_sale(self, sale_id: str) -> Dict[str, Any]:
        """
        Completar venta y activar servicios
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Obtener la venta
            sale = self.sale_repository.find_by_id(sale_id)
            if not sale:
                return {
                    'success': False,
                    'message': 'Venta no encontrada'
                }
            
            if sale.get('status') != 'pending':
                return {
                    'success': False,
                    'message': 'La venta ya fue procesada'
                }
            
            # Activar servicios (cambiar estado de pending a active)
            services = sale.get('items', {}).get('services', [])
            for i, service in enumerate(services):
                if service.get('status') == 'pending':
                    # Marcar máquina como ocupada y servicio como activo
                    machine_id = service.get('machine_id')
                    if machine_id:
                        self._activate_machine_service(machine_id, sale_id, i)
                    
                    # Actualizar estado del servicio
                    self.sale_repository.update_service_status(sale_id, i, 'active')
            
            # Completar la venta
            updated_sale = self.sale_repository.update_sale_status(sale_id, 'completed')
            
            if updated_sale:
                sale_response = sale_response_schema.dump(updated_sale)
                return {
                    'success': True,
                    'message': 'Venta completada y servicios activados',
                    'data': sale_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al completar la venta'
                }
                
        except Exception as e:
            logger.error(f"Error al completar venta: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_sale_by_id(self, sale_id: str) -> Dict[str, Any]:
        """
        Obtener venta por ID
        
        Args:
            sale_id: ID de la venta
            
        Returns:
            Dict: Información de la venta
        """
        try:
            sale = self.sale_repository.find_by_id(sale_id)
            
            if not sale:
                return {
                    'success': False,
                    'message': 'Venta no encontrada'
                }
            
            sale_response = sale_response_schema.dump(sale)
            return {
                'success': True,
                'message': 'Venta encontrada',
                'data': sale_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener venta: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_sales_list(self, page: int = 1, per_page: int = 10, **filters) -> Dict[str, Any]:
        """
        Obtener lista de ventas con filtros
        
        Args:
            page: Página actual
            per_page: Elementos por página
            **filters: Filtros adicionales (status, employee_id, client_id, date_range)
            
        Returns:
            Dict: Lista de ventas
        """
        try:
            # Aplicar filtros según los parámetros
            if 'employee_id' in filters:
                result = self.sale_repository.find_by_employee(filters['employee_id'], page, per_page)
            elif 'client_id' in filters:
                result = self.sale_repository.find_by_client(filters['client_id'], page, per_page)
            elif 'status' in filters:
                result = self.sale_repository.find_by_status(filters['status'], page, per_page)
            elif 'today' in filters and filters['today']:
                result = self.sale_repository.find_today_sales(page, per_page)
            else:
                # Sin filtros específicos, obtener todas las ventas
                result = self.sale_repository.find_many({}, page, per_page, 'created_at', -1)
            
            sales_response = sales_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Ventas obtenidas exitosamente',
                'data': sales_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de ventas: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_sales_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Obtener resumen de ventas por rango de fechas
        
        Args:
            start_date: Fecha de inicio (YYYY-MM-DD)
            end_date: Fecha de fin (YYYY-MM-DD)
            
        Returns:
            Dict: Resumen de ventas
        """
        try:
            # Convertir strings a datetime
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            summary = self.sale_repository.get_sales_summary(start_dt, end_dt)
            
            return {
                'success': True,
                'message': 'Resumen de ventas obtenido exitosamente',
                'data': summary
            }
            
        except ValueError as e:
            return {
                'success': False,
                'message': 'Formato de fecha inválido. Use YYYY-MM-DD'
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def _validate_payments(self, payment_methods: List[Dict[str, Any]], total_amount: float) -> Dict[str, Any]:
        """Validar métodos de pago y saldos"""
        total_paid = 0
        
        for payment in payment_methods:
            amount = float(payment['amount'])
            total_paid += amount
            
            # Validar pagos con tarjeta recargable
            if payment['payment_type'] == 'tarjeta_recargable':
                card_id = payment.get('card_id')
                if not card_id:
                    return {'valid': False, 'message': 'ID de tarjeta requerido para pago con tarjeta recargable'}
                
                validation = self.card_repository.validate_card_for_payment(card_id, amount)
                if not validation['valid']:
                    return {'valid': False, 'message': f"Tarjeta: {validation['message']}"}
        
        # Verificar que el total de pagos coincida
        if abs(total_paid - total_amount) > 0.01:
            return {'valid': False, 'message': 'El total de pagos no coincide con el monto de la venta'}
        
        return {'valid': True, 'message': 'Pagos válidos'}
    
    def _process_payments(self, sale_id: str, payment_methods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar pagos (descontar saldos de tarjetas)"""
        try:
            for payment in payment_methods:
                if payment['payment_type'] == 'tarjeta_recargable':
                    card_id = payment['card_id']
                    amount = float(payment['amount'])
                    
                    # Descontar saldo de la tarjeta
                    result = self.card_repository.update_balance(card_id, amount, 'subtract')
                    if not result:
                        return {'success': False, 'message': f'Error al procesar pago con tarjeta {card_id}'}
            
            return {'success': True, 'message': 'Pagos procesados exitosamente'}
            
        except Exception as e:
            logger.error(f"Error al procesar pagos: {e}")
            return {'success': False, 'message': 'Error al procesar pagos'}
    
    def _get_machine_by_id(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Obtener máquina por ID (puede ser lavadora o secadora)"""
        # Primero intentar encontrar en lavadoras
        machine = self.washer_repository.find_by_id(machine_id)
        if machine:
            return machine
        
        # Si no está, buscar en secadoras
        return self.dryer_repository.find_by_id(machine_id)
    
    def _activate_machine_service(self, machine_id: str, sale_id: str, service_index: int) -> bool:
        """Activar servicio en máquina"""
        # TODO: Implementar lógica para marcar máquina como ocupada
        # Esto podría incluir agregar un campo 'current_service' a las máquinas
        # Por ahora, solo loggeamos la activación
        logger.info(f"Activando servicio en máquina {machine_id} para venta {sale_id}, servicio {service_index}")
        return True 