from typing import Dict, Any, Optional, List
from app.repositories.sale_repository import SaleRepository
from app.repositories.card_repository import CardRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.repositories.washer_repository import WasherRepository
from app.repositories.dryer_repository import DryerRepository
from app.services.nfc_payment_service import NFCPaymentService
from app.schemas.sale_schema import (
    sale_schema,
    sale_update_schema,
    sale_response_schema,
    sales_response_schema
)

# Agregar esta importación al inicio del archivo
from app.services.esp32_service import ESP32Service
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
        self.nfc_payment_service = NFCPaymentService()
        self.esp32_service = ESP32Service()  
        self._esp32_last_error: Optional[str] = None
    
    def create_sale(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nueva venta con validaciones completas
        
        Args:
            sale_data: Datos de la venta
            
        Returns:
            Dict: Resultado de la operación
        """
        logger.info(f"🔍 [sale_service] Iniciando create_sale")
        logger.info(f"🔍 [sale_service] Datos recibidos: {sale_data}")
        
        try:
            # Validar datos básicos
            logger.info(f"🔍 [sale_service] Validando datos con schema...")
            validated_data = sale_schema.load(sale_data)
            logger.info(f"🔍 [sale_service] Datos validados exitosamente: {validated_data}")
            
            if not validated_data or not isinstance(validated_data, dict):
                return {
                    'success': False,
                    'message': 'Error en validación de datos'
                }
            
            # Asegurar que el store_id esté presente
            if 'store_id' not in validated_data:
                return {
                    'success': False,
                    'message': 'El ID de la tienda (store_id) es requerido'
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
                
                # Actualizar stock de productos
                product_update_result = self._update_product_stock(sale_data_enriched['items'].get('products', []))
                if not product_update_result['success']:
                    # Considerar revertir venta si falla el stock (ej: devolver saldo de tarjetas)
                    self.sale_repository.update_sale_status(sale['_id'], 'cancelled')
                    return product_update_result

                sale_response = sale_response_schema.dump(sale)

                # Marcar máquinas asociadas como ocupadas al crear la venta
                for idx, service_item in enumerate(sale_data_enriched['items'].get('services', [])):
                    machine_id = service_item.get('machine_id')
                    if machine_id:
                        self._mark_machine_occupied_on_sale_creation(
                            machine_id,
                            sale['_id'],
                            idx, # Pasar el índice del servicio
                            service_item.get('service_cycle_id')
                        )

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
            logger.error(f"❌ [sale_service] Error de validación en venta: {e.messages}")
            logger.error(f"❌ [sale_service] Error completo: {e}")
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
    
    def _mark_machine_occupied_on_sale_creation(self, machine_id: str, sale_id: str, service_index: int, service_cycle_id: str):
        """
        Marca la máquina como 'ocupada' y establece la información del servicio actual
        cuando se crea una venta.
        """
        try:
            machine = self._get_machine_by_id(machine_id)
            if machine:
                update_data = {
                    'estado': 'ocupada',
                    'current_service': {
                        'sale_id': sale_id,
                        'service_index': service_index,
                        'service_cycle_id': service_cycle_id,
                    }
                }
                if machine.get('tipo') == 'lavadora':
                    self.washer_repository.upsert({'_id': machine_id, **update_data})
                elif machine.get('tipo') == 'secadora':
                    self.dryer_repository.upsert({'_id': machine_id, **update_data})
                else:
                    logger.warning(f"Tipo de máquina desconocido para {machine_id}. No se pudo actualizar el estado a ocupada.")
        except Exception as e:
            logger.error(f"Error al marcar máquina {machine_id} como ocupada en creación de venta: {e}")

    def _enrich_sale_data(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enriquecer datos de venta con precios y validaciones
        
        Args:
            sale_data: Datos básicos de la venta
            
        Returns:
            Dict: Datos enriquecidos o error
        """

        logger.info(f"Datos sin enriquecer: {sale_data}")
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
                    service_item['machine_id'],
                    machine_type
                )
                if not validation['valid']:
                    return {
                        'success': False,
                        'message': validation['message']
                    }
                
                # Calcular precio y duración basado en el tipo de servicio
                price = 0.0
                if cycle.get('service_type') == 'encargo_lavado':
                    # Intentar convertir weight_kg a float primero
                    try:
                        weight_kg_val = float(service_item.get('weight_kg', 0)) # Usar .get para evitar KeyError
                    except (ValueError, TypeError):
                        return {
                            'success': False,
                            'message': 'Peso en kilogramos inválido para encargo_lavado. Debe ser un número.'
                        }

                    if weight_kg_val <= 0:
                        return {
                            'success': False,
                            'message': 'Peso en kilogramos debe ser un número positivo para encargo_lavado.'
                        }
                    price = float(service_item['price']) # Usar el precio calculado enviado desde el frontend
                    service_item['weight_kg'] = weight_kg_val # Actualizar el ítem con el valor flotante
                else:
                    price = float(cycle.get('price', 0)) # Usar el precio fijo del ciclo de servicio

                duration = cycle.get('duration_minutes', 30)
                
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
                    service_cycle_id = service.get('service_cycle_id')
                    duration = service.get('duration') # Duración en minutos

                    if machine_id and service_cycle_id and duration is not None:
                        # Capturar los valores de started_at y estimated_end_at
                        success, started_at_val, estimated_end_at_val = self._activate_machine_service(
                            machine_id, sale_id, i, service_cycle_id, duration
                        )
                        if success:
                            # Actualizar estado del servicio en la venta, pasando los nuevos tiempos
                            self.sale_repository.update_service_status(
                                sale_id, i, 'active', started_at=started_at_val, estimated_end_at=estimated_end_at_val
                            )
                        else:
                            # Falla ESP32: revertir estado de la máquina y no continuar la operación
                            error_message = getattr(self, '_esp32_last_error', None) or \
                                f"ESP32: fallo de activación para máquina {machine_id}"
                            logger.error(error_message)

                            try:
                                # Revertir máquina a disponible y limpiar current_service
                                revert_ops = {
                                    '$set': {'estado': 'disponible'},
                                    '$unset': {'current_service': ''}
                                }
                                updated_machine = None
                                machine = self._get_machine_by_id(machine_id)
                                if machine:
                                    if machine.get('tipo') == 'lavadora':
                                        self.washer_repository.update_document_by_id(machine_id, revert_ops)
                                        updated_machine = self.washer_repository.find_by_id(machine_id)
                                    elif machine.get('tipo') == 'secadora' or 'capacidad' in machine:
                                        self.dryer_repository.update_document_by_id(machine_id, revert_ops)
                                        updated_machine = self.dryer_repository.find_by_id(machine_id)
                                if updated_machine:
                                    self._emit_machine_update(machine_id, updated_machine, 'available')
                            except Exception as revert_err:
                                logger.error(f"Error revirtiendo estado de máquina {machine_id} tras fallo ESP32: {revert_err}")

                            return {
                                'success': False,
                                'message': error_message,
                                'error_type': 'esp32_activation_failed'
                            }
                    
                    # La actualización del estado se mueve dentro del if success
                    # self.sale_repository.update_service_status(sale_id, i, 'active') 
            
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
    
    def get_sales_list(self, page: int = 1, per_page: int = 10, exclude_finalized: bool = False, **filters) -> Dict[str, Any]:
        """
        Obtener lista de ventas con filtros, incluyendo la opción de excluir ventas finalizadas.
        
        Args:
            page: Página actual
            per_page: Elementos por página
            exclude_finalized: Si es True, no incluir ventas con estado 'finalized'.
            **filters: Filtros adicionales (status, employee_id, client_id, date_range)
            
        Returns:
            Dict: Lista de ventas
        """
        try:
            query_filters = {} # Filtros base para la consulta

            if exclude_finalized:
                query_filters['status'] = {'$ne': 'finalized'}
            
            # Aplicar filtros específicos si existen
            if 'employee_id' in filters:
                query_filters['employee_id'] = filters['employee_id']
            elif 'client_id' in filters:
                query_filters['client_id'] = filters['client_id']
            elif 'status' in filters:
                query_filters['status'] = filters['status']
            elif 'today' in filters and filters['today']:
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                tomorrow = today + timedelta(days=1)
                query_filters['created_at'] = {'$gte': today, '$lte': tomorrow}
            
            # Obtener ventas usando find_many con los filtros combinados
            result = self.sale_repository.find_many(query_filters, page, per_page, 'created_at', -1)
            
            return {
                'success': True,
                'message': 'Ventas obtenidas exitosamente',
                'data': result['documents'],
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
                # CASOS: card_id tradicional vs nfc_uid
                card_id = payment.get('card_id')
                nfc_uid = payment.get('nfc_uid')
                
                if nfc_uid:
                    # NUEVO: Validación NFC
                    validation = self.card_repository.validate_nfc_payment(nfc_uid, amount)
                    if not validation['valid']:
                        return {'valid': False, 'message': f"Tarjeta NFC: {validation['message']}"}
                elif card_id:
                    # EXISTENTE: Validación por card_id
                    validation = self.card_repository.validate_card_for_payment(card_id, amount)
                    if not validation['valid']:
                        return {'valid': False, 'message': f"Tarjeta: {validation['message']}"}
                else:
                    return {'valid': False, 'message': 'ID de tarjeta o UID NFC requerido para pago con tarjeta recargable'}
        
        # Verificar que el total de pagos coincida
        if abs(total_paid - total_amount) > 0.01:
            return {'valid': False, 'message': 'El total de pagos no coincide con el monto de la venta'}
        
        return {'valid': True, 'message': 'Pagos válidos'}
    
    def _process_payments(self, sale_id: str, payment_methods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Procesar pagos (descontar saldos de tarjetas)"""
        try:
            for payment in payment_methods:
                if payment['payment_type'] == 'tarjeta_recargable':
                    amount = float(payment['amount'])
                    card_id = payment.get('card_id')
                    nfc_uid = payment.get('nfc_uid')
                    
                    if nfc_uid:
                        # NUEVO: Procesar pago NFC
                        result = self.card_repository.process_nfc_payment(nfc_uid, amount)
                        if not result['success']:
                            return {'success': False, 'message': f'Error al procesar pago NFC: {result["message"]}'}
                    elif card_id:
                        # EXISTENTE: Procesar pago tradicional
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

    def _update_product_stock(self, products_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Actualizar el stock de productos después de una venta.
        
        Args:
            products_data: Lista de productos vendidos con quantity.
            
        Returns:
            Dict: Resultado de la operación.
        """
        try:
            for product_item in products_data:
                product_id = product_item['product_id']
                quantity = product_item['quantity']
                
                # Restar la cantidad del stock
                result = self.product_repository.update_stock(product_id, quantity, 'reducir')
                if not result:
                    return {'success': False, 'message': f'Error al actualizar stock del producto {product_id}'}
            
            return {'success': True, 'message': 'Stock de productos actualizado exitosamente'}
        except Exception as e:
            logger.error(f"Error al actualizar stock de productos: {e}")
            return {'success': False, 'message': 'Error al actualizar stock de productos'}

    def _activate_machine_service(self, machine_id: str, sale_id: str, service_index: int, service_cycle_id: str, duration_minutes: int) -> tuple[bool, Optional[datetime], Optional[datetime]]:
        """
        Activar servicio en máquina y calcular tiempo de finalización.
        (El estado 'ocupada' se establece al crear la venta)
        
        Args:
            machine_id: ID de la máquina
            sale_id: ID de la venta
            service_index: Índice del servicio en la lista de la venta
            service_cycle_id: ID del ciclo de servicio
            duration_minutes: Duración del ciclo en minutos
            
        Returns:
            tuple[bool, Optional[datetime], Optional[datetime]]: (éxito, started_at, estimated_end_at)
        """
        try:
            current_time = datetime.utcnow()
            estimated_end_time = current_time + timedelta(minutes=duration_minutes)

            # Determinar si es lavadora o secadora y actualizar el repositorio correspondiente
            machine = self._get_machine_by_id(machine_id)
            if not machine:
                logger.error(f"Máquina {machine_id} no encontrada para activación.")
                return False, None, None # Devuelve False y None para los tiempos

            # NUEVO: Enviar comando al ESP32 físico. Si falla, cancelar la operación
            try:
                esp32_id = machine.get('esp32_id')
                if not esp32_id:
                    self._esp32_last_error = f"ESP32: máquina {machine_id} sin esp32_id configurado"
                    logger.error(self._esp32_last_error)
                    return False, None, None

                machine_data = {
                    'machine_id': machine_id,
                    'start_time': current_time.strftime('%H:%M:%S'),
                    'end_time': estimated_end_time.strftime('%H:%M:%S'),
                    'service_cycle_id': service_cycle_id,
                    'sale_id': sale_id
                }
                esp32_result = self.esp32_service.start_machine(esp32_id, machine_data)
                if not esp32_result.get('success'):
                    self._esp32_last_error = f"ESP32: fallo al activar máquina {machine_id} - {esp32_result.get('message')}"
                    logger.error(self._esp32_last_error)
                    return False, None, None
            except Exception as e:
                self._esp32_last_error = f"ESP32: error de comunicación para máquina {machine_id} - {e}"
                logger.error(self._esp32_last_error)
                return False, None, None

            # Solo actualizar los timestamps dentro de current_service
            update_operators = {
                '$set': {
                    'current_service.started_at': current_time,
                    'current_service.estimated_end_at': estimated_end_time
                }
            }
            
            updated_machine = None
            if machine.get('tipo') == 'lavadora': # Asumiendo 'tipo' existe para lavadoras
                self.washer_repository.update_document_by_id(machine_id, update_operators)
                updated_machine = self.washer_repository.find_by_id(machine_id)
            elif machine.get('tipo') == 'secadora' or 'capacidad' in machine: # Secadoras no siempre tienen 'tipo', pero tienen 'capacidad'
                self.dryer_repository.update_document_by_id(machine_id, update_operators)
                updated_machine = self.dryer_repository.find_by_id(machine_id)
            else:
                logger.warning(f"Tipo de máquina desconocido para {machine_id}. No se pudo actualizar el servicio actual de la máquina.")
                return False, None, None # Devuelve False y None para los tiempos
            
            if updated_machine:
                self._emit_machine_update(machine_id, updated_machine, 'activated')

            logger.info(f"Servicio activado en máquina {machine_id} para venta {sale_id}, servicio {service_index}. Fin estimado: {estimated_end_time}")
            return True, current_time, estimated_end_time # Devuelve True y los tiempos
        except Exception as e:
            logger.error(f"Error al activar servicio en máquina {machine_id}: {e}")
            return False, None, None

    def check_and_deactivate_machines(self) -> Dict[str, Any]:
        """
        Verifica los servicios activos y desactiva las máquinas si su ciclo ha terminado.
        
        Returns:
            Dict: Resultado de la operación.
        """
        try:
            active_services = self.sale_repository.get_active_services()
            deactivated_count = 0
            current_time = datetime.utcnow()

            for service_data in active_services:
                service_info = service_data['service']
                machine_id = service_info['machine_id']
                sale_id = service_data['sale_id']
                service_index = service_data['service_index'] # Acceder directamente al service_index
                estimated_end_at = service_info['estimated_end_at']

                if estimated_end_at and current_time >= estimated_end_at:
                    # Intentar detener la máquina física vía ESP32 (no bloqueante)
                    try:
                        machine = self._get_machine_by_id(machine_id)
                        if machine:
                            esp32_id = machine.get('esp32_id')
                            if esp32_id:
                                stop_payload = {
                                    'machine_id': machine_id,
                                    'end_time': current_time.strftime('%H:%M:%S'),
                                    'sale_id': sale_id,
                                    'service_index': service_index
                                }
                                stop_result = self.esp32_service.stop_machine(esp32_id, stop_payload)
                                if not stop_result.get('success'):
                                    logger.error(f"Error al detener ESP32 {esp32_id} para máquina {machine_id}: {stop_result.get('message')}")
                            else:
                                logger.warning(f"Máquina {machine_id} no tiene esp32_id configurado para detener")
                    except Exception as stop_err:
                        logger.error(f"Error de comunicación al detener ESP32 para máquina {machine_id}: {stop_err}")

                    # Desactivar máquina en BD
                    machine = self._get_machine_by_id(machine_id)
                    if machine:
                        update_operators = {
                            '$set': {'estado': 'disponible'},
                            '$unset': {'current_service': ''} # Usar $unset directamente
                        }
                        updated_machine = None
                        if machine.get('tipo') == 'lavadora': # Asumiendo 'tipo' existe para lavadoras
                            self.washer_repository.update_document_by_id(machine_id, update_operators)
                            updated_machine = self.washer_repository.find_by_id(machine_id)
                        elif machine.get('tipo') == 'secadora' or 'capacidad' in machine: # Secadoras no siempre tienen 'tipo', pero tienen 'capacidad'
                            self.dryer_repository.update_document_by_id(machine_id, update_operators)
                            updated_machine = self.dryer_repository.find_by_id(machine_id)
                        else:
                            logger.warning(f"Tipo de máquina desconocido para {machine_id}. No se pudo actualizar el estado de la máquina.")
                            continue # Salta a la siguiente iteración si no se puede actualizar la máquina
                        
                        if updated_machine:
                            self._emit_machine_update(machine_id, updated_machine, 'available')

                        logger.info(f"Máquina {machine_id} desactivada. Fin de servicio en venta {sale_id}.")
                        
                        # Actualizar estado del servicio en la venta a 'completed'
                        self.sale_repository.update_service_status(sale_id, service_index, 'completed')
                        deactivated_count += 1

            return {'success': True, 'message': f'{deactivated_count} máquinas y servicios actualizados.'}

        except Exception as e:
            logger.error(f"Error en check_and_deactivate_machines: {e}")
            return {'success': False, 'message': 'Error interno al desactivar máquinas.'} 

# Modificaciones para el servicio de ventas para soportar el estado 'finalized'

    def finalize_sale(self, sale_id: str) -> Dict[str, Any]:
        """
        Finalizar una venta, asegurando que todos los servicios estén completados.
        
        Args:
            sale_id: ID de la venta a finalizar.
            
        Returns:
            Dict: Resultado de la operación de finalización.
        """
        try:
            sale = self.sale_repository.find_by_id(sale_id)
            if not sale:
                return {'success': False, 'message': 'Venta no encontrada'}
            
            if sale.get('status') == 'finalized':
                return {'success': False, 'message': 'La venta ya ha sido finalizada'}
            
            # Verificar el estado de los servicios
            services_status = self.sale_repository.get_sale_services_status(sale_id)
            
            if services_status['has_services'] and not services_status['all_services_completed']:
                return {'success': False, 'message': 'No todos los servicios de la venta están completados'}
            
            # Actualizar el estado de la venta a 'finalized'
            updated_sale = self.sale_repository.update_sale_status(sale_id, 'finalized')
            
            if updated_sale:
                sale_response = sale_response_schema.dump(updated_sale)
                return {
                    'success': True,
                    'message': 'Venta finalizada exitosamente',
                    'data': sale_response
                }
            else:
                return {'success': False, 'message': 'Error al finalizar la venta'}
                
        except Exception as e:
            logger.error(f"Error al finalizar venta {sale_id}: {e}")
            return {'success': False, 'message': 'Error interno del servidor al finalizar la venta'} 

    def _emit_machine_update(self, machine_id, machine_data, operation):
        """Emitir evento WebSocket cuando cambia estado de máquina"""
        try:
            from app import socketio
            socketio.emit('machine_updated', {
                'machine_id': machine_id,
                'machine_data': machine_data,
                'operation': operation,
                'timestamp': datetime.utcnow().isoformat()
            })
            logger.info(f"Evento emitido: máquina {machine_id} - {operation}")
        except Exception as e:
            logger.error(f"Error emitiendo evento de máquina: {e}")

    def create_sale_with_nfc_payment(self, sale_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear venta con validación y procesamiento NFC automático
        
        Args:
            sale_data: Datos de la venta con payment_methods conteniendo nfc_uid
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar que hay métodos de pago NFC
            nfc_payments = [pm for pm in sale_data.get('payment_methods', []) 
                           if pm.get('payment_type') == 'tarjeta_recargable' and pm.get('nfc_uid')]
            
            if not nfc_payments:
                # Si no hay pagos NFC, usar el método normal
                return self.create_sale(sale_data)
            
            # Validar cada pago NFC antes de proceder
            for nfc_payment in nfc_payments:
                nfc_uid = nfc_payment['nfc_uid']
                amount = float(nfc_payment['amount'])
                
                validation = self.card_repository.validate_nfc_payment(nfc_uid, amount)
                if not validation['valid']:
                    return {
                        'success': False,
                        'message': f'Validación NFC falló: {validation["message"]}',
                        'error_type': 'nfc_validation_failed'
                    }
            
            # Si todas las validaciones pasan, crear la venta normalmente
            return self.create_sale(sale_data)
            
        except Exception as e:
            logger.error(f"Error en venta con pago NFC: {e}")
            return {
                'success': False,
                'message': 'Error interno al procesar venta con NFC'
            } 