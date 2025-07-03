from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING

class ProductRepository(BaseRepository):
    """
    Repositorio para productos con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('products')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para productos
        
        Args:
            data: Datos del producto
            
        Returns:
            Dict: Filtro basado en nombre
        """
        filter_criteria = {}
        
        if 'nombre' in data:
            filter_criteria['nombre'] = data['nombre']
        
        return filter_criteria
    
    def find_by_nombre(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar producto por nombre
        
        Args:
            nombre: Nombre del producto
            
        Returns:
            Dict: Producto encontrado o None
        """
        return self.find_one({'nombre': nombre, 'is_active': True})
    
    def find_by_tipo(self, tipo: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar productos por tipo
        
        Args:
            tipo: Tipo de producto
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Productos encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'tipo': tipo, 'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def find_active_products(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todos los productos activos
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Productos encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def find_low_stock(self, threshold: int = 10, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar productos con stock bajo
        
        Args:
            threshold: Umbral de stock bajo
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Productos con stock bajo
        """
        return self.find_many(
            filter_criteria={
                'stock': {'$lte': threshold},
                'is_active': True
            },
            page=page,
            per_page=per_page
        )
    
    def update_stock(self, product_id: str, amount: int, operation: str) -> Optional[Dict[str, Any]]:
        """
        Actualizar stock del producto
        
        Args:
            product_id: ID del producto
            amount: Cantidad a aplicar
            operation: Tipo de operación (agregar, reducir, establecer)
            
        Returns:
            Dict: Producto actualizado o None
        """
        product = self.find_by_id(product_id)
        if not product:
            return None
        
        current_stock = int(product.get('stock', 0))
        new_stock = current_stock
        
        if operation == 'agregar':
            new_stock = current_stock + amount
        elif operation == 'reducir':
            new_stock = max(0, current_stock - amount)
        elif operation == 'establecer':
            new_stock = amount
        
        # Actualizar stock usando upsert
        updated_data = {
            '_id': product_id,
            'stock': new_stock
        }
        
        return self.upsert(updated_data)
    
    def search_products(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Buscar productos por nombre o descripción
        
        Args:
            query: Texto a buscar
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Productos encontrados
        """
        return self.find_many(
            filter_criteria={
                '$or': [
                    {'nombre': {'$regex': query, '$options': 'i'}},
                    {'descripcion': {'$regex': query, '$options': 'i'}}
                ],
                'is_active': True
            },
            page=page,
            per_page=per_page
        )
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('nombre', ASCENDING)], unique=True),
            IndexModel([('tipo', ASCENDING)]),
            IndexModel([('stock', ASCENDING)]),
            IndexModel([('precio', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
