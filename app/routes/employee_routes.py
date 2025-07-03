from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.services.employee_service import EmployeeService
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.auth_utils import admin_required, employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de empleados
employee_bp = Blueprint('employees', __name__)

# Instanciar servicios
employee_service = EmployeeService()

@employee_bp.route('/', methods=['POST'])
@admin_required
def create_employee(current_user):
    """
    Crear nuevo empleado (solo admin)
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        username: str - Nombre de usuario
        email: str - Email
        password: str - Contraseña
        role: str - Rol (admin/empleado)
        store_id: str - ID de la tienda
        
    Returns:
        JSON con datos del empleado creado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar creación
        result = employee_service.create_or_update_employee(data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message'],
                status_code=201
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors=result.get('errors')
            )
            
    except Exception as e:
        logger.error(f"Error en create employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/', methods=['GET'])
@employee_required
def get_employees(current_user):
    """
    Obtener lista de empleados con paginación
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        store_id: str - Filtrar por tienda
        role: str - Filtrar por rol
        
    Returns:
        JSON con lista paginada de empleados
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        store_id = request.args.get('store_id')
        role = request.args.get('role')
        
        # Procesar consulta
        result = employee_service.get_employees_list(
            page=page,
            per_page=per_page,
            store_id=store_id,
            role=role
        )
        
        if result['success']:
            return paginated_response(
                data=result['data'],
                pagination=result['pagination'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get employees endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/<employee_id>', methods=['GET'])
@employee_required
def get_employee(current_user, employee_id):
    """
    Obtener empleado por ID
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        employee_id: str - ID del empleado
        
    Returns:
        JSON con datos del empleado
    """
    try:
        # Procesar consulta
        result = employee_service.get_employee_by_id(employee_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/<employee_id>', methods=['PUT'])
@admin_required
def update_employee(current_user, employee_id):
    """
    Actualizar empleado (solo admin)
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        employee_id: str - ID del empleado
        
    Body:
        username: str - Nombre de usuario (opcional)
        email: str - Email (opcional)
        password: str - Contraseña (opcional)
        role: str - Rol (opcional)
        store_id: str - ID de la tienda (opcional)
        is_active: bool - Estado activo (opcional)
        
    Returns:
        JSON con datos del empleado actualizado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Agregar ID al data para el upsert
        data['_id'] = employee_id
        
        # Procesar actualización
        result = employee_service.create_or_update_employee(data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors=result.get('errors')
            )
            
    except Exception as e:
        logger.error(f"Error en update employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/<employee_id>', methods=['DELETE'])
@admin_required
def delete_employee(current_user, employee_id):
    """
    Eliminar empleado (solo admin)
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        employee_id: str - ID del empleado
        
    Returns:
        JSON confirmando la eliminación
    """
    try:
        # Verificar que no se esté eliminando a sí mismo
        if employee_id == current_user['_id']:
            return error_response('No puedes eliminar tu propio usuario', 400)
        
        # Procesar eliminación
        result = employee_service.delete_employee(employee_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en delete employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/store/<store_id>', methods=['GET'])
@employee_required
def get_employees_by_store(current_user, store_id):
    """
    Obtener empleados por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de empleados de la tienda
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = employee_service.get_employees_by_store(
            store_id=store_id,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return paginated_response(
                data=result['data'],
                pagination=result['pagination'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get employees by store endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/current', methods=['GET'])
@employee_required
def get_current_employee(current_user):
    """
    Obtener datos del empleado actual
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON con datos del empleado actual
    """
    try:
        return success_response(
            data=current_user,
            message='Empleado actual obtenido exitosamente'
        )
        
    except Exception as e:
        logger.error(f"Error en get current employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@employee_bp.route('/current', methods=['PUT'])
@employee_required
def update_current_employee(current_user):
    """
    Actualizar datos del empleado actual (campos limitados)
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        email: str - Email (opcional)
        password: str - Contraseña (opcional)
        
    Returns:
        JSON con datos actualizados del empleado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Permitir solo campos específicos para auto-actualización
        allowed_fields = ['email', 'password']
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not filtered_data:
            return error_response('No hay campos válidos para actualizar', 400)
        
        # Agregar ID al data para el upsert
        filtered_data['_id'] = current_user['_id']
        
        # Procesar actualización
        result = employee_service.create_or_update_employee(filtered_data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors=result.get('errors')
            )
            
    except Exception as e:
        logger.error(f"Error en update current employee endpoint: {e}")
        return error_response('Error interno del servidor', 500)

# Manejador de errores para el blueprint
@employee_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@employee_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@employee_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@employee_bp.errorhandler(404)
def not_found(error):
    return error_response('Recurso no encontrado', 404)

@employee_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en employee routes: {error}')
    return error_response('Error interno del servidor', 500)
