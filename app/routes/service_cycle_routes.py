from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.service_cycle_service import ServiceCycleService
from app.utils.auth_utils import employee_required, admin_required
from app.utils.response_utils import success_response, error_response, paginated_response

# Crear blueprint para rutas de ciclos de servicio
service_cycle_bp = Blueprint('service_cycles', __name__)
service_cycle_service = ServiceCycleService()

@service_cycle_bp.route('/service-cycles', methods=['GET'])
@employee_required
def get_service_cycles(current_user):
    """
    Obtener lista de ciclos de servicio
    GET /api/service-cycles
    """
    try:
        # Obtener parámetros de consulta
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        service_type = request.args.get('service_type', type=str)
        
        # Aplicar filtros según los parámetros
        if service_type:
            result = service_cycle_service.get_cycles_by_type(service_type)
            if result['success']:
                return success_response(
                    data=result['data'],
                    message=result['message']
                )
            else:
                return error_response(result['message'], 500)
        else:
            result = service_cycle_service.get_cycles_list(page, per_page)
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

@service_cycle_bp.route('/service-cycles', methods=['POST'])
@admin_required
def create_service_cycle(current_user):
    """
    Crear nuevo ciclo de servicio (UPSERT)
    POST /api/service-cycles
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        
        # Crear ciclo
        result = service_cycle_service.create_or_update_cycle(data)
        
        if result['success']:
            status_code = 201 if '_id' not in data else 200
            return success_response(
                data=result['data'],
                message=result['message'],
                status_code=status_code
            )
        else:
            status_code = 400
            if result.get('errors'):
                status_code = 422 # Código 422 para errores de validación
            return error_response(
                message=result['message'],
                errors=result.get('errors'),
                status_code=status_code
            )
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@service_cycle_bp.route('/service-cycles/<cycle_id>', methods=['GET'])
@employee_required
def get_service_cycle(current_user, cycle_id):
    """
    Obtener ciclo de servicio por ID
    GET /api/service-cycles/{id}
    """
    try:
        result = service_cycle_service.get_cycle_by_id(cycle_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@service_cycle_bp.route('/service-cycles/<cycle_id>', methods=['DELETE'])
@admin_required
def delete_service_cycle(current_user, cycle_id):
    """
    Eliminar ciclo de servicio (soft delete)
    DELETE /api/service-cycles/{id}
    """
    try:
        result = service_cycle_service.delete_cycle(cycle_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@service_cycle_bp.route('/service-cycles/initialize', methods=['POST'])
@admin_required
def initialize_default_cycles(current_user):
    """
    Inicializar ciclos de servicio predefinidos
    POST /api/service-cycles/initialize
    """
    try:
        result = service_cycle_service.initialize_default_cycles()
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500) 