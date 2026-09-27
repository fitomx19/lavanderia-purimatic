from flask import Blueprint, request
from marshmallow import ValidationError
from app.repositories.store_repository import StoreRepository
from app.schemas.ticket_settings_schema import (
    ticket_settings_schema,
    ticket_settings_response_schema,
)
from app.utils.auth_utils import admin_required, employee_required
from app.utils.response_utils import success_response, error_response
import logging

logger = logging.getLogger(__name__)

ticket_settings_bp = Blueprint('ticket_settings', __name__)
store_repository = StoreRepository()


@ticket_settings_bp.route('/ticket-settings', methods=['GET'])
@employee_required
def get_ticket_settings(current_user):
    """Obtener configuración de ticket de la tienda."""
    try:
        include_logo = request.args.get('include_logo', 'false').lower() == 'true'
        data = store_repository.get_ticket_settings(include_logo=include_logo)
        return success_response(
            data=ticket_settings_response_schema.dump(data),
            message='Configuración de ticket obtenida',
        )
    except Exception as e:
        logger.error(f"Error obteniendo ticket_settings: {e}")
        return error_response('Error interno del servidor', 500)


@ticket_settings_bp.route('/ticket-settings', methods=['PUT'])
@admin_required
def update_ticket_settings(current_user):
    """
    Actualizar configuración de ticket (admin).

    Body JSON:
      store_name, wifi_password, promo_mes, printer_name,
      logo_base64 (opcional), logo_mime (opcional), clear_logo (bool)
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = ticket_settings_schema.load(data)
        saved = store_repository.upsert_ticket_settings(validated)
        return success_response(
            data=ticket_settings_response_schema.dump(saved),
            message='Configuración de ticket guardada',
        )
    except ValidationError as e:
        return error_response('Datos de entrada inválidos', 400, errors=e.messages)
    except Exception as e:
        logger.error(f"Error guardando ticket_settings: {e}")
        return error_response('Error interno del servidor', 500)


@ticket_settings_bp.route('/ticket-settings/printers', methods=['GET'])
@admin_required
def list_windows_printers(current_user):
    """Listar impresoras instaladas en Windows (para elegir en el CRUD)."""
    try:
        from app.services.ticket_print_service import TicketPrintService

        printers = TicketPrintService.list_printers()
        default_name = TicketPrintService.get_default_printer_name()
        return success_response(
            data={'printers': printers, 'default': default_name},
            message='Impresoras obtenidas',
        )
    except Exception as e:
        logger.error(f"Error listando impresoras: {e}")
        return error_response(
            'No se pudieron listar impresoras (¿Windows / pywin32?)',
            500,
        )


@ticket_settings_bp.route('/ticket-settings/test-print', methods=['POST'])
@admin_required
def test_ticket_print(current_user):
    """Imprimir un ticket de prueba con la configuración actual."""
    try:
        from app.services.ticket_print_service import TicketPrintService

        result = TicketPrintService().print_test_ticket()
        if result.get('success'):
            return success_response(
                data=result,
                message=result.get('message') or 'Ticket de prueba enviado',
            )
        return error_response(result.get('message') or 'No se pudo imprimir', 502)
    except Exception as e:
        logger.error(f"Error en test-print: {e}")
        return error_response('Error interno al imprimir', 500)
