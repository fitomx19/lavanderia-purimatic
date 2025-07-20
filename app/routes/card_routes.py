from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.card_service import CardService
from app.utils.auth_utils import employee_required
from app.utils.response_utils import success_response, error_response

# Crear blueprint para rutas de tarjetas
card_bp = Blueprint('cards', __name__)
card_service = CardService()

@card_bp.route('/clients/<client_id>/cards', methods=['POST'])
@employee_required
def create_card(current_user, client_id):
    """
    Crear nueva tarjeta para un cliente
    POST /api/clients/{client_id}/cards
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        data['client_id'] = client_id
        
        # Crear tarjeta
        result = card_service.create_card(data)
        
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

@card_bp.route('/clients/<client_id>/cards', methods=['GET'])
@employee_required
def get_client_cards(current_user, client_id):
    """
    Obtener tarjetas de un cliente
    GET /api/clients/{client_id}/cards
    """
    try:
        result = card_service.get_client_cards(client_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/<card_id>/add-balance', methods=['POST'])
@employee_required
def add_balance(current_user, card_id):
    """
    Agregar saldo a una tarjeta
    POST /api/cards/{card_id}/add-balance
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        
        # Agregar saldo
        result = card_service.add_balance(card_id, data)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                errors=result.get('errors'),
                status_code=400
            )
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/transfer-balance', methods=['POST'])
@employee_required
def transfer_balance(current_user):
    """
    Transferir saldo entre tarjetas
    POST /api/cards/transfer-balance
    """
    try:
        # Validar que los datos JSON estén presentes
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        
        # Transferir saldo
        result = card_service.transfer_balance(data)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(
                message=result['message'],
                errors=result.get('errors'),
                status_code=400
            )
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/<card_id>', methods=['DELETE'])
@employee_required
def delete_card(current_user, card_id):
    """
    Eliminar tarjeta (soft delete)
    DELETE /api/cards/{card_id}
    """
    try:
        result = card_service.delete_card(card_id)
        
        if result['success']:
            return success_response(message=result['message'])
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/<card_id>/balance', methods=['GET'])
@employee_required
def get_card_balance(current_user, card_id):
    """
    Consultar saldo de una tarjeta
    GET /api/cards/{card_id}/balance
    """
    try:
        result = card_service.get_card_balance(card_id)
        
        if result['success']:
            return success_response(
                data=result['data'],
                message=result['message']
            )
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/<card_id>/link-nfc', methods=['POST'])
@employee_required
def link_card_nfc(current_user, card_id):
    """
    Vincular tarjeta lógica con UID NFC físico
    POST /api/cards/{card_id}/link-nfc
    """
    try:
        result = card_service.link_nfc_to_card(card_id)
        if result['success']:
            return success_response(data=result['data'], message=result['message'])
        else:
            return error_response(result['message'], 400)
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/cards/reload-nfc', methods=['POST'])
@employee_required
def reload_card_nfc(current_user):
    """
    Recargar tarjeta mediante lectura NFC
    POST /api/cards/reload-nfc
    """
    try:
        if not request.is_json or not request.get_json():
            return error_response('Datos JSON requeridos', 400)
        
        data = request.get_json()
        amount = float(data.get('amount', 0))
        
        if amount <= 0:
            return error_response('Monto debe ser mayor a 0', 400)
        
        result = card_service.reload_card_via_nfc(amount)
        if result['success']:
            return success_response(data=result['data'], message=result['message'])
        else:
            return error_response(result['message'], 400)
    except Exception as e:
        return error_response('Error interno del servidor', 500)

@card_bp.route('/nfc/status', methods=['GET'])
@employee_required
def get_nfc_status(current_user):
    """
    Obtener estado del lector NFC
    GET /api/nfc/status
    """
    try:
        from app.services.nfc_client_service import NFCClientService
        nfc_client = NFCClientService()
        result = nfc_client.get_status()
        return success_response(data=result, message="Estado NFC obtenido")
    except Exception as e:
        return error_response('Error al consultar estado NFC', 500)

@card_bp.route('/cards/query-balance-nfc', methods=['POST'])
@employee_required
def query_balance_nfc(current_user):
    """
    Consultar saldo de tarjeta mediante lectura NFC
    POST /api/cards/query-balance-nfc
    """
    try:
        result = card_service.query_balance_via_nfc()
        if result['success']:
            return success_response(
                data=result['data'], 
                message=result['message']
            )
        else:
            return error_response(
                message=result['message'],
                status_code=400
            )
    except Exception as e:
        return error_response('Error interno del servidor', 500)