from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING

class StoreRepository(BaseRepository):
    """
    Repositorio para tiendas con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('stores')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para tiendas
        
        Args:
            data: Datos de la tienda
            
        Returns:
            Dict: Filtro basado en nombre
        """
        filter_criteria = {}
        
        if 'nombre' in data:
            filter_criteria['nombre'] = data['nombre']
        
        return filter_criteria
    
    def find_by_nombre(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar tienda por nombre
        
        Args:
            nombre: Nombre de la tienda
            
        Returns:
            Dict: Tienda encontrada o None
        """
        return self.find_one({'nombre': nombre, 'is_active': True})
    
    def find_active_stores(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todas las tiendas activas
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Tiendas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('nombre', ASCENDING)], unique=True),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
