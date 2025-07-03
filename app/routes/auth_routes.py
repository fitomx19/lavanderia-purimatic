from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.services.auth_service import AuthService
from app.utils.response_utils import success_response, error_response, validation_error_response
from app.utils.auth_utils import employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de autenticación
auth_bp = Blueprint('auth', __name__)

# Instanciar servicios
auth_service = AuthService()

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login para usuarios empleados
    
    Body:
        username: str - Nombre de usuario o email
        password: str - Contraseña
        
    Returns:
        JSON con token JWT y datos del usuario
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar login
        result = auth_service.login(data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            status_code = 401 if 'Credenciales' in result['message'] else 400
            return error_response(
                message=result['message'],
                status_code=status_code,
                errors=result.get('errors')
            )
            
    except Exception as e:
        logger.error(f"Error en login endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@auth_bp.route('/logout', methods=['POST'])
@employee_required
def logout(current_user):
    """
    Endpoint de logout para usuarios empleados
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON confirmando el logout
    """
    try:
        # Obtener ID del usuario actual
        user_id = get_jwt_identity()
        
        # Procesar logout
        result = auth_service.logout(user_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en logout endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@auth_bp.route('/verify', methods=['GET'])
@employee_required
def verify_token(current_user):
    """
    Endpoint para verificar la validez del token JWT
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON con datos del usuario si el token es válido
    """
    try:
        # Obtener ID del usuario actual
        user_id = get_jwt_identity()
        
        # Verificar token
        result = auth_service.verify_token(user_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 401)
            
    except Exception as e:
        logger.error(f"Error en verify endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@auth_bp.route('/change-password', methods=['PUT'])
@employee_required
def change_password(current_user):
    """
    Endpoint para cambiar contraseña del usuario
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        old_password: str - Contraseña actual
        new_password: str - Nueva contraseña
        
    Returns:
        JSON confirmando el cambio de contraseña
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Validar campos requeridos
        required_fields = ['old_password', 'new_password']
        for field in required_fields:
            if field not in data:
                return error_response(f'Campo requerido: {field}', 400)
        
        # Obtener ID del usuario actual
        user_id = get_jwt_identity()
        
        # Procesar cambio de contraseña
        result = auth_service.change_password(
            user_id,
            data['old_password'],
            data['new_password']
        )
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors=result.get('errors')
            )
            
    except Exception as e:
        logger.error(f"Error en change password endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@auth_bp.route('/profile', methods=['GET'])
@employee_required
def get_profile(current_user):
    """
    Endpoint para obtener perfil del usuario actual
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON con datos del usuario
    """
    try:
        return success_response(
            data=current_user,
            message='Perfil obtenido exitosamente'
        )
        
    except Exception as e:
        logger.error(f"Error en profile endpoint: {e}")
        return error_response('Error interno del servidor', 500)

# Manejador de errores para el blueprint
@auth_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@auth_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@auth_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@auth_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en auth routes: {error}')
    return error_response('Error interno del servidor', 500)
