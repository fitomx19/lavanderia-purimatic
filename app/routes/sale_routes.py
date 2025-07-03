from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.sale_service import SaleService
from app.utils.auth_utils import employee_required, admin_required
from app.utils.response_utils import success_response, error_response, paginated_response

# Crear blueprint para rutas de ventas
sale_bp = Blueprint('sales', __name__)
sale_service = SaleService()

@sale_bp.route('/sales', methods=['POST'])
@employee_required
def create_sale(current_user):
    """
    Crear nueva venta
    POST /api/sales
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        
        # Agregar ID del empleado actual si no está presente
        if 'employee_id' not in data:
            data['employee_id'] = current_user['_id']
        
        # Crear venta
        result = sale_service.create_sale(data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message'],
                status_code=201
            )
        else:
            return error_response(
                message=result['message'],
                errors=result.get('errors'),
                status_code=400
            )
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales', methods=['GET'])
@employee_required
def get_sales(current_user):
    """
    Obtener lista de ventas con filtros
    GET /api/sales
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', type=str)
        employee_id = request.args.get('employee_id', type=str)
        client_id = request.args.get('client_id', type=str)
        today = request.args.get('today', False, type=bool)
        
        # Preparar filtros
        filters = {}
        if status:
            filters['status'] = status
        if employee_id:
            filters['employee_id'] = employee_id
        if client_id:
            filters['client_id'] = client_id
        if today:
            filters['today'] = True
        
        # Obtener ventas
        result = sale_service.get_sales_list(page, per_page, **filters)
        
        if result['success']:
            pagination = result.get('pagination', {})
            return paginated_response(
                data=result['data'],
                page=pagination.get('page', page),
                per_page=pagination.get('per_page', per_page),
                total=pagination.get('total', 0),
                message=result['message']
            )
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/<sale_id>', methods=['GET'])
@employee_required
def get_sale(current_user, sale_id):
    """
    Obtener venta por ID
    GET /api/sales/{id}
    """
    try:
        result = sale_service.get_sale_by_id(sale_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/<sale_id>/status', methods=['PUT'])
@employee_required
def update_sale_status(current_user, sale_id):
    """
    Actualizar estado de una venta
    PUT /api/sales/{id}/status
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return error_response('Estado requerido', 400)
        
        if new_status not in ['pending', 'completed', 'cancelled']:
            return error_response('Estado inválido', 400)
        
        # Actualizar estado usando el repositorio directamente
        from app.repositories.sale_repository import SaleRepository
        sale_repository = SaleRepository()
        
        updated_sale = sale_repository.update_sale_status(sale_id, new_status)
        
        if updated_sale:
            return success_response(
                data=updated_sale,
                message=f'Estado de venta actualizado a {new_status}'
            )
        else:
            return error_response('Error al actualizar el estado', 400)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/<sale_id>/complete', methods=['POST'])
@employee_required
def complete_sale(current_user, sale_id):
    """
    Completar venta y activar servicios
    POST /api/sales/{id}/complete
    """
    try:
        result = sale_service.complete_sale(sale_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/summary', methods=['GET'])
@admin_required
def get_sales_summary(current_user):
    """
    Obtener resumen de ventas por rango de fechas
    GET /api/sales/summary?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return error_response('Fechas de inicio y fin son requeridas', 400)
        
        result = sale_service.get_sales_summary(start_date, end_date)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500) 