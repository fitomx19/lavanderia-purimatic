from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.sale_service import SaleService
from app.services.nfc_payment_service import NFCPaymentService
from app.utils.auth_utils import employee_required, admin_required
from app.utils.response_utils import success_response, error_response, paginated_response
from app import socketio # Importar la instancia de socketio
import logging

logger = logging.getLogger(__name__)

# Crear blueprint para rutas de ventas
sale_bp = Blueprint('sales', __name__)
sale_service = SaleService()
nfc_payment_service = NFCPaymentService()

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
        logger.info(f"Datos recibidos: {data}")
        
        # Agregar ID del empleado actual si no está presente
        if 'employee_id' not in data:
            data['employee_id'] = current_user['_id']
        
        # Crear venta
        result = sale_service.create_sale(data)
        
        if result['success']:
            # Emitir evento WebSocket para notificar nueva venta
            socketio.emit('new_sale', result['data'])
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
        exclude_finalized = request.args.get('exclude_finalized', False, type=bool) # Nuevo parámetro
        
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
        result = sale_service.get_sales_list(page, per_page, exclude_finalized, **filters) # Pasar exclude_finalized
        
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
            # Emitir evento WebSocket para notificar venta completada y estado de máquinas
            socketio.emit('sale_updated', result['data'])
            socketio.emit('machine_status_updated')
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"Error al completar venta: {e}")
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/<sale_id>/finalize', methods=['POST'])
@employee_required
def finalize_sale(current_user, sale_id):
    """
    Finalizar una venta
    POST /api/sales/{id}/finalize
    """
    try:
        result = sale_service.finalize_sale(sale_id)
        
        if result['success']:
            # Emitir evento WebSocket para notificar venta finalizada
            socketio.emit('sale_finalized', result['data'])
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

@sale_bp.route('/sales/deactivate-machines', methods=['POST'])
@admin_required
def deactivate_machines(current_user):
    """
    Verifica y desactiva máquinas cuyos ciclos de servicio han terminado.
    POST /api/sales/deactivate-machines
    """
    try:
        result = sale_service.check_and_deactivate_machines()
        
        if result['success']:
            # Emitir evento WebSocket para notificar cambios en el estado de las máquinas
            socketio.emit('machine_status_updated')
            return success_response(
                message=result['message']
            )
        else:
            return error_response(result['message'], 500)

    except Exception as e:
        return error_response('Error interno del servidor', 500) 

@sale_bp.route('/sales/monitor-status', methods=['GET'])
@admin_required
def get_monitor_status(current_user):
    """
    Obtener estado del monitor de máquinas
    GET /api/sales/monitor-status
    """
    try:
        from app.services.machine_monitor import machine_monitor
        status = machine_monitor.get_status()
        
        return success_response(
            data=status,
            message='Estado del monitor obtenido exitosamente'
        )
        
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/sales/check-services-now', methods=['POST'])
@admin_required
def check_services_now(current_user):
    """
    Forzar verificación inmediata de servicios completados
    POST /api/sales/check-services-now
    """
    try:
        from app.services.machine_monitor import machine_monitor
        result = machine_monitor.check_and_notify_completed_services()
        
        if result['success']:
            return success_response(
                data={'updated_count': result.get('updated_count', 0)},
                message=result['message']
            )
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/nfc/validate-payment', methods=['POST'])
@employee_required
def validate_nfc_payment(current_user):
    """
    Validar pago con tarjeta NFC
    POST /api/sales/nfc/validate-payment
    
    Body:
    {
        "amount": 25.50,
        "timeout": 30
    }
    """
    try:
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        amount = data.get('amount')
        timeout = data.get('timeout', 30)
        
        if not amount or amount <= 0:
            return error_response('Monto requerido y debe ser mayor a cero', 400)
        
        # Validar pago NFC
        result = nfc_payment_service.validate_payment_with_nfc(
            amount=float(amount), 
            timeout=int(timeout)
        )
        
        if result['success']:
            return success_response(
                data={
                    'card_data': result.get('card_data', {}),
                    'logs': result.get('logs', []),
                    'nfc_uid': result.get('nfc_uid')
                },
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors={'error_type': result.get('error_type'), 'card_data': result.get('card_data'), 'logs': result.get('logs', [])}
            )
            
    except Exception as e:
        logger.error(f"Error en validación NFC: {e}")
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/nfc/process-payment', methods=['POST'])
@employee_required
def process_nfc_payment(current_user):
    """
    Procesar pago con tarjeta NFC
    POST /api/sales/nfc/process-payment
    
    Body:
    {
        "nfc_uid": "91AC001E",
        "amount": 25.50
    }
    """
    try:
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        nfc_uid = data.get('nfc_uid')
        amount = data.get('amount')
        
        if not nfc_uid:
            return error_response('UID NFC requerido', 400)
        
        if not amount or amount <= 0:
            return error_response('Monto requerido y debe ser mayor a cero', 400)
        
        # Procesar pago NFC
        result = nfc_payment_service.process_nfc_payment(
            nfc_uid=nfc_uid,
            amount=float(amount)
        )
        
        if result['success']:
            return success_response(
                data=result.get('card_data', {}),
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400,
                errors={'error_type': result.get('error_type')}
            )
            
    except Exception as e:
        logger.error(f"Error procesando pago NFC: {e}")
        return error_response('Error interno del servidor', 500)

@sale_bp.route('/nfc/status', methods=['GET'])
@employee_required
def get_nfc_status(current_user):
    """
    Obtener estado del lector NFC
    GET /api/sales/nfc/status
    """
    try:
        result = nfc_payment_service.get_nfc_status()
        
        if result.get('success', False):
            return success_response(
                data=result.get('data', {}),
                message=result.get('message', 'Estado NFC obtenido')
            )
        else:
            return error_response(
                message=result.get('message', 'Error al obtener estado NFC'),
                status_code=503
            )
            
    except Exception as e:
        logger.error(f"Error obteniendo estado NFC: {e}")
        return error_response('Error interno del servidor', 500)