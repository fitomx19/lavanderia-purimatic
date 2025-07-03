from flask import Blueprint, request
from app.services.client_service import ClientService
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.auth_utils import employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de clientes
client_bp = Blueprint('clients', __name__)

# Instanciar servicios
client_service = ClientService()

@client_bp.route('/', methods=['POST'])
@employee_required
def create_client(current_user):
    """
    Crear nuevo cliente
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        nombre: str - Nombre del cliente
        telefono: str - Teléfono
        email: str - Email
        direccion: str - Dirección del cliente (opcional)
        
    Returns:
        JSON con datos del cliente creado
        
    Nota: El saldo de la tarjeta recargable se asigna solo cuando se crea una tarjeta
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar creación
        result = client_service.create_or_update_client(data)
        
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
        logger.error(f"Error en create client endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/', methods=['GET'])
@employee_required
def get_clients(current_user):
    """
    Obtener lista de clientes con paginación
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        search: str - Término de búsqueda por nombre
        
    Returns:
        JSON con lista paginada de clientes
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search')
        
        # Procesar consulta
        result = client_service.get_clients_list(
            page=page,
            per_page=per_page,
            search=search
        )
        
        if result['success']:
            return success_response(
                data={
                    'clients': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get clients endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/<client_id>', methods=['GET'])
@employee_required
def get_client(current_user, client_id):
    """
    Obtener cliente por ID
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        client_id: str - ID del cliente
        
    Returns:
        JSON con datos del cliente
    """
    try:
        # Procesar consulta
        result = client_service.get_client_by_id(client_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get client endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/<client_id>', methods=['PUT'])
@employee_required
def update_client(current_user, client_id):
    """
    Actualizar cliente
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        client_id: str - ID del cliente
        
    Body:
        nombre: str - Nombre del cliente (opcional)
        telefono: str - Teléfono (opcional)
        email: str - Email (opcional)
        is_active: bool - Estado activo (opcional)
        
    Returns:
        JSON con datos del cliente actualizado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Agregar ID al data para el upsert
        data['_id'] = client_id
        
        # Procesar actualización
        result = client_service.create_or_update_client(data)
        
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
        logger.error(f"Error en update client endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/<client_id>', methods=['DELETE'])
@employee_required
def delete_client(current_user, client_id):
    """
    Eliminar cliente
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        client_id: str - ID del cliente
        
    Returns:
        JSON confirmando la eliminación
    """
    try:
        # Procesar eliminación
        result = client_service.delete_client(client_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en delete client endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/<client_id>/balance', methods=['PUT'])
@employee_required
def update_client_balance(current_user, client_id):
    """
    Actualizar saldo de tarjeta recargable del cliente
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        client_id: str - ID del cliente
        
    Body:
        saldo_tarjeta_recargable: float - Cantidad a aplicar
        operacion: str - Tipo de operación (agregar, reducir, establecer)
        
    Returns:
        JSON con datos actualizados del cliente
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar actualización de saldo
        result = client_service.update_client_balance(client_id, data)
        
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
        logger.error(f"Error en update client balance endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@client_bp.route('/search', methods=['GET'])
@employee_required
def search_clients(current_user):
    """
    Buscar clientes por nombre
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        q: str - Término de búsqueda
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de clientes encontrados
    """
    try:
        # Obtener parámetros de consulta
        search_term = request.args.get('q')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not search_term:
            return error_response('Término de búsqueda requerido', 400)
        
        # Procesar búsqueda
        result = client_service.search_clients(
            search_term=search_term,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'clients': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en search clients endpoint: {e}")
        return error_response('Error interno del servidor', 500)

# Manejador de errores para el blueprint
@client_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@client_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@client_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@client_bp.errorhandler(404)
def not_found(error):
    return error_response('Recurso no encontrado', 404)

@client_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en client routes: {error}')
    return error_response('Error interno del servidor', 500)
