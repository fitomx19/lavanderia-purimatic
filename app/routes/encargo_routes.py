from flask import Blueprint, request
from marshmallow import ValidationError
from app.services.encargo_service import EncargoService
from app.utils.auth_utils import employee_required, admin_required
from app.utils.response_utils import success_response, error_response
import logging

logger = logging.getLogger(__name__)

encargo_bp = Blueprint('encargos', __name__)
encargo_service = EncargoService()


@encargo_bp.route('/encargos/settings', methods=['GET'])
@employee_required
def get_encargo_settings(current_user):
    result = encargo_service.get_settings()
    return success_response(data=result['data'], message='Configuración de encargos')


@encargo_bp.route('/encargos/settings', methods=['PUT'])
@admin_required
def update_encargo_settings(current_user):
    data = request.get_json() or {}
    result = encargo_service.update_settings(data)
    if result.get('success'):
        return success_response(data=result['data'], message=result.get('message'))
    return error_response(result.get('message') or 'Error', 400, errors=result.get('errors'))


@encargo_bp.route('/encargos', methods=['GET'])
@employee_required
def list_encargos(current_user):
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        status = request.args.get('status')
        folio = request.args.get('folio')
        q = request.args.get('q')
        result = encargo_service.list_encargos(
            status=status, folio=folio, q=q, page=page, per_page=per_page
        )
        return success_response(data=result['data'], message='Encargos obtenidos')
    except Exception as e:
        logger.error(f"list encargos: {e}")
        return error_response('Error interno', 500)


@encargo_bp.route('/encargos', methods=['POST'])
@employee_required
def create_encargo(current_user):
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)
        employee_id = str(current_user.get('_id') or current_user.get('id') or '')
        result = encargo_service.create_encargo(data, employee_id)
        if result.get('success'):
            payload = result.get('data') or {}
            if isinstance(payload, dict):
                payload = {
                    **payload,
                    'ticket_printed': result.get('ticket_printed'),
                    'ticket_message': result.get('ticket_message'),
                    'bag_printed': result.get('bag_printed'),
                    'bag_message': result.get('bag_message'),
                }
            return success_response(data=payload, message=result.get('message'), status_code=201)
        return error_response(
            result.get('message') or 'Error',
            400,
            errors=result.get('errors'),
        )
    except Exception as e:
        logger.error(f"create encargo: {e}")
        return error_response('Error interno', 500)


@encargo_bp.route('/encargos/<encargo_id>', methods=['GET'])
@employee_required
def get_encargo(current_user, encargo_id):
    result = encargo_service.get_encargo(encargo_id)
    if result.get('success'):
        return success_response(data=result['data'])
    return error_response(result.get('message') or 'No encontrado', 404)


@encargo_bp.route('/encargos/<encargo_id>/status', methods=['POST'])
@employee_required
def update_encargo_status(current_user, encargo_id):
    data = request.get_json() or {}
    employee_id = str(current_user.get('_id') or current_user.get('id') or '')
    result = encargo_service.update_status(encargo_id, data, employee_id)
    if result.get('success'):
        return success_response(data=result['data'], message=result.get('message'))
    return error_response(result.get('message') or 'Error', 400, errors=result.get('errors'))


@encargo_bp.route('/encargos/<encargo_id>/reprint', methods=['POST'])
@employee_required
def reprint_encargo(current_user, encargo_id):
    employee_id = str(current_user.get('_id') or current_user.get('id') or '')
    result = encargo_service.reprint(encargo_id, employee_id)
    if result.get('success'):
        payload = result.get('data') or {}
        if isinstance(payload, dict):
            payload = {
                **payload,
                'ticket_printed': result.get('ticket_printed'),
                'ticket_message': result.get('ticket_message'),
                'bag_printed': result.get('bag_printed'),
                'bag_message': result.get('bag_message'),
            }
        return success_response(data=payload, message=result.get('message'))
    return error_response(result.get('message') or 'Error', 400)
