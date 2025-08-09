import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.repositories.store_repository import StoreRepository

logger = logging.getLogger(__name__)

class ESP32Service:
    """
    Este servicio es como un 'cartero' que sabe cómo hablar 
    con el microservicio ESP32
    """
    
    def __init__(self):
        # URL del microservicio ESP32 que actúa como intermediario
        self.base_url = "http://localhost:5002"
        self.timeout = 10
        self.store_repository = StoreRepository()
    
    def start_machine(self, esp32_id: str, machine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía comando para iniciar una máquina física
        
        Args:
            esp32_id: El ID del ESP32 (ejemplo: "100", "101", etc.)
            machine_data: Información sobre qué hacer (hora inicio, fin, etc.)
        """
        try:
            # Obtener URL del ESP32 desde DB (colección esp32_config)
            esp32_url = self.store_repository.get_esp32_url_by_id("100")
            if not esp32_url:
                return {
                    'success': False,
                    'message': f'ESP32 URL no configurada para esp32_id {esp32_id}'
                }
            
            # Preparar el mensaje en el formato que espera el microservicio
            payload = {
                "esp32_url": esp32_url,
                "laundry_data": {
                    "washer_id": machine_data.get("machine_id") or esp32_id,
                    "start_time": machine_data.get("start_time"), 
                    "end_time": machine_data.get("end_time"),
                    "status": "starting"
                }
            }
            
            logger.info(f"Enviando comando de inicio a ESP32 {esp32_id}")
            
            # Enviar la petición al microservicio ESP32 (puerto 5002)
            response = requests.post(
                f"{self.base_url}/send-to-esp32",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Máquina {esp32_id} iniciada correctamente',
                    'esp32_response': response.json()
                }
            else:
                return {
                    'success': False,
                    'message': f'Error al iniciar máquina {esp32_id}: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error comunicándose con ESP32 {esp32_id}: {e}")
            return {
                'success': False,
                'message': f'Error de comunicación: {str(e)}'
            }
    
    def stop_machine(self, esp32_id: str, machine_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía comando para detener una máquina física
        """
        try:
            esp32_url = self.store_repository.get_esp32_url_by_id("100")
            if not esp32_url:
                return {
                    'success': False,
                    'message': f'ESP32 URL no configurada para esp32_id {esp32_id}'
                }
            
            payload = {
                "esp32_url": esp32_url,
                "laundry_data": {
                    "washer_id": machine_data.get("machine_id") or esp32_id,
                    "status": "finished"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/send-to-esp32",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Máquina {esp32_id} detenida correctamente'
                }
            else:
                return {
                    'success': False,
                    'message': f'Error al detener máquina {esp32_id}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error de comunicación: {str(e)}'
            }