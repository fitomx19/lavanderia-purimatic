"""
Rutas HTTP del puente ESP32.

La API principal (puerto 5000) llama POST /send-to-esp32 en este
microservicio (puerto 5001) para prender/apagar las placas físicas.
"""

import time
import logging
from flask import Blueprint, request

from app.esp32_manager import ESP32Manager
from app.utils.response_utils import success_response, error_response

esp32_bp = Blueprint('esp32', __name__)
esp32_manager = ESP32Manager()
logger = logging.getLogger(__name__)


@esp32_bp.route('/send-to-esp32', methods=['POST'])
def send_to_esp32():
    """
    Reenviar laundry_data al ESP32 físico.

    Body esperado:
    {
      "esp32_url": "http://192.168.1.76/laundry-update",
      "laundry_data": {
        "washer_id": "76",
        "start_time": "...",
        "end_time": "...",
        "status": "starting"
      }
    }
    """
    start_time = time.time()
    payload = request.get_json(silent=True) or {}

    esp32_url = payload.get('esp32_url')
    laundry_data = payload.get('laundry_data')

    if not esp32_url:
        return error_response(
            message='esp32_url es requerida',
            status_code=400,
            error_code='MISSING_ESP32_URL',
            start_time=start_time,
        )

    if not laundry_data:
        return error_response(
            message='laundry_data es requerido',
            status_code=400,
            error_code='MISSING_LAUNDRY_DATA',
            start_time=start_time,
        )

    result = esp32_manager.send_laundry_update(esp32_url, laundry_data)

    if result['success']:
        return success_response(
            message=result['message'],
            data={
                'esp32_url': esp32_url,
                'esp32_status_code': result.get('status_code'),
                'esp32_response': result.get('response'),
            },
            start_time=start_time,
        )

    http_status = result.get('status_code') or 502
    if http_status < 400:
        http_status = 502
    if http_status > 599:
        http_status = 502

    return error_response(
        message=result['message'],
        status_code=http_status,
        error_code='ESP32_FORWARD_FAILED',
        start_time=start_time,
    )
