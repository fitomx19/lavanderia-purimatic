from flask import Blueprint, request
from app.services.washer_service import WasherService
from app.utils.response_utils import success_response, error_response
from app.utils.auth_utils import employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de lavadoras
washer_bp = Blueprint('washers', __name__)

# Instanciar servicios
washer_service = WasherService()

@washer_bp.route('/', methods=['POST'])
@employee_required
def create_washer(current_user):
    """
    Crear nueva lavadora
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        numero: int - Número de la lavadora
        marca: str - Marca
        capacidad: int - Capacidad en kg
        store_id: str - ID de la tienda
        estado: str - Estado (disponible, ocupada, mantenimiento)
        
    Returns:
        JSON con datos de la lavadora creada
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar creación
        result = washer_service.create_or_update_washer(data)
        
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
        logger.error(f"Error en create washer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/', methods=['GET'])
@employee_required
def get_washers(current_user):
    """
    Obtener lista de lavadoras con paginación
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        store_id: str - Filtrar por tienda
        
    Returns:
        JSON con lista paginada de lavadoras
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        store_id = request.args.get('store_id')
        
        if store_id:
            # Procesar consulta por tienda
            result = washer_service.get_washers_by_store(
                store_id=store_id,
                page=page,
                per_page=per_page
            )
        else:
            return error_response('store_id es requerido', 400)
        
        if result['success']:
            return success_response(
                data={
                    'washers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get washers endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/<washer_id>', methods=['GET'])
@employee_required
def get_washer(current_user, washer_id):
    """
    Obtener lavadora por ID
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        
    Returns:
        JSON con datos de la lavadora
    """
    try:
        # Procesar consulta
        result = washer_service.get_washer_by_id(washer_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get washer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/<washer_id>', methods=['PUT'])
@employee_required
def update_washer(current_user, washer_id):
    """
    Actualizar lavadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        
    Body:
        numero: int - Número de la lavadora (opcional)
        marca: str - Marca (opcional)
        capacidad: int - Capacidad en kg (opcional)
        estado: str - Estado (opcional)
        is_active: bool - Estado activo (opcional)
        
    Returns:
        JSON con datos de la lavadora actualizada
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Agregar ID al data para el upsert
        data['_id'] = washer_id
        
        # Procesar actualización
        result = washer_service.create_or_update_washer(data)
        
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
        logger.error(f"Error en update washer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/<washer_id>', methods=['DELETE'])
@employee_required
def delete_washer(current_user, washer_id):
    """
    Eliminar lavadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        
    Returns:
        JSON confirmando la eliminación
    """
    try:
        # Procesar eliminación
        result = washer_service.delete_washer(washer_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en delete washer endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/<washer_id>/status', methods=['PUT'])
@employee_required
def update_washer_status(current_user, washer_id):
    """
    Actualizar estado de la lavadora
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        
    Body:
        estado: str - Nuevo estado (disponible, ocupada, mantenimiento)
        
    Returns:
        JSON con datos actualizados de la lavadora
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar actualización de estado
        result = washer_service.update_washer_status(washer_id, data)
        
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
        logger.error(f"Error en update washer status endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/store/<store_id>', methods=['GET'])
@employee_required
def get_washers_by_store(current_user, store_id):
    """
    Obtener lavadoras por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de lavadoras de la tienda
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = washer_service.get_washers_by_store(
            store_id=store_id,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'washers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get washers by store endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/store/<store_id>/available', methods=['GET'])
@employee_required
def get_available_washers(current_user, store_id):
    """
    Obtener lavadoras disponibles por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de lavadoras disponibles
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = washer_service.get_available_washers(
            store_id=store_id,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'washers': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get available washers endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@washer_bp.route('/store/<store_id>/statistics', methods=['GET'])
@employee_required
def get_store_statistics(current_user, store_id):
    """
    Obtener estadísticas de lavadoras por tienda
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        store_id: str - ID de la tienda
        
    Returns:
        JSON con estadísticas de lavadoras de la tienda
    """
    try:
        # Procesar consulta
        result = washer_service.get_store_statistics(store_id)
        
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

@washer_bp.route('/<washer_id>/compatible-cycles', methods=['GET'])
@employee_required
def get_compatible_cycles(current_user, washer_id):
    """
    Obtener ciclos compatibles con una lavadora específica
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        
    Returns:
        JSON con lista de ciclos compatibles
    """
    try:
        # Procesar consulta
        result = washer_service.get_compatible_cycles(washer_id)
        
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

@washer_bp.route('/<washer_id>/validate-cycle/<cycle_id>', methods=['GET'])
@employee_required
def validate_cycle_compatibility(current_user, washer_id, cycle_id):
    """
    Validar compatibilidad entre una lavadora y un ciclo específico
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        washer_id: str - ID de la lavadora
        cycle_id: str - ID del ciclo
        
    Returns:
        JSON con resultado de la validación
    """
    try:
        # Procesar validación
        result = washer_service.validate_cycle_compatibility(washer_id, cycle_id)
        
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

# Manejador de errores para el blueprint
@washer_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@washer_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@washer_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@washer_bp.errorhandler(404)
def not_found(error):
    return error_response('Recurso no encontrado', 404)

@washer_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en washer routes: {error}')
    return error_response('Error interno del servidor', 500)
