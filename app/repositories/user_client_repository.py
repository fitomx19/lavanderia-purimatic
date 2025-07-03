from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId

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
