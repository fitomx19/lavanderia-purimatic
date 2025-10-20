from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId
import random
import string
import logging

# Configurar logger
logger = logging.getLogger(__name__)

class CardRepository(BaseRepository):
    """
    Repositorio para tarjetas recargables con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('cards')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para tarjetas
        
        Args:
            data: Datos de la tarjeta
            
        Returns:
            Dict: Filtro basado en número de tarjeta
        """
        filter_criteria = {}
        
        if 'card_number' in data:
            filter_criteria['card_number'] = data['card_number']
        elif '_id' in data:
            filter_criteria['_id'] = ObjectId(data['_id']) if isinstance(data['_id'], str) else data['_id']
        
        return filter_criteria
    
    def generate_card_number(self) -> str:
        """
        Generar número de tarjeta único
        
        Returns:
            str: Número de tarjeta de 12 dígitos
        """
        while True:
            # Generar número de 12 dígitos
            card_number = ''.join(random.choices(string.digits, k=12))
            
            # Verificar que no exista
            if not self.find_one({'card_number': card_number}):
                return card_number
    
    def find_by_card_number(self, card_number: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar tarjeta por número
        
        Args:
            card_number: Número de tarjeta
            
        Returns:
            Dict: Tarjeta encontrada o None
        """
        return self.find_one({'card_number': card_number, 'is_active': True})
    
    def find_by_client_id(self, client_id: str) -> list:
        """
        Encontrar todas las tarjetas de un cliente
        
        Args:
            client_id: ID del cliente
            
        Returns:
            list: Lista de tarjetas del cliente
        """
        result = self.find_many(
            filter_criteria={'client_id': client_id, 'is_active': True},
            per_page=100
        )
        return result['documents']
    
    def update_balance(self, card_id: str, amount: float, operation: str, employee_id: str, transaction_type: str, sale_id: Optional[str] = None, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Actualizar saldo de tarjeta y registrar transacción
        
        Args:
            card_id: ID de la tarjeta
            amount: Monto a aplicar
            operation: Tipo de operación (add, subtract)
            employee_id: ID del empleado que realiza la operación
            transaction_type: Tipo de transacción para registro
            sale_id: ID de venta (opcional, para pagos)
            notes: Notas adicionales (opcional)
            
        Returns:
            Dict: Tarjeta actualizada o None
        """
        card = self.find_by_id(card_id)
        if not card:
            return None
        
        current_balance = float(card.get('balance', 0))
        new_balance = current_balance
        
        if operation == 'add':
            new_balance = current_balance + amount
        elif operation == 'subtract':
            new_balance = max(0, current_balance - amount)
        
        # Validar límites
        if new_balance > 1000:
            return None
        
        # Registrar transacción ANTES de actualizar saldo
        from app.repositories.card_transaction_repository import CardTransactionRepository
        transaction_repo = CardTransactionRepository()
        
        transaction_data = {
            'card_id': card_id,
            'amount': amount,
            'transaction_type': transaction_type,
            'balance_before': current_balance,
            'balance_after': new_balance,
            'employee_id': employee_id,
            'sale_id': sale_id,
            'notes': notes
        }
        
        transaction_repo.create_transaction(transaction_data)
        
        # Actualizar saldo usando upsert
        updated_data = {
            '_id': card_id,
            'balance': new_balance,
            'last_used': self._get_current_datetime()
        }
        
        return self.upsert(updated_data)
    
    def transfer_balance(self, from_card_id: str, to_card_id: str, amount: float, employee_id: str) -> Dict[str, Any]:
        """
        Transferir saldo entre tarjetas y registrar ambas transacciones
        
        Args:
            from_card_id: ID de la tarjeta origen
            to_card_id: ID de la tarjeta destino
            amount: Monto a transferir
            employee_id: ID del empleado que realiza la transferencia
            
        Returns:
            Dict: Resultado de la operación
        """
        from_card = self.find_by_id(from_card_id)
        to_card = self.find_by_id(to_card_id)
        
        if not from_card or not to_card:
            return {'success': False, 'message': 'Tarjeta no encontrada'}
        
        # Verificar que pertenezcan al mismo cliente
        if from_card.get('client_id') != to_card.get('client_id'):
            return {'success': False, 'message': 'Las tarjetas deben pertenecer al mismo cliente'}
        
        # Verificar saldo suficiente
        from_balance = float(from_card.get('balance', 0))
        if from_balance < amount:
            return {'success': False, 'message': 'Saldo insuficiente'}
        
        # Verificar límite de tarjeta destino
        to_balance = float(to_card.get('balance', 0))
        if to_balance + amount > 1000:
            return {'success': False, 'message': 'La transferencia excedería el límite de la tarjeta destino'}
        
        # Registrar transacciones para ambas tarjetas
        from app.repositories.card_transaction_repository import CardTransactionRepository
        transaction_repo = CardTransactionRepository()
        
        # Transacción de salida (tarjeta origen)
        transaction_out_data = {
            'card_id': from_card_id,
            'amount': amount,
            'transaction_type': 'transferencia_out',
            'balance_before': from_balance,
            'balance_after': from_balance - amount,
            'employee_id': employee_id,
            'related_card_id': to_card_id,
            'notes': f'Transferencia a tarjeta {to_card.get("card_number")}'
        }
        transaction_repo.create_transaction(transaction_out_data)
        
        # Transacción de entrada (tarjeta destino)
        transaction_in_data = {
            'card_id': to_card_id,
            'amount': amount,
            'transaction_type': 'transferencia_in',
            'balance_before': to_balance,
            'balance_after': to_balance + amount,
            'employee_id': employee_id,
            'related_card_id': from_card_id,
            'notes': f'Transferencia desde tarjeta {from_card.get("card_number")}'
        }
        transaction_repo.create_transaction(transaction_in_data)
        
        # Actualizar saldos directamente (sin registrar transacciones nuevamente)
        self.collection.update_one(
            {'_id': self._get_object_id(from_card_id)},
            {'$set': {'balance': from_balance - amount, 'last_used': self._get_current_datetime(), 'updated_at': self._get_current_datetime()}}
        )
        self.collection.update_one(
            {'_id': self._get_object_id(to_card_id)},
            {'$set': {'balance': to_balance + amount, 'last_used': self._get_current_datetime(), 'updated_at': self._get_current_datetime()}}
        )
        
        return {'success': True, 'message': 'Transferencia realizada exitosamente'}
    
    def _get_object_id(self, id_value):
        """Helper para convertir string a ObjectId si es necesario"""
        from bson import ObjectId
        return ObjectId(id_value) if isinstance(id_value, str) else id_value
    
    def card_number_exists(self, card_number: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el número de tarjeta ya existe
        
        Args:
            card_number: Número de tarjeta a verificar
            exclude_id: ID a excluir de la verificación
            
        Returns:
            bool: True si el número existe
        """
        if exclude_id:
            # Crear filtro complejo para excluir un ID específico
            filter_criteria = {
                'card_number': card_number,
                '_id': {'$ne': ObjectId(exclude_id)}
            }
        else:
            filter_criteria = {'card_number': card_number}
        
        return self.find_one(filter_criteria) is not None
    
    def validate_card_for_payment(self, card_id: str, amount: float) -> Dict[str, Any]:
        """
        Validar tarjeta para pago
        
        Args:
            card_id: ID de la tarjeta
            amount: Monto del pago
            
        Returns:
            Dict: Resultado de la validación
        """
        card = self.find_by_id(card_id)
        
        if not card:
            return {'valid': False, 'message': 'Tarjeta no encontrada'}
        
        if not card.get('is_active', False):
            return {'valid': False, 'message': 'Tarjeta inactiva'}
        
        balance = float(card.get('balance', 0))
        if balance < amount:
            return {'valid': False, 'message': 'Saldo insuficiente'}
        
        return {'valid': True, 'message': 'Tarjeta válida para pago'}
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('card_number', ASCENDING)], unique=True),
            IndexModel([('client_id', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
    
    def _get_current_datetime(self):
        """
        Obtener fecha y hora actual
        
        Returns:
            datetime: Fecha y hora actual
        """
        from datetime import datetime
        return datetime.utcnow() 

    def update_nfc_uid(self, card_id: str, nfc_uid: str) -> Optional[Dict[str, Any]]:
        """Asociar UID NFC con tarjeta"""
        updated_data = {
            '_id': card_id,
            'nfc_uid': nfc_uid,
            'is_nfc_enabled': True,
            'last_nfc_read': self._get_current_datetime()
        }
        return self.upsert(updated_data)

    def find_by_nfc_uid(self, nfc_uid: str) -> Optional[Dict[str, Any]]:
        """Encontrar tarjeta por UID NFC"""
        return self.find_one({'nfc_uid': nfc_uid, 'is_active': True})

    def nfc_uid_exists(self, nfc_uid: str, exclude_id: Optional[str] = None) -> bool:
        """Verificar si UID NFC ya está en uso"""
        filter_criteria = {'nfc_uid': nfc_uid}
        if exclude_id:
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        return self.find_one(filter_criteria) is not None

    def validate_nfc_payment(self, nfc_uid: str, amount: float) -> Dict[str, Any]:
        """
        Validar pago NFC con UID físico
        
        Args:
            nfc_uid: UID físico de la tarjeta NFC
            amount: Monto a validar
            
        Returns:
            Dict: Resultado de la validación con info del cliente
        """
        logger.info(f"🔍 [card_repository] Iniciando validate_nfc_payment")
        logger.info(f"🔍 [card_repository] Parámetros: nfc_uid={nfc_uid}, amount={amount}")
        
        try:
            # Buscar tarjeta por UID NFC
            logger.info(f"🔍 [card_repository] Buscando tarjeta con UID NFC: {nfc_uid}")
            card = self.find_by_nfc_uid(nfc_uid)
            
            if not card:
                logger.warning(f"⚠️ [card_repository] Tarjeta NFC no encontrada: {nfc_uid}")
                return {
                    'valid': False,
                    'message': 'Tarjeta NFC no registrada en el sistema'
                }
            
            logger.info(f"✅ [card_repository] Tarjeta encontrada: {card.get('card_number')}")
            
            if not card.get('is_active', False):
                logger.warning(f"⚠️ [card_repository] Tarjeta inactiva: {card.get('card_number')}")
                return {
                    'valid': False,
                    'message': 'Tarjeta inactiva'
                }
            
            balance = float(card.get('balance', 0))
            logger.info(f"💰 [card_repository] Saldo actual: ${balance:.2f}, Monto requerido: ${amount:.2f}")
            
            if balance < amount:
                logger.warning(f"⚠️ [card_repository] Saldo insuficiente: ${balance:.2f} < ${amount:.2f}")
                return {
                    'valid': False,
                    'message': f'Saldo insuficiente. Disponible: ${balance:.2f}',
                    'card_data': {
                        'card_id': str(card['_id']),
                        'card_number': card.get('card_number'),
                        'current_balance': balance,
                        'client_id': card.get('client_id'),
                        'nfc_uid': nfc_uid
                    }
                }
            
            # Obtener datos del cliente
            logger.info(f"🔍 [card_repository] Obteniendo datos del cliente: {card.get('client_id')}")
            from app.repositories.user_client_repository import UserClientRepository
            client_repo = UserClientRepository()
            client_id = card.get('client_id')
            client = client_repo.find_by_id(client_id) if client_id else None
            
            client_name = client.get('nombre', 'Cliente Desconocido') if client else 'Cliente Desconocido'
            logger.info(f"👤 [card_repository] Cliente: {client_name}")
            
            remaining_balance = balance - amount
            logger.info(f"✅ [card_repository] Validación exitosa. Saldo restante: ${remaining_balance:.2f}")
            
            return {
                'valid': True,
                'message': f'Tarjeta válida para pago de ${amount:.2f}',
                'card_data': {
                    'card_id': str(card['_id']),
                    'card_number': card.get('card_number'),
                    'current_balance': balance,
                    'client_id': card.get('client_id'),
                    'client_name': client_name,
                    'nfc_uid': nfc_uid,
                    'remaining_balance': remaining_balance
                }
            }
            
        except Exception as e:
            logger.error(f"❌ [card_repository] Error validando pago NFC: {e}")
            return {
                'valid': False,
                'message': 'Error interno al validar tarjeta'
            }

    def process_nfc_payment(self, nfc_uid: str, amount: float, employee_id: str, sale_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Procesar pago NFC descontando saldo y registrando transacción
        
        Args:
            nfc_uid: UID físico de la tarjeta NFC
            amount: Monto a descontar
            employee_id: ID del empleado que procesa el pago
            sale_id: ID de la venta asociada (opcional)
            
        Returns:
            Dict: Resultado del procesamiento
        """
        logger.info(f"🔍 [card_repository] Iniciando process_nfc_payment")
        logger.info(f"🔍 [card_repository] Parámetros: nfc_uid={nfc_uid}, amount={amount}")
        
        try:
            # Buscar tarjeta por UID NFC
            logger.info(f"🔍 [card_repository] Buscando tarjeta con UID NFC: {nfc_uid}")
            card = self.find_by_nfc_uid(nfc_uid)
            
            if not card:
                logger.warning(f"⚠️ [card_repository] Tarjeta NFC no encontrada: {nfc_uid}")
                return {
                    'success': False,
                    'message': 'Tarjeta NFC no encontrada'
                }
            
            logger.info(f"✅ [card_repository] Tarjeta encontrada: {card.get('card_number')}")
            
            # Validar nuevamente antes de procesar
            logger.info(f"🔍 [card_repository] Validando pago antes de procesar")
            validation = self.validate_nfc_payment(nfc_uid, amount)
            if not validation['valid']:
                logger.warning(f"⚠️ [card_repository] Validación fallida: {validation['message']}")
                return {
                    'success': False,
                    'message': validation['message']
                }
            
            logger.info(f"✅ [card_repository] Validación exitosa, procediendo a descontar saldo")
            
            # Descontar saldo y registrar transacción
            card_id = str(card['_id'])
            logger.info(f"💰 [card_repository] Descontando ${amount:.2f} de la tarjeta {card_id}")
            updated_card = self.update_balance(
                card_id, 
                amount, 
                'subtract',
                employee_id,
                'pago_venta',
                sale_id=sale_id,
                notes=f'Pago en venta con NFC'
            )
            
            if updated_card:
                logger.info(f"✅ [card_repository] Pago procesado exitosamente. Nuevo saldo: ${updated_card['balance']:.2f}")
                return {
                    'success': True,
                    'message': f'Pago procesado exitosamente. Nuevo saldo: ${updated_card["balance"]:.2f}',
                    'card_data': {
                        'card_id': str(updated_card['_id']),
                        'new_balance': updated_card['balance'],
                        'amount_charged': amount,
                        'nfc_uid': nfc_uid
                    }
                }
            else:
                logger.error(f"❌ [card_repository] Error al actualizar saldo de la tarjeta")
                return {
                    'success': False,
                    'message': 'Error al procesar el pago'
                }
                
        except Exception as e:
            logger.error(f"❌ [card_repository] Error procesando pago NFC: {e}")
            return {
                'success': False,
                'message': 'Error interno al procesar pago'
            }