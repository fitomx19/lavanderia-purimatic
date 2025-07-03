from typing import Dict, Any, Optional
from app.repositories.user_employee_repository import UserEmployeeRepository
from app.utils.auth_utils import hash_password, verify_password, generate_token
from app.utils.validation_utils import validate_email, validate_password_strength
from app.schemas.user_employee_schema import (
    user_employee_login_schema,
    user_employee_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """
    Servicio de autenticación con lógica de negocio
    """
    
    def __init__(self):
        self.user_repository = UserEmployeeRepository()
    
    def login(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Autenticar usuario empleado
        
        Args:
            credentials: Credenciales de login (username, password)
            
        Returns:
            Dict: Resultado de la autenticación
        """
        try:
            # Validar datos de entrada
            validated_data = user_employee_login_schema.load(credentials)
            
            # Buscar usuario por username o email
            user = self.user_repository.find_by_username_or_email(
                validated_data['username']
            )
            
            if not user:
                return {
                    'success': False,
                    'message': 'Credenciales inválidas'
                }
            
            # Verificar contraseña
            if not verify_password(validated_data['password'], user['password_hash']):
                return {
                    'success': False,
                    'message': 'Credenciales inválidas'
                }
            
            # Verificar que el usuario esté activo
            if not user.get('is_active', False):
                return {
                    'success': False,
                    'message': 'Usuario inactivo'
                }
            
            # Generar token JWT
            token_claims = {
                'role': user['role'],
                'store_id': user['store_id'],
                'username': user['username']
            }
            
            token = generate_token(user['_id'], token_claims)
            
            # Preparar respuesta
            user_data = user_employee_response_schema.dump(user)
            
            return {
                'success': True,
                'message': 'Autenticación exitosa',
                'data': {
                    'user': user_data,
                    'token': token,
                    'token_type': 'Bearer'
                }
            }
            
        except ValidationError as e:
            logger.error(f"Error de validación en login: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en login: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información del usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Información del usuario o None
        """
        try:
            return self.user_repository.find_by_id(user_id)
        except Exception as e:
            logger.error(f"Error al obtener información del usuario: {e}")
            return None
    
    def verify_token(self, user_id: str) -> Dict[str, Any]:
        """
        Verificar token y obtener información del usuario
        
        Args:
            user_id: ID del usuario desde el token
            
        Returns:
            Dict: Información del usuario
        """
        try:
            user = self.user_repository.find_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'Usuario no encontrado'
                }
            
            if not user.get('is_active', False):
                return {
                    'success': False,
                    'message': 'Usuario inactivo'
                }
            
            user_data = user_employee_response_schema.dump(user)
            
            return {
                'success': True,
                'message': 'Token válido',
                'data': user_data
            }
            
        except Exception as e:
            logger.error(f"Error en verificación de token: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        Cambiar contraseña del usuario
        
        Args:
            user_id: ID del usuario
            old_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Dict: Resultado del cambio de contraseña
        """
        try:
            # Obtener usuario
            user = self.user_repository.find_by_id(user_id)
            
            if not user:
                return {
                    'success': False,
                    'message': 'Usuario no encontrado'
                }
            
            # Verificar contraseña actual
            if not verify_password(old_password, user['password_hash']):
                return {
                    'success': False,
                    'message': 'Contraseña actual incorrecta'
                }
            
            # Validar nueva contraseña
            is_valid, errors = validate_password_strength(new_password)
            if not is_valid:
                return {
                    'success': False,
                    'message': 'La nueva contraseña no cumple con los requisitos',
                    'errors': errors
                }
            
            # Actualizar contraseña
            new_password_hash = hash_password(new_password)
            
            updated_user = self.user_repository.upsert({
                '_id': user_id,
                'password_hash': new_password_hash
            })
            
            if updated_user:
                return {
                    'success': True,
                    'message': 'Contraseña actualizada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar la contraseña'
                }
                
        except Exception as e:
            logger.error(f"Error al cambiar contraseña: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def logout(self, user_id: str) -> Dict[str, Any]:
        """
        Cerrar sesión del usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Resultado del logout
        """
        try:
            # En una implementación más completa, aquí se podría
            # agregar el token a una lista de tokens revocados
            
            return {
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error en logout: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
