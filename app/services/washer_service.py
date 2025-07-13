from typing import Dict, Any, Optional, cast
from app.repositories.washer_repository import WasherRepository
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.schemas.washer_schema import (
    washer_schema,
    washer_update_schema,
    washer_status_schema,
    washer_response_schema,
    washers_response_schema
)
from app.utils.machine_utils import (
    get_machine_type_from_data,
    validate_cycle_machine_compatibility,
    get_compatible_cycles_for_machine
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class WasherService:
    """
    Servicio para manejo de lavadoras con lógica de negocio
    """
    
    def __init__(self):
        self.washer_repository = WasherRepository()
        self.service_cycle_repository = ServiceCycleRepository()
    
    def create_or_update_washer(self, washer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar lavadora usando UPSERT
        
        Args:
            washer_data: Datos de la lavadora
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            data_to_validate = washer_data.copy()
            data_to_validate.pop('created_at', None)
            data_to_validate.pop('updated_at', None)
            data_to_validate.pop('machine_type', None)

            validated_data: Dict[str, Any]

            if '_id' in data_to_validate:
                # Actualización
                validated_data = cast(Dict[str, Any], washer_update_schema.load(data_to_validate))
            else:
                # Creación
                validated_data = cast(Dict[str, Any], washer_schema.load(data_to_validate))
                
                # Verificar que el número de lavadora no existe en la tienda
                existing_washer = self.washer_repository.find_by_numero_and_store(
                    validated_data['numero'],
                    validated_data['store_id']
                )
                if existing_washer:
                    return {
                        'success': False,
                        'message': f'Ya existe una lavadora con el número {validated_data["numero"]} en esta tienda'
                    }
            
            # Realizar upsert
            washer = self.washer_repository.upsert(validated_data)
            
            if washer:
                washer_response = washer_response_schema.dump(washer)
                return {
                    'success': True,
                    'message': 'Lavadora guardada exitosamente',
                    'data': washer_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar la lavadora'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en lavadora: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de lavadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_washer_by_id(self, washer_id: str) -> Dict[str, Any]:
        """
        Obtener lavadora por ID
        
        Args:
            washer_id: ID de la lavadora
            
        Returns:
            Dict: Información de la lavadora
        """
        try:
            washer = self.washer_repository.find_by_id(washer_id)
            
            if not washer:
                return {
                    'success': False,
                    'message': 'Lavadora no encontrada'
                }
            
            washer_response = washer_response_schema.dump(washer)
            return {
                'success': True,
                'message': 'Lavadora encontrada',
                'data': washer_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lavadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_washers_by_store(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener lavadoras por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de lavadoras de la tienda
        """
        try:
            result = self.washer_repository.find_by_store(store_id, page, per_page)
            
            washers_response = washers_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Lavadoras obtenidas exitosamente',
                'data': washers_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lavadoras por tienda: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_available_washers(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener lavadoras disponibles por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de lavadoras disponibles
        """
        try:
            result = self.washer_repository.find_available_washers(store_id, page, per_page)
            
            washers_response = washers_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Lavadoras disponibles obtenidas exitosamente',
                'data': washers_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lavadoras disponibles: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_all_active_washers(self) -> Dict[str, Any]:
        """
        Obtener todas las lavadoras activas sin importar su estado.
        
        Returns:
            Dict: Lista de lavadoras activas.
        """
        try:
            washers = self.washer_repository.find_all_active_washers()
            washers_response = washers_response_schema.dump(washers)
            
            return {
                'success': True,
                'message': 'Lavadoras activas obtenidas exitosamente',
                'data': washers_response
            }
        except Exception as e:
            logger.error(f"Error al obtener todas las lavadoras activas: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor al obtener lavadoras activas'
            }

    def update_washer_status(self, washer_id: str, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar estado de la lavadora
        
        Args:
            washer_id: ID de la lavadora
            status_data: Nuevo estado (disponible, ocupada, mantenimiento)
            
        Returns:
            Dict: Datos actualizados de la lavadora
        """
        try:
            # Validar datos de estado
            validated_status = cast(Dict[str, str], washer_status_schema.load(status_data))
            
            # Actualizar estado de la lavadora
            washer = self.washer_repository.update_estado(washer_id, validated_status['estado'])
            
            if washer:
                washer_response = washer_response_schema.dump(washer)
                return {
                    'success': True,
                    'message': 'Estado de lavadora actualizado exitosamente',
                    'data': washer_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar el estado de la lavadora'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en estado de lavadora: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error al actualizar estado de lavadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_washer(self, washer_id: str) -> Dict[str, Any]:
        """
        Eliminar lavadora (soft delete)
        
        Args:
            washer_id: ID de la lavadora
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que la lavadora existe
            washer = self.washer_repository.find_by_id(washer_id)
            if not washer:
                return {
                    'success': False,
                    'message': 'Lavadora no encontrada'
                }
            
            # Verificar que la lavadora no esté ocupada
            if washer.get('estado') == 'ocupada':
                return {
                    'success': False,
                    'message': 'No se puede eliminar una lavadora que está ocupada'
                }
            
            # Realizar soft delete
            deleted = self.washer_repository.soft_delete(washer_id)
            
            if deleted:
                return {
                    'success': True,
                    'message': 'Lavadora eliminada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar la lavadora'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar lavadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_store_statistics(self, store_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de lavadoras por tienda
        
        Args:
            store_id: ID de la tienda
            
        Returns:
            Dict: Estadísticas de la tienda
        """
        try:
            stats = self.washer_repository.get_store_statistics(store_id)
            
            return {
                'success': True,
                'message': 'Estadísticas obtenidas exitosamente',
                'data': stats
            }
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }

    def get_compatible_cycles(self, washer_id: str) -> Dict[str, Any]:
        """
        Obtener ciclos compatibles con una lavadora específica
        
        Args:
            washer_id: ID de la lavadora
            
        Returns:
            Dict: Lista de ciclos compatibles
        """
        try:
            # Obtener datos de la lavadora
            washer = self.washer_repository.find_by_id(washer_id)
            if not washer:
                return {
                    'success': False,
                    'message': 'Lavadora no encontrada'
                }
            
            # Obtener todos los ciclos activos
            cycles_result = self.service_cycle_repository.find_active_cycles(page=1, per_page=100)
            available_cycles = cycles_result['documents']
            
            # Filtrar ciclos compatibles
            compatible_cycles = get_compatible_cycles_for_machine(
                washer, 'washer', available_cycles
            )
            
            # Obtener tipo de máquina para información adicional
            machine_type = get_machine_type_from_data(washer, 'washer')
            
            return {
                'success': True,
                'message': 'Ciclos compatibles obtenidos exitosamente',
                'data': {
                    'washer_id': washer_id,
                    'machine_type': machine_type,
                    'compatible_cycles': compatible_cycles,
                    'total_compatible': len(compatible_cycles)
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener ciclos compatibles: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }

    def validate_cycle_compatibility(self, washer_id: str, cycle_id: str) -> Dict[str, Any]:
        """
        Validar si un ciclo específico es compatible con una lavadora
        
        Args:
            washer_id: ID de la lavadora
            cycle_id: ID del ciclo
            
        Returns:
            Dict: Resultado de la validación
        """
        try:
            # Obtener datos de la lavadora
            washer = self.washer_repository.find_by_id(washer_id)
            if not washer:
                return {
                    'success': False,
                    'message': 'Lavadora no encontrada'
                }
            
            # Obtener datos del ciclo
            cycle = self.service_cycle_repository.find_by_id(cycle_id)
            if not cycle:
                return {
                    'success': False,
                    'message': 'Ciclo no encontrado'
                }
            
            # Validar compatibilidad
            validation_result = validate_cycle_machine_compatibility(
                cycle, washer, 'washer'
            )
            
            return {
                'success': True,
                'message': 'Validación completada',
                'data': validation_result
            }
            
        except Exception as e:
            logger.error(f"Error en validación de compatibilidad: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
