from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING

class WasherRepository(BaseRepository):
    """
    Repositorio para lavadoras con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('washers')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para lavadoras
        
        Args:
            data: Datos de la lavadora
            
        Returns:
            Dict: Filtro basado en número y store_id
        """
        filter_criteria = {}
        
        if 'numero' in data and 'store_id' in data:
            filter_criteria = {
                'numero': data['numero'],
                'store_id': data['store_id']
            }
        
        return filter_criteria
    
    def find_by_numero_and_store(self, numero: int, store_id: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar lavadora por número y tienda
        
        Args:
            numero: Número de la lavadora
            store_id: ID de la tienda
            
        Returns:
            Dict: Lavadora encontrada o None
        """
        return self.find_one({
            'numero': numero,
            'store_id': store_id,
            'is_active': True
        })
    
    def find_by_store(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar lavadoras por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lavadoras encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'store_id': store_id, 'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def find_by_estado(self, estado: str, store_id: Optional[str] = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar lavadoras por estado
        
        Args:
            estado: Estado de la lavadora
            store_id: ID de la tienda (opcional)
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lavadoras encontradas
        """
        filter_criteria = {'estado': estado, 'is_active': True}
        if store_id:
            filter_criteria['store_id'] = store_id
        
        return self.find_many(
            filter_criteria=filter_criteria,
            page=page,
            per_page=per_page
        )
    
    def find_available_washers(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar lavadoras disponibles por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lavadoras disponibles
        """
        return self.find_by_estado('disponible', store_id, page, per_page)

    def find_all_active_washers(self) -> list:
        """
        Encontrar todas las lavadoras activas sin importar su estado.
        
        Returns:
            list: Lista de todas las lavadoras activas.
        """
        result = self.find_many(
            filter_criteria={'is_active': True},
            per_page=1000 # Un número grande para obtener todos
        )
        return result['documents']
    
    def update_estado(self, washer_id: str, estado: str) -> Optional[Dict[str, Any]]:
        """
        Actualizar estado de la lavadora
        
        Args:
            washer_id: ID de la lavadora
            estado: Nuevo estado
            
        Returns:
            Dict: Lavadora actualizada o None
        """
        updated_data = {
            '_id': washer_id,
            'estado': estado
        }
        
        return self.upsert(updated_data)
    
    def numero_exists_in_store(self, numero: int, store_id: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el número de lavadora ya existe en la tienda
        
        Args:
            numero: Número de lavadora
            store_id: ID de la tienda
            exclude_id: ID a excluir de la verificación
            
        Returns:
            bool: True si el número existe
        """
        filter_criteria = {'numero': numero, 'store_id': store_id}
        if exclude_id:
            from bson import ObjectId
            filter_criteria['_id'] = {'$ne': ObjectId(exclude_id)}
        
        return self.find_one(filter_criteria) is not None
    
    def get_store_statistics(self, store_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de lavadoras por tienda
        
        Args:
            store_id: ID de la tienda
            
        Returns:
            Dict: Estadísticas de la tienda
        """
        pipeline = [
            {'$match': {'store_id': store_id, 'is_active': True}},
            {'$group': {
                '_id': '$estado',
                'count': {'$sum': 1}
            }}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        stats = {
            'total': 0,
            'disponible': 0,
            'ocupada': 0,
            'mantenimiento': 0
        }
        
        for item in result:
            estado = item['_id']
            count = item['count']
            stats[estado] = count
            stats['total'] += count
        
        return stats
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('numero', ASCENDING), ('store_id', ASCENDING)], unique=True),
            IndexModel([('store_id', ASCENDING)]),
            IndexModel([('estado', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
