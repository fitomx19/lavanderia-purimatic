from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId
import random
import string

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
    
    def update_balance(self, card_id: str, amount: float, operation: str) -> Optional[Dict[str, Any]]:
        """
        Actualizar saldo de tarjeta
        
        Args:
            card_id: ID de la tarjeta
            amount: Monto a aplicar
            operation: Tipo de operación (add, subtract)
            
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
        
        # Actualizar saldo usando upsert
        updated_data = {
            '_id': card_id,
            'balance': new_balance,
            'last_used': self._get_current_datetime()
        }
        
        return self.upsert(updated_data)
    
    def transfer_balance(self, from_card_id: str, to_card_id: str, amount: float) -> Dict[str, Any]:
        """
        Transferir saldo entre tarjetas
        
        Args:
            from_card_id: ID de la tarjeta origen
            to_card_id: ID de la tarjeta destino
            amount: Monto a transferir
            
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
        
        # Realizar transferencia
        self.update_balance(from_card_id, amount, 'subtract')
        self.update_balance(to_card_id, amount, 'add')
        
        return {'success': True, 'message': 'Transferencia realizada exitosamente'}
    
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