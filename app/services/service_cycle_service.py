from typing import Dict, Any, Optional
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.schemas.service_cycle_schema import (
    service_cycle_schema,
    service_cycle_update_schema,
    service_cycle_response_schema,
    service_cycles_response_schema
)
from app.services.washer_service import WasherService
from app.services.dryer_service import DryerService
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class ServiceCycleService:
    """
    Servicio para manejo de ciclos de servicio con lógica de negocio
    """
    
    def __init__(self):
        self.service_cycle_repository = ServiceCycleRepository()
        self.washer_service = WasherService()
        self.dryer_service = DryerService()
    
    def _validate_allowed_machines(self, allowed_machines: list) -> Dict[str, Any]:
        """
        Valida que los IDs de máquina en allowed_machines existan y estén activos,
        y que el nombre proporcionado coincida.
        """
        if not allowed_machines:
            return {'success': False, 'message': 'Se deben especificar IDs y nombres de máquinas permitidas.'}

        for machine_data in allowed_machines:
            machine_id = machine_data.get('_id')
            machine_name = machine_data.get('name')

            if not machine_id or not machine_name:
                return {'success': False, 'message': 'Cada máquina en allowed_machines debe tener _id y name.'}

            washer_result = self.washer_service.get_washer_by_id(machine_id)
            dryer_result = self.dryer_service.get_dryer_by_id(machine_id)

            found_machine = None
            if washer_result['success']:
                found_machine = washer_result['data']
            elif dryer_result['success']:
                found_machine = dryer_result['data']

            if not found_machine:
                return {'success': False, 'message': f'Máquina con ID {machine_id} no encontrada.'}

            if not found_machine.get('is_active', False):
                return {'success': False, 'message': f'Máquina con ID {machine_id} no está activa.'}
            
            # Validar que el nombre proporcionado coincida con el número de la máquina
            # Asumimos que el 'name' en allowed_machines debe ser el número de la máquina para identificación
            if str(found_machine.get('numero')) != machine_name:
                return {'success': False, "message": f"El nombre proporcionado para la máquina {machine_id} ({machine_name}) no coincide con el número de la máquina ({found_machine.get('numero')})."}
                
        return {'success': True, 'message': 'Máquinas validadas correctamente.'}

    def create_or_update_cycle(self, cycle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar ciclo de servicio usando UPSERT
        
        Args:
            cycle_data: Datos del ciclo de servicio
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            if '_id' in cycle_data:
                # Actualización
                validated_data = service_cycle_update_schema.load(cycle_data)
                cycle_id = cycle_data['_id']
                
                # Verificar que el ciclo existe
                existing_cycle = self.service_cycle_repository.find_by_id(cycle_id)
                if not existing_cycle:
                    return {
                        'success': False,
                        'message': 'Ciclo de servicio no encontrado'
                    }
                
                # Verificar unicidad del nombre si se está actualizando
                if validated_data and isinstance(validated_data, dict) and 'name' in validated_data:
                    if self.service_cycle_repository.name_exists(str(validated_data['name']), cycle_id):
                        return {
                            'success': False,
                            'message': 'El nombre del ciclo ya existe'
                        }
                
            else:
                # Creación
                validated_data = service_cycle_schema.load(cycle_data)
                
                # Verificar que tenemos datos válidos
                if not validated_data or not isinstance(validated_data, dict):
                    return {
                        'success': False,
                        'message': 'Error en validación de datos'
                    }
                
                # Verificar unicidad del nombre
                if self.service_cycle_repository.name_exists(str(validated_data['name'])):
                    return {
                        'success': False,
                        'message': 'El nombre del ciclo ya existe'
                    }
            
            # Verificar que tenemos datos válidos antes del upsert
            if not validated_data or not isinstance(validated_data, dict):
                return {
                    'success': False,
                    'message': 'Error en validación de datos'
                }
            
            # Validar las máquinas permitidas por ID
            if 'allowed_machines' in validated_data and validated_data['allowed_machines']:
                machine_validation_result = self._validate_allowed_machines(validated_data['allowed_machines'])
                if not machine_validation_result['success']:
                    return machine_validation_result

            # Realizar upsert
            cycle = self.service_cycle_repository.upsert(validated_data)
            
            if cycle:
                cycle_response = service_cycle_response_schema.dump(cycle)
                return {
                    'success': True,
                    'message': 'Ciclo de servicio guardado exitosamente',
                    'data': cycle_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar el ciclo de servicio'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en ciclo de servicio: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de ciclos: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_cycle_by_id(self, cycle_id: str) -> Dict[str, Any]:
        """
        Obtener ciclo de servicio por ID
        
        Args:
            cycle_id: ID del ciclo
            
        Returns:
            Dict: Información del ciclo
        """
        try:
            cycle = self.service_cycle_repository.find_by_id(cycle_id)
            
            if not cycle:
                return {
                    'success': False,
                    'message': 'Ciclo de servicio no encontrado'
                }
            
            cycle_response = service_cycle_response_schema.dump(cycle)
            return {
                'success': True,
                'message': 'Ciclo de servicio encontrado',
                'data': cycle_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener ciclo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_cycles_list(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener lista de ciclos de servicio activos
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de ciclos
        """
        try:
            result = self.service_cycle_repository.find_active_cycles(page, per_page)
            
            cycles_response = service_cycles_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Ciclos de servicio obtenidos exitosamente',
                'data': cycles_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de ciclos: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_cycles_by_type(self, service_type: str) -> Dict[str, Any]:
        """
        Obtener ciclos por tipo de servicio
        
        Args:
            service_type: Tipo de servicio (lavado, secado, combo, encargo_lavado, encargo_secado, mixto, mixto_encargo)
            
        Returns:
            Dict: Lista de ciclos del tipo especificado
        """
        try:
            cycles = self.service_cycle_repository.find_by_service_type(service_type)
            cycles_response = service_cycles_response_schema.dump(cycles)
            
            return {
                'success': True,
                'message': f'Ciclos de {service_type} obtenidos exitosamente',
                'data': cycles_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener ciclos por tipo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_cycle(self, cycle_id: str) -> Dict[str, Any]:
        """
        Eliminar ciclo de servicio (soft delete)
        
        Args:
            cycle_id: ID del ciclo
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el ciclo existe
            cycle = self.service_cycle_repository.find_by_id(cycle_id)
            if not cycle:
                return {
                    'success': False,
                    'message': 'Ciclo de servicio no encontrado'
                }
            
            # TODO: Verificar que no haya servicios activos usando este ciclo
            # Esto se implementará cuando tengamos el servicio de ventas
            
            # Realizar soft delete
            success = self.service_cycle_repository.soft_delete(cycle_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Ciclo de servicio eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar el ciclo de servicio'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar ciclo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def initialize_default_cycles(self) -> Dict[str, Any]:
        """
        Inicializar ciclos de servicio predefinidos (eliminado el uso de tipos genéricos)
        
        Returns:
            Dict: Resultado de la inicialización
        """
        return {
            'success': True,
            'message': 'La inicialización de ciclos por defecto con tipos de máquina genéricos ha sido eliminada. Por favor, cree ciclos con IDs de máquina específicos.',
            'data': []
        } 