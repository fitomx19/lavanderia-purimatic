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


@esp32_config_bp.route('/esp32-config/<board_id>', methods=['GET'])
@employee_required
def get_esp32_config(current_user, board_id):
    """Obtener una placa por _id o por un esp32_id contenido."""
    try:
        doc = store_repository.get_esp32_config_by_board_id(board_id)
        if not doc:
            doc = store_repository.get_esp32_config_by_id(board_id)
        if not doc:
            return error_response(f'No hay configuración para {board_id}', 404)
        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Configuración ESP32 encontrada',
        )
    except Exception as e:
        logger.error(f"Error obteniendo esp32_config {board_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config', methods=['POST'])
@employee_required
def upsert_esp32_config(current_user):
    """
    Crear una placa ESP32 (una URL + varios esp32_ids).

    Body:
        esp32_ids: ["W001", "W002"]  (o string "W001, W002")
        esp32_url: http://IP_LOCAL/laundry-update
        name: opcional
        is_active: bool (opcional)
        _id: si se envía, actualiza esa placa
    """
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = esp32_config_schema.load(data)
        if data.get('_id'):
            validated['_id'] = str(data['_id'])

        conflict_check = store_repository._ids_conflict(
            validated.get('esp32_ids') or [],
            exclude_board_id=validated.get('_id'),
        )
        if conflict_check:
            return error_response(
                f'El esp32_id "{conflict_check}" ya está asignado a otra placa',
                400,
            )

        # Asegurar lista (puede ser vacía al crear solo la placa)
        if validated.get('esp32_ids') is None:
            validated['esp32_ids'] = []

        doc = store_repository.upsert_esp32_config(validated)
        if not doc:
            return error_response(
                'No se pudo guardar la configuración ESP32 (¿IDs duplicados?)',
                400,
            )

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


@esp32_config_bp.route('/esp32-config/<board_id>', methods=['PUT'])
@employee_required
def update_esp32_config(current_user, board_id):
    """Actualizar URL, IDs o estado de una placa por su _id."""
    try:
        data = request.get_json()
        if not data:
            return error_response('Datos requeridos', 400)

        validated = esp32_config_update_schema.load(data)
        existing = store_repository.get_esp32_config_by_board_id(board_id)
        if not existing:
            # compat: board_id podría ser un esp32_id legacy
            existing = store_repository.get_esp32_config_by_id(board_id)
            if existing:
                board_id = existing['_id']
            else:
                return error_response(f'No hay configuración para {board_id}', 404)

        payload = {k: v for k, v in validated.items() if v is not None}
        if 'esp32_ids' in payload:
            conflict = store_repository._ids_conflict(payload['esp32_ids'], exclude_board_id=board_id)
            if conflict:
                return error_response(
                    f'El esp32_id "{conflict}" ya está asignado a otra placa',
                    400,
                )

        doc = store_repository.update_esp32_config_by_board_id(board_id, payload)
        if not doc:
            return error_response('No se pudo actualizar la placa', 400)

        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Configuración ESP32 actualizada',
        )
    except ValidationError as e:
        return error_response('Datos de entrada inválidos', 400, errors=e.messages)
    except Exception as e:
        logger.error(f"Error actualizando esp32_config {board_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<board_id>/test', methods=['POST'])
@employee_required
def test_esp32_output(current_user, board_id):
    """
    Probar el relé de un esp32_id de la placa sin crear una venta.
    Body: { "action": "start"|"stop", "esp32_id": "W001" }
    Si no se envía esp32_id, usa el primero de la placa.
    """
    try:
        from datetime import datetime, timedelta
        from app.services.esp32_service import ESP32Service

        data = request.get_json(silent=True) or {}
        action = str(data.get('action') or 'start').strip().lower()
        if action not in ('start', 'stop'):
            return error_response('action debe ser start o stop', 400)

        board = store_repository.get_esp32_config_by_board_id(board_id)
        if not board:
            board = store_repository.get_esp32_config_by_id(board_id)
        if not board:
            return error_response(f'No hay configuración para {board_id}', 404)

        ids = board.get('esp32_ids') or []
        relay_id = str(data.get('esp32_id') or '').strip()
        if not relay_id:
            relay_id = ids[0] if ids else board_id
        elif ids and relay_id not in ids:
            return error_response(
                f'esp32_id {relay_id} no pertenece a esta placa',
                400,
            )

        now = datetime.utcnow()
        machine_data = {
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(minutes=1)).isoformat(),
        }
        service = ESP32Service()
        if action == 'stop':
            result = service.stop_machine(str(relay_id), machine_data)
        else:
            result = service.start_machine(str(relay_id), machine_data)

        if result.get('success'):
            verb = 'encendido' if action == 'start' else 'apagado'
            return success_response(
                data=result,
                message=f'Comando de {verb} enviado a {relay_id}',
            )
        return error_response(result.get('message') or 'La placa no respondió', 502)
    except Exception as e:
        logger.error(f"Error probando ESP32 {board_id}: {e}")
        return error_response('Error interno del servidor', 500)


@esp32_config_bp.route('/esp32-config/<board_id>', methods=['DELETE'])
@employee_required
def deactivate_esp32_config(current_user, board_id):
    """Desactivar una placa (no borra el documento)."""
    try:
        existing = store_repository.get_esp32_config_by_board_id(board_id)
        if not existing:
            existing = store_repository.get_esp32_config_by_id(board_id)
            if existing:
                board_id = existing['_id']
            else:
                return error_response(f'No hay configuración para {board_id}', 404)

        doc = store_repository.deactivate_esp32_config_by_board_id(board_id)
        return success_response(
            data=esp32_config_response_schema.dump(doc),
            message='Placa ESP32 desactivada',
        )
    except Exception as e:
        logger.error(f"Error desactivando esp32_config {board_id}: {e}")
        return error_response('Error interno del servidor', 500)
