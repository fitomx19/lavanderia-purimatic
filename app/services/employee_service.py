from typing import Dict, Any, Optional
from app.repositories.user_employee_repository import UserEmployeeRepository
from app.utils.auth_utils import hash_password
from app.schemas.user_employee_schema import (
    user_employee_schema,
    user_employee_update_schema,
    user_employee_response_schema,
    users_employee_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class EmployeeService:
    """
    Servicio para manejo de empleados con lógica de negocio
    """
    
    def __init__(self):
        self.employee_repository = UserEmployeeRepository()
    
    def create_or_update_employee(self, employee_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar empleado usando UPSERT
        
        Args:
            employee_data: Datos del empleado
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            if '_id' in employee_data:
                # Actualización
                validated_data = user_employee_update_schema.load(employee_data)
                employee_id = employee_data['_id']
                
                # Verificar que el empleado existe
                existing_employee = self.employee_repository.find_by_id(employee_id)
                if not existing_employee:
                    return {
                        'success': False,
                        'message': 'Empleado no encontrado'
                    }
                
                # Verificar unicidad de campos si se están actualizando
                if 'username' in validated_data:
                    if self.employee_repository.username_exists(validated_data['username'], employee_id):
                        return {
                            'success': False,
                            'message': 'El nombre de usuario ya existe'
                        }
                
                if 'email' in validated_data:
                    if self.employee_repository.email_exists(validated_data['email'], employee_id):
                        return {
                            'success': False,
                            'message': 'El email ya existe'
                        }
                
                # Hash de contraseña si se proporciona
                if 'password' in validated_data:
                    validated_data['password_hash'] = hash_password(validated_data['password'])
                    del validated_data['password']
                
            else:
                # Creación
                validated_data = user_employee_schema.load(employee_data)
                
                # Verificar unicidad de campos
                if self.employee_repository.username_exists(validated_data['username']):
                    return {
                        'success': False,
                        'message': 'El nombre de usuario ya existe'
                    }
                
                if self.employee_repository.email_exists(validated_data['email']):
                    return {
                        'success': False,
                        'message': 'El email ya existe'
                    }
                
                # Hash de contraseña
                validated_data['password_hash'] = hash_password(validated_data['password'])
                del validated_data['password']
            
            # Realizar upsert
            employee = self.employee_repository.upsert(validated_data)
            
            if employee:
                employee_response = user_employee_response_schema.dump(employee)
                return {
                    'success': True,
                    'message': 'Empleado guardado exitosamente',
                    'data': employee_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar el empleado'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en empleado: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de empleado: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_employee_by_id(self, employee_id: str) -> Dict[str, Any]:
        """
        Obtener empleado por ID
        
        Args:
            employee_id: ID del empleado
            
        Returns:
            Dict: Información del empleado
        """
        try:
            employee = self.employee_repository.find_by_id(employee_id)
            
            if not employee:
                return {
                    'success': False,
                    'message': 'Empleado no encontrado'
                }
            
            employee_response = user_employee_response_schema.dump(employee)
            return {
                'success': True,
                'message': 'Empleado encontrado',
                'data': employee_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener empleado: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_employees_list(self, page: int = 1, per_page: int = 10, store_id: Optional[str] = None, role: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener lista de empleados con paginación
        
        Args:
            page: Página actual
            per_page: Elementos por página
            store_id: Filtrar por tienda
            role: Filtrar por rol
            
        Returns:
            Dict: Lista de empleados
        """
        try:
            if store_id:
                result = self.employee_repository.find_by_store(store_id, page, per_page)
            elif role:
                result = self.employee_repository.find_by_role(role, page, per_page)
            else:
                result = self.employee_repository.find_active_employees(page, per_page)
            
            employees_response = users_employee_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Empleados obtenidos exitosamente',
                'data': employees_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de empleados: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_employee(self, employee_id: str) -> Dict[str, Any]:
        """
        Eliminar empleado (soft delete)
        
        Args:
            employee_id: ID del empleado
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el empleado existe
            employee = self.employee_repository.find_by_id(employee_id)
            if not employee:
                return {
                    'success': False,
                    'message': 'Empleado no encontrado'
                }
            
            # Realizar soft delete
            deleted = self.employee_repository.soft_delete(employee_id)
            
            if deleted:
                return {
                    'success': True,
                    'message': 'Empleado eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar el empleado'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar empleado: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_employees_by_store(self, store_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Obtener empleados por tienda
        
        Args:
            store_id: ID de la tienda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de empleados de la tienda
        """
        return self.get_employees_list(page, per_page, store_id=store_id)
