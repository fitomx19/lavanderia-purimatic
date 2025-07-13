from flask import Blueprint, request
from app.services.dryer_service import DryerService
from app.utils.response_utils import success_response, error_response
from app.utils.auth_utils import employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de secadoras
dryer_bp = Blueprint('dryers', __name__)

# Instanciar servicios
dryer_service = DryerService()

@dryer_bp.route('', methods=['POST'])
@employee_required
def create_dryer(current_user):
    """
    Crear nueva secadora
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        numero: int - Número de la secadora
        marca: str - Marca
        capacidad: int - Capacidad en kg
        store_id: str - ID de la tienda
        estado: str - Estado (disponible, ocupada, mantenimiento)
        
    Returns:
        JSON con datos de la secadora creada
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar creación
        result = dryer_service.create_or_update_dryer(data)
        
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
        logger.error(f"Error en create dryer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('', methods=['GET'])
@employee_required
def get_dryers(current_user):
    """
    Obtener lista de secadoras con paginación
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        store_id: str - Filtrar por tienda
        
    Returns:
        JSON con lista paginada de secadoras
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        store_id = request.args.get('store_id')
        
        if store_id:
            # Procesar consulta por tienda
            result = dryer_service.get_dryers_by_store(
                store_id=store_id,
                page=page,
                per_page=per_page
            )
        else:
            return error_response('store_id es requerido', 400)
        
        if result['success']:
            return success_response(
                data={
                    'dryers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get dryers endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>', methods=['GET'])
@employee_required
def get_dryer(current_user, dryer_id):
    """
    Obtener secadora por ID
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        
    Returns:
        JSON con datos de la secadora
    """
    try:
        # Procesar consulta
        result = dryer_service.get_dryer_by_id(dryer_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get dryer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>', methods=['PUT'])
@employee_required
def update_dryer(current_user, dryer_id):
    """
    Actualizar secadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        
    Body:
        numero: int - Número de la secadora (opcional)
        marca: str - Marca (opcional)
        capacidad: int - Capacidad en kg (opcional)
        estado: str - Estado (opcional)
        is_active: bool - Estado activo (opcional)
        
    Returns:
        JSON con datos de la secadora actualizada
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Agregar ID al data para el upsert
        data['_id'] = dryer_id
        
        # Procesar actualización
        result = dryer_service.create_or_update_dryer(data)
        
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
        logger.error(f"Error en update dryer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>', methods=['DELETE'])
@employee_required
def delete_dryer(current_user, dryer_id):
    """
    Eliminar secadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        
    Returns:
        JSON confirmando la eliminación
    """
    try:
        # Procesar eliminación
        result = dryer_service.delete_dryer(dryer_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en delete dryer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>/status', methods=['PUT'])
@employee_required
def update_dryer_status(current_user, dryer_id):
    """
    Actualizar estado de la secadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        
    Body:
        estado: str - Nuevo estado (disponible, ocupada, mantenimiento)
        
    Returns:
        JSON con datos actualizados de la secadora
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar actualización de estado
        result = dryer_service.update_dryer_status(dryer_id, data)
        
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
        logger.error(f"Error en update dryer status endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/store/<store_id>', methods=['GET'])
@employee_required
def get_dryers_by_store(current_user, store_id):
    """
    Obtener secadoras por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de secadoras de la tienda
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = dryer_service.get_dryers_by_store(
            store_id=store_id,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'dryers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get dryers by store endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/store/<store_id>/available', methods=['GET'])
@employee_required
def get_available_dryers(current_user, store_id):
    """
    Obtener secadoras disponibles por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de secadoras disponibles
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = dryer_service.get_available_dryers(
            store_id=store_id,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'dryers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get available dryers endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/store/<store_id>/statistics', methods=['GET'])
@employee_required
def get_store_statistics(current_user, store_id):
    """
    Obtener estadísticas de secadoras por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Returns:
        JSON con estadísticas de secadoras de la tienda
    """
    try:
        # Procesar consulta
        result = dryer_service.get_store_statistics(store_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get store statistics endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>/compatible-cycles', methods=['GET'])
@employee_required
def get_compatible_cycles(current_user, dryer_id):
    """
    Obtener ciclos compatibles con una secadora específica
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        
    Returns:
        JSON con lista de ciclos compatibles
    """
    try:
        # Procesar consulta
        result = dryer_service.get_compatible_cycles(dryer_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get compatible cycles endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/<dryer_id>/validate-cycle/<cycle_id>', methods=['GET'])
@employee_required
def validate_cycle_compatibility(current_user, dryer_id, cycle_id):
    """
    Validar compatibilidad entre una secadora y un ciclo específico
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        dryer_id: str - ID de la secadora
        cycle_id: str - ID del ciclo
        
    Returns:
        JSON con resultado de la validación
    """
    try:
        # Procesar validación
        result = dryer_service.validate_cycle_compatibility(dryer_id, cycle_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en validate cycle compatibility endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@dryer_bp.route('/all-active', methods=['GET'])
@employee_required
def get_all_active_dryers(current_user):
    """
    Obtener todas las secadoras activas sin importar su estado.
    
    Headers:
        Authorization: Bearer <token>
        
    Returns:
        JSON con lista de secadoras activas.
    """
    try:
        result = dryer_service.get_all_active_dryers()
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        logger.error(f"Error en get_all_active_dryers endpoint: {e}")
        return error_response('Error interno del servidor', 500)

# Manejador de errores para el blueprint
@dryer_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@dryer_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@dryer_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@dryer_bp.errorhandler(404)
def not_found(error):
    return error_response('Recurso no encontrado', 404)

@dryer_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en dryer routes: {error}')
    return error_response('Error interno del servidor', 500)
