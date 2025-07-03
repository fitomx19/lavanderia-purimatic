from typing import Dict, Any, Optional
from app.repositories.service_cycle_repository import ServiceCycleRepository
from app.schemas.service_cycle_schema import (
    service_cycle_schema,
    service_cycle_update_schema,
    service_cycle_response_schema,
    service_cycles_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class ServiceCycleService:
    """
    Servicio para manejo de ciclos de servicio con lógica de negocio
    """
    
    def __init__(self):
        self.service_cycle_repository = ServiceCycleRepository()
    
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
            service_type: Tipo de servicio (lavado, secado, combo)
            
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
    
    def get_cycles_by_machine_type(self, machine_type: str) -> Dict[str, Any]:
        """
        Obtener ciclos compatibles con un tipo de máquina
        
        Args:
            machine_type: Tipo de máquina (chica, grande, secadora)
            
        Returns:
            Dict: Lista de ciclos compatibles
        """
        try:
            cycles = self.service_cycle_repository.find_by_machine_type(machine_type)
            cycles_response = service_cycles_response_schema.dump(cycles)
            
            return {
                'success': True,
                'message': f'Ciclos compatibles con máquina {machine_type} obtenidos exitosamente',
                'data': cycles_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener ciclos por máquina: {e}")
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
    
    def validate_cycle_for_machine(self, cycle_id: str, machine_type: str) -> Dict[str, Any]:
        """
        Validar si un ciclo es compatible con un tipo de máquina
        
        Args:
            cycle_id: ID del ciclo
            machine_type: Tipo de máquina
            
        Returns:
            Dict: Resultado de la validación
        """
        try:
            return self.service_cycle_repository.validate_cycle_for_machine(cycle_id, machine_type)
            
        except Exception as e:
            logger.error(f"Error en validación de ciclo: {e}")
            return {
                'valid': False,
                'message': 'Error interno del servidor'
            }
    
    def initialize_default_cycles(self) -> Dict[str, Any]:
        """
        Inicializar ciclos de servicio predefinidos
        
        Returns:
            Dict: Resultado de la inicialización
        """
        try:
            default_cycles = [
                {
                    'name': 'Lavado Chico',
                    'description': 'Ciclo de lavado para máquinas chicas',
                    'service_type': 'lavado',
                    'duration_minutes': 30,
                    'price': 25.00,
                    'machine_types_allowed': ['chica']
                },
                {
                    'name': 'Lavado Grande',
                    'description': 'Ciclo de lavado para máquinas grandes',
                    'service_type': 'lavado',
                    'duration_minutes': 45,
                    'price': 35.00,
                    'machine_types_allowed': ['grande']
                },
                {
                    'name': 'Secado',
                    'description': 'Ciclo de secado estándar',
                    'service_type': 'secado',
                    'duration_minutes': 30,
                    'price': 20.00,
                    'machine_types_allowed': ['secadora']
                },
                {
                    'name': 'Lavado + Secado Chico',
                    'description': 'Combo completo para máquinas chicas',
                    'service_type': 'combo',
                    'duration_minutes': 60,
                    'price': 40.00,
                    'machine_types_allowed': ['chica', 'secadora']
                },
                {
                    'name': 'Lavado + Secado Grande',
                    'description': 'Combo completo para máquinas grandes',
                    'service_type': 'combo',
                    'duration_minutes': 75,
                    'price': 50.00,
                    'machine_types_allowed': ['grande', 'secadora']
                }
            ]
            
            created_cycles = []
            for cycle_data in default_cycles:
                # Solo crear si no existe
                existing = self.service_cycle_repository.find_by_name(cycle_data['name'])
                if not existing:
                    result = self.create_or_update_cycle(cycle_data)
                    if result['success']:
                        created_cycles.append(result['data'])
            
            return {
                'success': True,
                'message': f'Ciclos predefinidos inicializados: {len(created_cycles)} creados',
                'data': created_cycles
            }
            
        except Exception as e:
            logger.error(f"Error al inicializar ciclos predefinidos: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            } 