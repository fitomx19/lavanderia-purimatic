from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId

class UserEmployeeRepository(BaseRepository):
    """
    Repositorio para usuarios empleados con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('user_employees')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para usuarios empleados
        
        Args:
            data: Datos del usuario empleado
            
        Returns:
            Dict: Filtro basado en username o email
        """
        # Buscar por username o email (campos únicos)
        filter_criteria = {}
        
        if 'username' in data:
            filter_criteria['username'] = data['username']
        elif 'email' in data:
            filter_criteria['email'] = data['email']
        
        return filter_criteria
    
    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar usuario empleado por nombre de usuario
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Dict: Usuario encontrado o None
        """
        return self.find_one({'username': username, 'is_active': True})
    
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar usuario empleado por email
        
        Args:
            email: Email del usuario
            
        Returns:
            Dict: Usuario encontrado o None
        """
        return self.find_one({'email': email, 'is_active': True})
    
    def find_by_username_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar usuario empleado por nombre de usuario o email
        
        Args:
            identifier: Nombre de usuario o email
            
        Returns:
            Dict: Usuario encontrado o None
        """
        return self.find_one({
            '$or': [
                {'username': identifier},
                {'email': identifier}
            ],
            'is_active': True
        })
    
    def find_by_store(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar usuarios empleados por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Usuarios encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'store_id': store_id, 'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def find_by_role(self, role: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar usuarios empleados por rol
        
        Args:
            role: Rol del usuario (admin, empleado)
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Usuarios encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'role': role, 'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def find_active_employees(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todos los usuarios empleados activos
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Usuarios encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def username_exists(self, username: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el nombre de usuario ya existe
        
        Args:
            username: Nombre de usuario a verificar
            exclude_id: ID a excluir de la verificación (para updates)
            
        Returns:
            bool: True si el nombre de usuario existe
        """
        filter_criteria = {'username': username}
        if exclude_id:
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        
        return self.find_one(filter_criteria) is not None
    
    def email_exists(self, email: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el email ya existe
        
        Args:
            email: Email a verificar
            exclude_id: ID a excluir de la verificación (para updates)
            
        Returns:
            bool: True si el email existe
        """
        filter_criteria = {'email': email}
        if exclude_id:
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        
        return self.find_one(filter_criteria) is not None
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('username', ASCENDING)], unique=True),
            IndexModel([('email', ASCENDING)], unique=True),
            IndexModel([('store_id', ASCENDING)]),
            IndexModel([('role', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
