from flask import Blueprint, request
from app.services.product_service import ProductService
from app.utils.response_utils import success_response, error_response
from app.utils.auth_utils import employee_required
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de productos
product_bp = Blueprint('products', __name__)

# Instanciar servicios
product_service = ProductService()

@product_bp.route('', methods=['POST'])
@employee_required
def create_product(current_user):
    """
    Crear nuevo producto
    
    Headers:
        Authorization: Bearer <token>
        
    Body:
        nombre: str - Nombre del producto
        descripcion: str - Descripción
        precio: float - Precio
        tipo: str - Tipo (jabon, bolsas, suavizante, etc.)
        stock: int - Stock inicial
        
    Returns:
        JSON con datos del producto creado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Procesar creación
        result = product_service.create_or_update_product(data)
        
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
        logger.error(f"Error en create product endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('', methods=['GET'])
@employee_required
def get_products(current_user):
    """
    Obtener lista de productos con paginación
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        tipo: str - Filtrar por tipo
        search: str - Término de búsqueda
        
    Returns:
        JSON con lista paginada de productos
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        tipo = request.args.get('tipo')
        search = request.args.get('search')
        
        # Procesar consulta
        result = product_service.get_products_list(
            page=page,
            per_page=per_page,
            tipo=tipo,
            search=search
        )
        
        if result['success']:
            return success_response(
                data={
                    'products': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get products endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/<product_id>', methods=['GET'])
@employee_required
def get_product(current_user, product_id):
    """
    Obtener producto por ID
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        product_id: str - ID del producto
        
    Returns:
        JSON con datos del producto
    """
    try:
        # Procesar consulta
        result = product_service.get_product_by_id(product_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"Error en get product endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/<product_id>', methods=['PUT'])
@employee_required
def update_product(current_user, product_id):
    """
    Actualizar producto
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        product_id: str - ID del producto
        
    Body:
        nombre: str - Nombre del producto (opcional)
        descripcion: str - Descripción (opcional)
        precio: float - Precio (opcional)
        tipo: str - Tipo (opcional)
        stock: int - Stock (opcional)
        is_active: bool - Estado activo (opcional)
        
    Returns:
        JSON con datos del producto actualizado
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Agregar ID al data para el upsert
        data['_id'] = product_id
        
        # Procesar actualización
        result = product_service.create_or_update_product(data)
        
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
        logger.error(f"Error en update product endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/<product_id>', methods=['DELETE'])
@employee_required
def delete_product(current_user, product_id):
    """
    Eliminar producto
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        product_id: str - ID del producto
        
    Returns:
        JSON confirmando la eliminación
    """
    try:
        # Procesar eliminación
        result = product_service.delete_product(product_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en delete product endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/<product_id>/stock', methods=['PUT'])
@employee_required
def update_product_stock(current_user, product_id):
    """
    Actualizar stock del producto
    
    Headers:
        Authorization: Bearer <token>
        
    Path Parameters:
        product_id: str - ID del producto
        
    Body:
        amount: int - Cantidad a aplicar
        operation: str - Tipo de operación (agregar, reducir, establecer)
        
    Returns:
        JSON con datos actualizados del producto
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return error_response('Datos requeridos', 400)
        
        # Validar campos requeridos
        if 'amount' not in data or 'operation' not in data:
            return error_response('Campos requeridos: amount, operation', 400)
        
        # Procesar actualización de stock
        result = product_service.update_product_stock(
            product_id,
            data['amount'],
            data['operation']
        )
        
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
        logger.error(f"Error en update product stock endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/low-stock', methods=['GET'])
@employee_required
def get_low_stock_products(current_user):
    """
    Obtener productos con stock bajo
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        threshold: int - Umbral de stock bajo (default: 10)
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de productos con stock bajo
    """
    try:
        # Obtener parámetros de consulta
        threshold = request.args.get('threshold', 10, type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Procesar consulta
        result = product_service.get_low_stock_products(
            threshold=threshold,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'products': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en get low stock products endpoint: {e}")
        return error_response('Error interno del servidor', 500)

@product_bp.route('/search', methods=['GET'])
@employee_required
def search_products(current_user):
    """
    Buscar productos por nombre o descripción
    
    Headers:
        Authorization: Bearer <token>
        
    Query Parameters:
        q: str - Término de búsqueda
        page: int - Página actual (default: 1)
        per_page: int - Elementos por página (default: 10)
        
    Returns:
        JSON con lista paginada de productos encontrados
    """
    try:
        # Obtener parámetros de consulta
        search_term = request.args.get('q')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not search_term:
            return error_response('Término de búsqueda requerido', 400)
        
        # Procesar búsqueda
        result = product_service.search_products(
            search_term=search_term,
            page=page,
            per_page=per_page
        )
        
        if result['success']:
            return success_response(
                data={
                    'products': result['data'],
                    'pagination': result['pagination']
                },
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error en search products endpoint: {e}")
        return error_response('Error interno del servidor', 500)

# Manejador de errores para el blueprint
@product_bp.errorhandler(400)
def bad_request(error):
    return error_response('Solicitud incorrecta', 400)

@product_bp.errorhandler(401)
def unauthorized(error):
    return error_response('No autorizado', 401)

@product_bp.errorhandler(403)
def forbidden(error):
    return error_response('Acceso prohibido', 403)

@product_bp.errorhandler(404)
def not_found(error):
    return error_response('Recurso no encontrado', 404)

@product_bp.errorhandler(500)
def internal_error(error):
    logger.error(f'Error interno en product routes: {error}')
    return error_response('Error interno del servidor', 500)
