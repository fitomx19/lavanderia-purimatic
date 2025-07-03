import bcrypt
from functools import wraps
from flask import current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from app.utils.response_utils import error_response

def hash_password(password: str) -> str:
    """
    Generar hash de contraseña usando bcrypt
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        str: Hash de la contraseña
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verificar contraseña contra su hash
    
    Args:
        password: Contraseña en texto plano
        password_hash: Hash de la contraseña almacenado
        
    Returns:
        bool: True si la contraseña es correcta
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def generate_token(user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generar token JWT para usuario
    
    Args:
        user_id: ID del usuario
        additional_claims: Claims adicionales para el token
        
    Returns:
        str: Token JWT
    """
    return create_access_token(
        identity=user_id,
        additional_claims=additional_claims or {}
    )

def role_required(required_roles: list) -> Callable:
    """
    Decorador para requerir roles específicos
    
    Args:
        required_roles: Lista de roles requeridos
        
    Returns:
        Callable: Decorador
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from app.services.auth_service import AuthService
            
            # Obtener información del usuario actual
            current_user_id = get_jwt_identity()
            auth_service = AuthService()
            
            try:
                user_info = auth_service.get_user_info(current_user_id)
                
                if not user_info:
                    return error_response("Usuario no encontrado", 404)
                
                user_role = user_info.get('role')
                
                if user_role not in required_roles:
                    return error_response("Acceso denegado: permisos insuficientes", 403)
                
                # Pasar información del usuario a la función decorada
                return f(current_user=user_info, *args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Error en verificación de rol: {e}")
                return error_response("Error interno de autenticación", 500)
                
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorador para requerir rol de administrador
    
    Args:
        f: Función a decorar
        
    Returns:
        Función decorada
    """
    return role_required(['admin'])(f)

def employee_required(f):
    """
    Decorador para requerir rol de empleado o admin
    
    Args:
        f: Función a decorar
        
    Returns:
        Función decorada
    """
    return role_required(['admin', 'empleado'])(f)

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Obtener información del usuario actual desde el token
    
    Returns:
        Dict con información del usuario o None si no está autenticado
    """
    try:
        from app.services.auth_service import AuthService
        
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return None
            
        auth_service = AuthService()
        return auth_service.get_user_info(current_user_id)
        
    except Exception:
        return None

def validate_token_claims(required_claims: Dict[str, Any]) -> Callable:
    """
    Decorador para validar claims específicos en el token
    
    Args:
        required_claims: Claims requeridos
        
    Returns:
        Callable: Decorador
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt
            
            claims = get_jwt()
            
            for claim_key, claim_value in required_claims.items():
                if claims.get(claim_key) != claim_value:
                    return error_response(f"Claim inválido: {claim_key}", 403)
            
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator
