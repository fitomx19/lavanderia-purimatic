from typing import Dict, Any, Optional, List
from datetime import datetime
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
import logging

logger = logging.getLogger(__name__)

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
        self._create_esp32_config_indexes()

    def _esp32_collection(self):
        return self.db['esp32_config']

    def _create_esp32_config_indexes(self):
        """Índice único de esp32_id para que cada placa tenga una sola URL."""
        indexes = [
            IndexModel([('esp32_id', ASCENDING)], unique=True),
            IndexModel([('is_active', ASCENDING)]),
        ]
        self._esp32_collection().create_indexes(indexes)

    def _serialize_esp32_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        serialized = dict(doc)
        if '_id' in serialized:
            serialized['_id'] = str(serialized['_id'])
        return serialized

    # --- ESP32 CONFIG ---
    def get_esp32_url_by_id(self, esp32_id: str) -> Optional[str]:
        """
        Obtener la URL del ESP32 desde la colección 'esp32_config'.
        Estructura esperada del documento:
          { esp32_id: "100", esp32_url: "http://192.168.1.100/laundry-update", is_active: true }
        """
        try:
            cfg_collection = self._esp32_collection()
            doc = (
                cfg_collection.find_one({'esp32_id': str(esp32_id), 'is_active': True})
                or cfg_collection.find_one({'esp32_id': str(esp32_id)})
            )
            if not doc:
                return None
            return doc.get('esp32_url') or doc.get('url')
        except Exception as e:
            logger.error(f"Error obteniendo esp32_url para esp32_id={esp32_id}: {e}")
            return None

    def get_esp32_config_by_id(self, esp32_id: str) -> Optional[Dict[str, Any]]:
        """Obtener el documento completo de una placa por esp32_id."""
        try:
            doc = self._esp32_collection().find_one({'esp32_id': str(esp32_id)})
            return self._serialize_esp32_doc(doc)
        except Exception as e:
            logger.error(f"Error obteniendo esp32_config para esp32_id={esp32_id}: {e}")
            return None

    def list_esp32_configs(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Listar placas registradas en esp32_config."""
        try:
            query = {} if include_inactive else {'is_active': True}
            docs = self._esp32_collection().find(query).sort('esp32_id', ASCENDING)
            return [self._serialize_esp32_doc(doc) for doc in docs]
        except Exception as e:
            logger.error(f"Error listando esp32_config: {e}")
            return []

    def upsert_esp32_config(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear o actualizar una placa ESP32.
        Clave única: esp32_id.
        """
        try:
            esp32_id = str(data.get('esp32_id', '')).strip()
            esp32_url = str(data.get('esp32_url', '')).strip()
            if not esp32_id or not esp32_url:
                return None

            now = datetime.utcnow()
            payload = {
                'esp32_id': esp32_id,
                'esp32_url': esp32_url,
                'is_active': bool(data.get('is_active', True)),
                'updated_at': now,
            }
            self._esp32_collection().update_one(
                {'esp32_id': esp32_id},
                {'$set': payload, '$setOnInsert': {'created_at': now}},
                upsert=True,
            )
            return self.get_esp32_config_by_id(esp32_id)
        except Exception as e:
            logger.error(f"Error guardando esp32_config: {e}")
            return None
