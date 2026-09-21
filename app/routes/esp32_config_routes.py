from flask import Blueprint, request
from marshmallow import ValidationError
from app.repositories.store_repository import StoreRepository
from app.schemas.esp32_config_schema import (
    esp32_config_schema,
    esp32_config_update_schema,
    esp32_config_response_schema,
    esp32_configs_response_schema,
)
from app.utils.auth_utils import employee_required
from app.utils.response_utils import success_response, error_response
import logging

logger = logging.getLogger(__name__)

esp32_config_bp = Blueprint('esp32_config', __name__)
store_repository = StoreRepository()


@esp32_config_bp.route('/esp32-config', methods=['GET'])
@employee_required
def list_esp32_configs(current_user):
    """Listar placas ESP32 registradas en esta tienda."""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        docs = store_repository.list_esp32_configs(include_inactive=include_inactive)
        return success_response(
            data=esp32_configs_response_schema.dump(docs),
            message='Configuraciones ESP32 obtenidas',
        )
    except Exception as e:
        logger.error(f"Error listando esp32_config: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<esp32_id>', methods=['GET'])
@employee_required
def get_esp32_config(current_user, esp32_id):
    """Obtener una placa ESP32 por su esp32_id."""
    try:
        doc = store_repository.get_esp32_config_by_id(esp32_id)
        if not doc:
            return error_response(f'No hay configuración para esp32_id {esp32_id}', 404)
        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Configuración ESP32 encontrada',
        )
    except Exception as e:
        logger.error(f"Error obteniendo esp32_config {esp32_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config', methods=['POST'])
@employee_required
def upsert_esp32_config(current_user):
    """
    Crear o actualizar una placa ESP32.

    Body:
        esp32_id: id de la placa (debe coincidir con washers.esp32_id)
        esp32_url: http://IP_LOCAL/laundry-update
        is_active: bool (opcional, default true)
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = esp32_config_schema.load(data)
        doc = store_repository.upsert_esp32_config(validated)
        if not doc:
            return error_response('No se pudo guardar la configuración ESP32', 400)

        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Configuración ESP32 guardada',
            status_code=201,
        )
    except ValidationError as e:
        return error_response('Datos de entrada inválidos', 400, errors=e.messages)
    except Exception as e:
        logger.error(f"Error guardando esp32_config: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<esp32_id>', methods=['PUT'])
@employee_required
def update_esp32_config(current_user, esp32_id):
    """Actualizar URL o estado activo de una placa ya registrada."""
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = esp32_config_update_schema.load(data)
        payload = {'esp32_id': str(esp32_id)}
        payload.update({k: v for k, v in validated.items() if v is not None})

        existing = store_repository.get_esp32_config_by_id(esp32_id)
        if not existing:
            return error_response(f'No hay configuración para esp32_id {esp32_id}', 404)

        if 'esp32_url' not in payload:
            payload['esp32_url'] = existing.get('esp32_url')
        if 'is_active' not in payload:
            payload['is_active'] = existing.get('is_active', True)

        doc = store_repository.upsert_esp32_config(payload)
        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Configuración ESP32 actualizada',
        )
    except ValidationError as e:
        return error_response('Datos de entrada inválidos', 400, errors=e.messages)
    except Exception as e:
        logger.error(f"Error actualizando esp32_config {esp32_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<esp32_id>/test', methods=['POST'])
@employee_required
def test_esp32_output(current_user, esp32_id):
    """
    Probar el relé de una placa sin crear una venta.
    Body: { "action": "start" } o { "action": "stop" }
    """
    try:
        from datetime import datetime, timedelta
        from app.services.esp32_service import ESP32Service

        data = request.get_json(silent=True) or {}
        action = str(data.get('action') or 'start').strip().lower()
        if action not in ('start', 'stop'):
            return error_response('action debe ser start o stop', 400)

        existing = store_repository.get_esp32_config_by_id(esp32_id)
        if not existing:
            return error_response(f'No hay configuración para esp32_id {esp32_id}', 404)

        now = datetime.utcnow()
        machine_data = {
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(minutes=1)).isoformat(),
        }
        service = ESP32Service()
        if action == 'stop':
            result = service.stop_machine(str(esp32_id), machine_data)
        else:
            result = service.start_machine(str(esp32_id), machine_data)

        if result.get('success'):
            verb = 'encendido' if action == 'start' else 'apagado'
            return success_response(
                data=result,
                message=f'Comando de {verb} enviado a {esp32_id}',
            )
        return error_response(result.get('message') or 'La placa no respondió', 502)
    except Exception as e:
        logger.error(f"Error probando ESP32 {esp32_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<esp32_id>', methods=['DELETE'])
@employee_required
def deactivate_esp32_config(current_user, esp32_id):
    """Desactivar una placa (no borra el documento)."""
    try:
        existing = store_repository.get_esp32_config_by_id(esp32_id)
        if not existing:
            return error_response(f'No hay configuración para esp32_id {esp32_id}', 404)

        doc = store_repository.upsert_esp32_config({
            'esp32_id': str(esp32_id),
            'esp32_url': existing.get('esp32_url'),
            'is_active': False,
        })
        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message=f'ESP32 {esp32_id} desactivado',
        )
    except Exception as e:
        logger.error(f"Error desactivando esp32_config {esp32_id}: {e}")
        return error_response('Error interno del servidor', 500)
