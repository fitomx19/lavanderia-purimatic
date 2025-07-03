from typing import Dict, Any, Optional
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
from bson import ObjectId

class ServiceCycleRepository(BaseRepository):
    """
    Repositorio para ciclos de servicio con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('service_cycles')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para ciclos de servicio
        
        Args:
            data: Datos del ciclo de servicio
            
        Returns:
            Dict: Filtro basado en nombre
        """
        filter_criteria = {}
        
        if 'name' in data:
            filter_criteria['name'] = data['name']
        elif '_id' in data:
            filter_criteria['_id'] = ObjectId(data['_id']) if isinstance(data['_id'], str) else data['_id']
        
        return filter_criteria
    
    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar ciclo de servicio por nombre
        
        Args:
            name: Nombre del ciclo
            
        Returns:
            Dict: Ciclo encontrado o None
        """
        return self.find_one({'name': name, 'is_active': True})
    
    def find_by_service_type(self, service_type: str) -> list:
        """
        Encontrar ciclos por tipo de servicio
        
        Args:
            service_type: Tipo de servicio (lavado, secado, combo)
            
        Returns:
            list: Lista de ciclos del tipo especificado
        """
        result = self.find_many(
            filter_criteria={'service_type': service_type, 'is_active': True},
            per_page=100
        )
        return result['documents']
    
    def find_by_machine_type(self, machine_type: str) -> list:
        """
        Encontrar ciclos compatibles con un tipo de máquina
        
        Args:
            machine_type: Tipo de máquina (chica, grande, secadora)
            
        Returns:
            list: Lista de ciclos compatibles
        """
        result = self.find_many(
            filter_criteria={
                'machine_types_allowed': machine_type,
                'is_active': True
            },
            per_page=100
        )
        return result['documents']
    
    def find_active_cycles(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todos los ciclos activos
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ciclos encontrados con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page,
            sort_by='name',
            sort_order=1
        )
    
    def name_exists(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Verificar si el nombre ya existe
        
        Args:
            name: Nombre a verificar
            exclude_id: ID a excluir de la verificación
            
        Returns:
            bool: True si el nombre existe
        """
        if exclude_id:
            filter_criteria = {
                'name': name,
                '_id': {'$ne': ObjectId(exclude_id)}
            }
        else:
            filter_criteria = {'name': name}
        
        return self.find_one(filter_criteria) is not None
    
    def validate_cycle_for_machine(self, cycle_id: str, machine_type: str) -> Dict[str, Any]:
        """
        Validar si un ciclo es compatible con un tipo de máquina
        
        Args:
            cycle_id: ID del ciclo
            machine_type: Tipo de máquina
            
        Returns:
            Dict: Resultado de la validación
        """
        cycle = self.find_by_id(cycle_id)
        
        if not cycle:
            return {'valid': False, 'message': 'Ciclo no encontrado'}
        
        if not cycle.get('is_active', False):
            return {'valid': False, 'message': 'Ciclo inactivo'}
        
        machine_types_allowed = cycle.get('machine_types_allowed', [])
        if machine_type not in machine_types_allowed:
            return {'valid': False, 'message': f'Ciclo no compatible con máquina tipo {machine_type}'}
        
        return {'valid': True, 'message': 'Ciclo válido para la máquina'}
    
    def get_cycle_price(self, cycle_id: str) -> Optional[float]:
        """
        Obtener precio de un ciclo
        
        Args:
            cycle_id: ID del ciclo
            
        Returns:
            float: Precio del ciclo o None si no existe
        """
        cycle = self.find_by_id(cycle_id)
        if cycle:
            return float(cycle.get('price', 0))
        return None
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('name', ASCENDING)], unique=True),
            IndexModel([('service_type', ASCENDING)]),
            IndexModel([('machine_types_allowed', ASCENDING)]),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes) 