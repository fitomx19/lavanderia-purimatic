from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class UserClientRepository(BaseRepository):
    """
    Repositorio para usuarios clientes con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('user_clients')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para usuarios clientes
        
        Args:
            data: Datos del usuario cliente
            
        Returns:
            Dict: Filtro basado en email o teléfono
        """
        filter_criteria = {}
        
        if 'email' in data:
            filter_criteria['email'] = data['email']
        elif 'telefono' in data:
            filter_criteria['telefono'] = data['telefono']
        
        return filter_criteria
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar usuario cliente por email
        
        Args:
            email: Email del cliente
            
        Returns:
            Dict: Cliente encontrado o None
        """
        return self.find_one({'email': email, 'is_active': True})
    
    def find_by_telefono(self, telefono: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar usuario cliente por teléfono
        
        Args:
            telefono: Teléfono del cliente
            
        Returns:
            Dict: Cliente encontrado o None
        """
        return self.find_one({'telefono': telefono, 'is_active': True})
    
    def find_by_nombre(self, nombre: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Buscar clientes por nombre (búsqueda parcial)
        
        Args:
            nombre: Nombre a buscar
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Clientes encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={
                'nombre': {'$regex': nombre, '$options': 'i'},
                'is_active': True
            },
            page=page,
            per_page=per_page
        )
    
    def find_active_clients(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todos los clientes activos
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Clientes encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def update_balance(self, client_id: str, amount: float, operation: str) -> Optional[Dict[str, Any]]:
        """
        Actualizar saldo de tarjeta recargable
        
        Args:
            client_id: ID del cliente
            amount: Monto a aplicar
            operation: Tipo de operación (agregar, reducir, establecer)
            
        Returns:
            Dict: Cliente actualizado o None
        """
        client = self.find_by_id(client_id)
        if not client:
            return None
        
        current_balance = float(client.get('saldo_tarjeta_recargable', 0))
        new_balance = current_balance
        
        if operation == 'agregar':
            new_balance = current_balance + amount
        elif operation == 'reducir':
            new_balance = max(0, current_balance - amount)
        elif operation == 'establecer':
            new_balance = amount
        
        # Actualizar saldo usando upsert
        updated_data = {
            '_id': client_id,
            'saldo_tarjeta_recargable': new_balance
        }
        
        return self.upsert(updated_data)
    
    def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el email ya existe
        
        Args:
            email: Email a verificar
            exclude_id: ID a excluir de la verificación
            
        Returns:
            bool: True si el email existe
        """
        filter_criteria = {'email': email}
        if exclude_id:
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        
        return self.find_one(filter_criteria) is not None
    
    def telefono_exists(self, telefono: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el teléfono ya existe
        
        Args:
            telefono: Teléfono a verificar
            exclude_id: ID a excluir de la verificación
            
        Returns:
            bool: True si el teléfono existe
        """
        filter_criteria = {'telefono': telefono}
        if exclude_id:
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        
        return self.find_one(filter_criteria) is not None
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('email', ASCENDING)], unique=True),
            IndexModel([('telefono', ASCENDING)], unique=True),
            IndexModel([('nombre', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)

    def find_clients_with_card_balance(self, search: Optional[str] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener lista de clientes con el saldo calculado de las tarjetas asociadas.

        Args:
            search: Término de búsqueda por nombre.
            page: Página actual.
            per_page: Elementos por página.

        Returns:
            Dict: Clientes encontrados con el saldo de tarjeta calculado y paginación.
        """
        pipeline = []

        # 1. Filtro inicial por is_active y opcionalmente por nombre
        match_criteria: Dict[str, Any] = {'is_active': True}
        if search:
            match_criteria['nombre'] = {'$regex': search, '$options': 'i'}
        pipeline.append({'$match': match_criteria})

        # 2. Lookup para unir con la colección de tarjetas
        #    'localField' es el _id del cliente (ObjectId)
        #    'foreignField' es client_id en la colección de tarjetas (String)
        pipeline.append({
            '$lookup': {
                'from': 'cards',
                'let': { 'clientId': { '$toString': '$_id' } }, # Convertir _id del cliente a String
                'pipeline': [
                    {
                        '$match': {
                            '$expr': {
                                '$and': [
                                    {'$eq': ['$client_id', '$$clientId']},
                                    {'$eq': ['$is_active', True]} # Considerar solo tarjetas activas
                                ]
                            }
                        }
                    },
                    {
                        '$project': {
                            '_id': 1,
                            'card_number': 1,
                            'balance': 1,
                            'client_id': 1,
                            'created_at': 1,
                            'is_active': 1,
                            'updated_at': 1,
                            'last_used': 1,
                            'is_nfc_enabled': {'$ifNull': ['$is_nfc_enabled', False]},
                            'nfc_uid': {'$ifNull': ['$nfc_uid', '']}
                        }
                    }
                ],
                'as': 'client_cards'
            }
        })

        logger.debug(f"Aggregation pipeline: {pipeline}")

        # 3. Sumar el balance de las tarjetas activas
        pipeline.append({
            '$addFields': {
                'saldo_tarjeta_recargable': {
                    '$sum': {
                        '$map': {
                            'input': {
                                '$filter': {
                                    'input': '$client_cards',
                                    'as': 'card',
                                    'cond': {'$eq': ['$$card.is_active', True]}
                                }
                            },
                            'as': 'active_card',
                            'in': '$$active_card.balance'
                        }
                    }
                }
            }
        })

        # 4. Proyectar campos deseados (todos los del cliente, el saldo calculado y el detalle de las tarjetas)
        pipeline.append({
            '$project': {
                '_id': 1,
                'nombre': 1,
                'telefono': 1,
                'email': 1,
                'direccion': 1,
                'is_active': 1,
                'created_at': 1,
                'updated_at': 1,
                'saldo_tarjeta_recargable': {'$toDouble': {'$ifNull': ['$saldo_tarjeta_recargable', 0]}}, # Asegurar que sea float
                'client_cards': 1 # Incluir el array de tarjetas
            }
        })

        # 5. Contar el total de documentos para la paginación
        count_pipeline = pipeline + [{'$count': 'total'}]
        total_result = list(self.collection.aggregate(count_pipeline))
        total_documents = total_result[0]['total'] if total_result else 0

        # 6. Aplicar paginación (skip y limit)
        pipeline.append({'$skip': (page - 1) * per_page})
        pipeline.append({'$limit': per_page})

        clients = list(self.collection.aggregate(pipeline))

        return {
            'documents': clients,
            'page': page,
            'per_page': per_page,
            'total': total_documents,
            'total_pages': (total_documents + per_page - 1) // per_page
        }
