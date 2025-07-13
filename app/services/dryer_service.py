from typing import Dict, Any, Optional, cast
from app.repositories.dryer_repository import DryerRepository
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.schemas.dryer_schema import (
    dryer_schema,
    dryer_update_schema,
    dryer_status_schema,
    dryer_response_schema,
    dryers_response_schema
)
from app.utils.machine_utils import (
    get_machine_type_from_data,
    validate_cycle_machine_compatibility,
    get_compatible_cycles_for_machine
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class DryerService:
    """
    Servicio para manejo de secadoras con lógica de negocio
    """
    
    def __init__(self):
        self.dryer_repository = DryerRepository()
        self.service_cycle_repository = ServiceCycleRepository()
    
    def create_or_update_dryer(self, dryer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar secadora usando UPSERT
        
        Args:
            dryer_data: Datos de la secadora
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            data_to_validate = dryer_data.copy()
            data_to_validate.pop('created_at', None)
            data_to_validate.pop('updated_at', None)
            # data_to_validate.pop('tipo', None)

            validated_data: Dict[str, Any]

            if '_id' in data_to_validate:
                # Actualización
                validated_data = cast(Dict[str, Any], dryer_update_schema.load(data_to_validate))
            else:
                # Creación
                validated_data = cast(Dict[str, Any], dryer_schema.load(data_to_validate))
                
                # Verificar que el número de secadora no existe en la tienda
                existing_dryer = self.dryer_repository.find_by_numero_and_store(
                    validated_data['numero'],
                    validated_data['store_id']
                )
                if existing_dryer:
                    return {
                        'success': False,
                        'message': f'Ya existe una secadora con el número {validated_data["numero"]} en esta tienda'
                    }
            
            # Realizar upsert
            dryer = self.dryer_repository.upsert(validated_data)
            
            if dryer:
                dryer_response = dryer_response_schema.dump(dryer)
                return {
                    'success': True,
                    'message': 'Secadora guardada exitosamente',
                    'data': dryer_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar la secadora'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en secadora: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de secadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_dryer_by_id(self, dryer_id: str) -> Dict[str, Any]:
        """
        Obtener secadora por ID
        
        Args:
            dryer_id: ID de la secadora
            
        Returns:
            Dict: Información de la secadora
        """
        try:
            dryer = self.dryer_repository.find_by_id(dryer_id)
            
            if not dryer:
                return {
                    'success': False,
                    'message': 'Secadora no encontrada'
                }
            
            dryer_response = dryer_response_schema.dump(dryer)
            return {
                'success': True,
                'message': 'Secadora encontrada',
                'data': dryer_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener secadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_dryers_by_store(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener secadoras por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de secadoras de la tienda
        """
        try:
            result = self.dryer_repository.find_by_store(store_id, page, per_page)
            
            dryers_response = dryers_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Secadoras obtenidas exitosamente',
                'data': dryers_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener secadoras por tienda: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_available_dryers(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener secadoras disponibles por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de secadoras disponibles
        """
        try:
            result = self.dryer_repository.find_available_dryers(store_id, page, per_page)
            
            dryers_response = dryers_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Secadoras disponibles obtenidas exitosamente',
                'data': dryers_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener secadoras disponibles: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_all_active_dryers(self) -> Dict[str, Any]:
        """
        Obtener todas las secadoras activas sin importar su estado.
        
        Returns:
            Dict: Lista de secadoras activas.
        """
        try:
            dryers = self.dryer_repository.find_all_active_dryers()
            dryers_response = dryers_response_schema.dump(dryers)
            
            return {
                'success': True,
                'message': 'Secadoras activas obtenidas exitosamente',
                'data': dryers_response
            }
        except Exception as e:
            logger.error(f"Error al obtener todas las secadoras activas: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor al obtener secadoras activas'
            }

    def update_dryer_status(self, dryer_id: str, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar estado de la secadora
        
        Args:
            dryer_id: ID de la secadora
            status_data: Nuevo estado (disponible, ocupada, mantenimiento)
            
        Returns:
            Dict: Datos actualizados de la secadora
        """
        try:
            # Validar datos de estado
            validated_status = cast(Dict[str, str], dryer_status_schema.load(status_data))
            
            # Actualizar estado de la secadora
            dryer = self.dryer_repository.update_estado(dryer_id, validated_status['estado'])
            
            if dryer:
                dryer_response = dryer_response_schema.dump(dryer)
                return {
                    'success': True,
                    'message': 'Estado de secadora actualizado exitosamente',
                    'data': dryer_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar el estado de la secadora'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en estado de secadora: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error al actualizar estado de secadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_dryer(self, dryer_id: str) -> Dict[str, Any]:
        """
        Eliminar secadora (soft delete)
        
        Args:
            dryer_id: ID de la secadora
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que la secadora existe
            dryer = self.dryer_repository.find_by_id(dryer_id)
            if not dryer:
                return {
                    'success': False,
                    'message': 'Secadora no encontrada'
                }
            
            # Verificar que la secadora no esté ocupada
            if dryer.get('estado') == 'ocupada':
                return {
                    'success': False,
                    'message': 'No se puede eliminar una secadora que está ocupada'
                }
            
            # Realizar soft delete
            deleted = self.dryer_repository.soft_delete(dryer_id)
            
            if deleted:
                return {
                    'success': True,
                    'message': 'Secadora eliminada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar la secadora'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar secadora: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_store_statistics(self, store_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de secadoras por tienda
        
        Args:
            store_id: ID de la tienda
            
        Returns:
            Dict: Estadísticas de la tienda
        """
        try:
            stats = self.dryer_repository.get_store_statistics(store_id)
            
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

    def get_compatible_cycles(self, dryer_id: str) -> Dict[str, Any]:
        """
        Obtener ciclos compatibles con una secadora específica
        
        Args:
            dryer_id: ID de la secadora
            
        Returns:
            Dict: Lista de ciclos compatibles
        """
        try:
            # Obtener datos de la secadora
            dryer = self.dryer_repository.find_by_id(dryer_id)
            if not dryer:
                return {
                    'success': False,
                    'message': 'Secadora no encontrada'
                }
            
            # Obtener todos los ciclos activos
            cycles_result = self.service_cycle_repository.find_active_cycles(page=1, per_page=100)
            available_cycles = cycles_result['documents']
            
            # Filtrar ciclos compatibles
            compatible_cycles = get_compatible_cycles_for_machine(
                dryer, 'dryer', available_cycles
            )
            
            # Obtener tipo de máquina para información adicional
            machine_type = get_machine_type_from_data(dryer, 'dryer')
            
            return {
                'success': True,
                'message': 'Ciclos compatibles obtenidos exitosamente',
                'data': {
                    'dryer_id': dryer_id,
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

    def validate_cycle_compatibility(self, dryer_id: str, cycle_id: str) -> Dict[str, Any]:
        """
        Validar si un ciclo específico es compatible con una secadora
        
        Args:
            dryer_id: ID de la secadora
            cycle_id: ID del ciclo
            
        Returns:
            Dict: Resultado de la validación
        """
        try:
            # Obtener datos de la secadora
            dryer = self.dryer_repository.find_by_id(dryer_id)
            if not dryer:
                return {
                    'success': False,
                    'message': 'Secadora no encontrada'
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
                cycle, dryer, 'dryer'
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
