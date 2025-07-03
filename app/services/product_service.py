from typing import Dict, Any, Optional
from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import (
    product_schema,
    product_update_schema,
    product_response_schema,
    products_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class ProductService:
    """
    Servicio para manejo de productos con lógica de negocio
    """
    
    def __init__(self):
        self.product_repository = ProductRepository()
    
    def create_or_update_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar producto usando UPSERT
        
        Args:
            product_data: Datos del producto
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            if '_id' in product_data:
                # Actualización
                validated_data = product_update_schema.load(product_data)
            else:
                # Creación
                validated_data = product_schema.load(product_data)
                
                # Verificar que el nombre del producto no existe
                existing_product = self.product_repository.find_by_nombre(validated_data['nombre'])
                if existing_product:
                    return {
                        'success': False,
                        'message': 'Ya existe un producto con ese nombre'
                    }
            
            # Realizar upsert
            product = self.product_repository.upsert(validated_data)
            
            if product:
                product_response = product_response_schema.dump(product)
                return {
                    'success': True,
                    'message': 'Producto guardado exitosamente',
                    'data': product_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar el producto'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en producto: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de producto: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """
        Obtener producto por ID
        
        Args:
            product_id: ID del producto
            
        Returns:
            Dict: Información del producto
        """
        try:
            product = self.product_repository.find_by_id(product_id)
            
            if not product:
                return {
                    'success': False,
                    'message': 'Producto no encontrado'
                }
            
            product_response = product_response_schema.dump(product)
            return {
                'success': True,
                'message': 'Producto encontrado',
                'data': product_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener producto: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_products_list(self, page: int = 1, per_page: int = 10, tipo: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener lista de productos con paginación y filtros
        
        Args:
            page: Página actual
            per_page: Elementos por página
            tipo: Filtrar por tipo de producto
            search: Término de búsqueda
            
        Returns:
            Dict: Lista de productos
        """
        try:
            if search:
                result = self.product_repository.search_products(search, page, per_page)
            elif tipo:
                result = self.product_repository.find_by_tipo(tipo, page, per_page)
            else:
                result = self.product_repository.find_active_products(page, per_page)
            
            products_response = products_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Productos obtenidos exitosamente',
                'data': products_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de productos: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_product(self, product_id: str) -> Dict[str, Any]:
        """
        Eliminar producto (soft delete)
        
        Args:
            product_id: ID del producto
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el producto existe
            product = self.product_repository.find_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'Producto no encontrado'
                }
            
            # Realizar soft delete
            deleted = self.product_repository.soft_delete(product_id)
            
            if deleted:
                return {
                    'success': True,
                    'message': 'Producto eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar el producto'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar producto: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def update_product_stock(self, product_id: str, amount: int, operation: str) -> Dict[str, Any]:
        """
        Actualizar stock del producto
        
        Args:
            product_id: ID del producto
            amount: Cantidad a aplicar
            operation: Tipo de operación (agregar, reducir, establecer)
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el producto existe
            product = self.product_repository.find_by_id(product_id)
            if not product:
                return {
                    'success': False,
                    'message': 'Producto no encontrado'
                }
            
            # Validar operación
            valid_operations = ['agregar', 'reducir', 'establecer']
            if operation not in valid_operations:
                return {
                    'success': False,
                    'message': f'Operación inválida. Debe ser una de: {", ".join(valid_operations)}'
                }
            
            # Actualizar stock
            updated_product = self.product_repository.update_stock(product_id, amount, operation)
            
            if updated_product:
                product_response = product_response_schema.dump(updated_product)
                return {
                    'success': True,
                    'message': 'Stock actualizado exitosamente',
                    'data': product_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar el stock'
                }
                
        except Exception as e:
            logger.error(f"Error al actualizar stock: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_low_stock_products(self, threshold: int = 10, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener productos con stock bajo
        
        Args:
            threshold: Umbral de stock bajo
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de productos con stock bajo
        """
        try:
            result = self.product_repository.find_low_stock(threshold, page, per_page)
            
            products_response = products_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': f'Productos con stock menor o igual a {threshold}',
                'data': products_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener productos con stock bajo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def search_products(self, search_term: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Buscar productos por nombre o descripción
        
        Args:
            search_term: Término de búsqueda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de productos encontrados
        """
        return self.get_products_list(page, per_page, search=search_term)
