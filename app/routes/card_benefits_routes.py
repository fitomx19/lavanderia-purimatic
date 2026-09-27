from flask import Blueprint, request
from marshmallow import ValidationError
from app.repositories.store_repository import StoreRepository
from app.schemas.card_benefits_schema import (
    card_benefits_settings_schema,
    card_benefits_response_schema,
)
from app.utils.auth_utils import admin_required, employee_required
from app.utils.response_utils import success_response, error_response
import logging

logger = logging.getLogger(__name__)

card_benefits_bp = Blueprint('card_benefits', __name__)
store_repository = StoreRepository()


@card_benefits_bp.route('/card-benefits-settings', methods=['GET'])
@employee_required
def get_card_benefits_settings(current_user):
    """Obtener configuración de beneficios de tarjeta."""
    try:
        data = store_repository.get_card_benefits_settings()
        return success_response(
            data=card_benefits_response_schema.dump(data),
            message='Configuración de beneficios obtenida',
        )
    except Exception as e:
        logger.error(f"Error obteniendo card_benefits_settings: {e}")
        return error_response('Error interno del servidor', 500)


@card_benefits_bp.route('/card-benefits-settings', methods=['PUT'])
@admin_required
def update_card_benefits_settings(current_user):
    """Actualizar configuración de beneficios de tarjeta (admin)."""
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = card_benefits_settings_schema.load(data)
        saved = store_repository.upsert_card_benefits_settings(validated)
        return success_response(
            data=card_benefits_response_schema.dump(saved),
            message='Configuración de beneficios guardada',
        )
    except ValidationError as e:
        return error_response('Datos de entrada inválidos', 400, errors=e.messages)
    except Exception as e:
        logger.error(f"Error guardando card_benefits_settings: {e}")
        return error_response('Error interno del servidor', 500)
