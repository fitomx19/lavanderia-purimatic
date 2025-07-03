from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
from bson import ObjectId
from datetime import datetime
from decimal import Decimal
from app import get_db
import logging

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """
    Repositorio base con operaciones UPSERT para MongoDB
    """
    
    def __init__(self, collection_name: str):
        """
        Inicializar repositorio base
        
        Args:
            collection_name: Nombre de la colección en MongoDB
        """
        self.collection_name = collection_name
        self.db = get_db()
        self.collection: Collection = self.db[collection_name]
    
    def upsert(self, data: Dict[str, Any], filter_criteria: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Operación UPSERT: actualizar si existe, crear si no existe
        
        Args:
            data: Datos a insertar/actualizar
            filter_criteria: Criterios de filtro para encontrar el documento existente
                           Si no se proporciona, se usa el _id del data si existe
            
        Returns:
            Dict: Documento creado o actualizado
        """
        try:
            # Preparar datos para la operación
            update_data = self._prepare_update_data(data)
            
            # Determinar criterios de filtro
            if filter_criteria is None:
                if '_id' in data:
                    filter_criteria = {'_id': ObjectId(data['_id']) if isinstance(data['_id'], str) else data['_id']}
                else:
                    # Si no hay criterios de filtro y no hay _id, usar campos únicos definidos
                    filter_criteria = self._get_unique_filter(data)
            
            print(update_data)
            
            # Realizar upsert
            result = self.collection.update_one(
                filter_criteria,
                {'$set': update_data},
                upsert=True
            )

            
            
            # Obtener y retornar el documento
            if result.upserted_id:
                # Documento creado
                document = self.collection.find_one({'_id': result.upserted_id})
                logger.info(f"Documento creado en {self.collection_name}: {result.upserted_id}")
            else:
                # Documento actualizado
                document = self.collection.find_one(filter_criteria)
                logger.info(f"Documento actualizado en {self.collection_name}")
            
            if document is None:
                raise RuntimeError(f"No se pudo recuperar el documento después del upsert en {self.collection_name}")
            
            return self._format_document(document)
            
        except PyMongoError as e:
            logger.error(f"Error en upsert de {self.collection_name}: {e}")
            raise
    
    def find_by_id(self, document_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Encontrar documento por ID
        
        Args:
            document_id: ID del documento
            
        Returns:
            Dict: Documento encontrado o None
        """
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            
            document = self.collection.find_one({'_id': document_id})
            return self._format_document(document) if document else None
            
        except PyMongoError as e:
            logger.error(f"Error al buscar por ID en {self.collection_name}: {e}")
            raise
    
    def find_one(self, filter_criteria: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Encontrar un documento por criterios
        
        Args:
            filter_criteria: Criterios de búsqueda
            
        Returns:
            Dict: Documento encontrado o None
        """
        try:
            document = self.collection.find_one(filter_criteria)
            return self._format_document(document) if document else None
            
        except PyMongoError as e:
            logger.error(f"Error al buscar en {self.collection_name}: {e}")
            raise
    
    def find_many(self, filter_criteria: Dict[str, Any] = None, page: int = 1, per_page: int = 10, sort_by: str = 'created_at', sort_order: int = -1) -> Dict[str, Any]:
        """
        Encontrar múltiples documentos con paginación
        
        Args:
            filter_criteria: Criterios de búsqueda
            page: Página actual
            per_page: Elementos por página
            sort_by: Campo para ordenar
            sort_order: Orden de clasificación (1 ascendente, -1 descendente)
            
        Returns:
            Dict: Documentos encontrados con información de paginación
        """
        try:
            filter_criteria = filter_criteria or {}
            
            # Calcular skip para paginación
            skip = (page - 1) * per_page
            
            # Obtener documentos con paginación
            cursor = self.collection.find(filter_criteria).sort(sort_by, sort_order).skip(skip).limit(per_page)
            documents = [self._format_document(doc) for doc in cursor]
            
            # Contar total de documentos
            total = self.collection.count_documents(filter_criteria)
            
            return {
                'documents': documents,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
            
        except PyMongoError as e:
            logger.error(f"Error al buscar múltiples en {self.collection_name}: {e}")
            raise
    
    def delete_by_id(self, document_id: Union[str, ObjectId]) -> bool:
        """
        Eliminar documento por ID
        
        Args:
            document_id: ID del documento
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            
            result = self.collection.delete_one({'_id': document_id})
            
            if result.deleted_count > 0:
                logger.info(f"Documento eliminado de {self.collection_name}: {document_id}")
                return True
            
            return False
            
        except PyMongoError as e:
            logger.error(f"Error al eliminar en {self.collection_name}: {e}")
            raise
    
    def soft_delete(self, document_id: Union[str, ObjectId]) -> bool:
        """
        Eliminación suave (marcar como inactivo)
        
        Args:
            document_id: ID del documento
            
        Returns:
            bool: True si se marcó como inactivo exitosamente
        """
        try:
            if isinstance(document_id, str):
                document_id = ObjectId(document_id)
            
            result = self.collection.update_one(
                {'_id': document_id},
                {'$set': {'is_active': False, 'updated_at': datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Documento marcado como inactivo en {self.collection_name}: {document_id}")
                return True
            
            return False
            
        except PyMongoError as e:
            logger.error(f"Error en soft delete en {self.collection_name}: {e}")
            raise
    
    def _prepare_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preparar datos para actualización
        
        Args:
            data: Datos originales
            
        Returns:
            Dict: Datos preparados para actualización
        """
        update_data = data.copy()
        
        # Remover _id si existe para evitar conflictos
        if '_id' in update_data:
            del update_data['_id']
        
        # Convertir objetos Decimal a float para compatibilidad con MongoDB
        for key, value in update_data.items():
            if isinstance(value, Decimal):
                update_data[key] = float(value)
        
        # Agregar timestamps
        now = datetime.utcnow()
        update_data['updated_at'] = now
        
        # Agregar created_at solo si no existe
        if 'created_at' not in update_data:
            update_data['created_at'] = now
        
        return update_data
    
    def _format_document(self, document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Formatear documento para respuesta
        
        Args:
            document: Documento de MongoDB
            
        Returns:
            Dict: Documento formateado o None si no hay documento
        """
        if not document:
            return None
        
        # Convertir ObjectId a string
        if '_id' in document:
            document['_id'] = str(document['_id'])
        
        return document
    
    @abstractmethod
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro de campos únicos para la operación upsert
        
        Args:
            data: Datos del documento
            
        Returns:
            Dict: Filtro basado en campos únicos
        """
        pass
    
    def create_indexes(self):
        """
        Crear índices para la colección
        Debe ser implementado por cada repositorio específico
        """
        pass
