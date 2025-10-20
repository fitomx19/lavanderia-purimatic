from typing import Dict, Any, Optional, List
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING, DESCENDING
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CardTransactionRepository(BaseRepository):
    """
    Repositorio para transacciones de tarjetas recargables
    """
    
    def __init__(self):
        super().__init__('card_transactions')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Las transacciones no tienen campos únicos de negocio,
        cada transacción es única por naturaleza (inserción pura)
        """
        return {}
    
    def create_transaction(self, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Registrar una nueva transacción
        
        Args:
            transaction_data: Datos de la transacción
            
        Returns:
            Dict: Transacción creada o None
        """
        try:
            # Usar upsert para crear la transacción (será siempre una inserción)
            transaction = self.upsert(transaction_data)
            logger.info(f"Transacción registrada: {transaction_data.get('transaction_type')} - Monto: {transaction_data.get('amount')}")
            return transaction
        except Exception as e:
            logger.error(f"Error al crear transacción: {e}")
            return None
    
    def get_transactions_by_card(self, card_id: str, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """
        Obtener transacciones de una tarjeta específica
        
        Args:
            card_id: ID de la tarjeta
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Transacciones con paginación
        """
        return self.find_many(
            filter_criteria={'card_id': card_id},
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def get_transactions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Obtener transacciones en un rango de fechas
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            transaction_type: Tipo de transacción (opcional)
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Transacciones con paginación
        """
        filter_criteria = {
            'created_at': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        if transaction_type:
            filter_criteria['transaction_type'] = transaction_type
        
        return self.find_many(
            filter_criteria=filter_criteria,
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def get_transactions_by_employee(
        self,
        employee_id: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Obtener transacciones realizadas por un empleado
        
        Args:
            employee_id: ID del empleado
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Transacciones con paginación
        """
        return self.find_many(
            filter_criteria={'employee_id': employee_id},
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def get_total_by_transaction_type(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Obtener totales agrupados por tipo de transacción
        
        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            List: Lista de totales por tipo
        """
        pipeline = [
            {
                '$match': {
                    'created_at': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': '$transaction_type',
                    'total_amount': {'$sum': '$amount'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'total_amount': -1}
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return result
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('card_id', ASCENDING), ('created_at', DESCENDING)]),
            IndexModel([('transaction_type', ASCENDING)]),
            IndexModel([('employee_id', ASCENDING)]),
            IndexModel([('created_at', DESCENDING)]),
            IndexModel([('sale_id', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)

