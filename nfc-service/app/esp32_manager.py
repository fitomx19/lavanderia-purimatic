"""
Puente HTTP hacia las placas ESP32 físicas.

La API principal no habla directo con la placa: este módulo recibe
esp32_url + laundry_data y hace el POST a /laundry-update de esa máquina.
"""

import logging
from typing import Any, Dict

import requests

from app.config import Config

logger = logging.getLogger(__name__)


class ESP32Manager:
    """Envía comandos de lavandería al ESP32 de la red local de la tienda."""

    def __init__(self):
        self.timeout = Config.ESP32_TIMEOUT

    def send_laundry_update(self, esp32_url: str, laundry_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        POST al endpoint de la placa (típicamente http://IP/laundry-update).

        Returns:
            dict: {success, message, status_code, response}
        """
        url = (esp32_url or '').strip()
        if not url:
            return {
                'success': False,
                'message': 'esp32_url es requerida',
                'status_code': 400,
                'response': None,
            }

        if not laundry_data or not isinstance(laundry_data, dict):
            return {
                'success': False,
                'message': 'laundry_data debe ser un objeto JSON',
                'status_code': 400,
                'response': None,
            }

        logger.info(f"Enviando comando al ESP32: {url}")

        try:
            response = requests.post(
                url,
                json=laundry_data,
                timeout=self.timeout,
            )
            body = None
            try:
                body = response.json()
            except ValueError:
                body = {'raw': response.text}

            if 200 <= response.status_code < 300:
                logger.info(f"ESP32 respondió {response.status_code} en {url}")
                return {
                    'success': True,
                    'message': 'Comando enviado al ESP32',
                    'status_code': response.status_code,
                    'response': body,
                }

            logger.warning(f"ESP32 respondió error {response.status_code} en {url}")
            return {
                'success': False,
                'message': f'El ESP32 respondió HTTP {response.status_code}',
                'status_code': response.status_code,
                'response': body,
            }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout al contactar ESP32: {url}")
            return {
                'success': False,
                'message': f'Timeout al contactar {url} (la placa no respondió en {self.timeout}s)',
                'status_code': 504,
                'response': None,
            }
        except requests.exceptions.ConnectionError as exc:
            logger.error(f"No se pudo conectar al ESP32 {url}: {exc}")
            return {
                'success': False,
                'message': (
                    f'No se pudo conectar a {url}. '
                    'Revisa que la placa esté en la misma red WiFi de esta máquina '
                    'y que la IP de esp32_config sea la correcta.'
                ),
                'status_code': 502,
                'response': None,
            }
        except Exception as exc:
            logger.error(f"Error enviando comando al ESP32 {url}: {exc}")
            return {
                'success': False,
                'message': f'Error de comunicación con el ESP32: {exc}',
                'status_code': 500,
                'response': None,
            }
