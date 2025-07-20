 
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class NFCClientService:
    """Cliente para comunicarse con microservicio NFC"""
    
    def __init__(self, nfc_base_url: str = "http://localhost:5001"):
        self.nfc_base_url = nfc_base_url
        self.logger = logger
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del lector NFC"""
        try:
            response = requests.get(f"{self.nfc_base_url}/status", timeout=5)
            if response.status_code == 200:
                return {
                    "connected": response.json()["data"]["reader_status"]["connected"],
                    "reader_info": response.json()["data"]["reader_info"],
                    "error": None
                }
            else:
                return {"connected": False, "reader_info": None, "error": "Servicio NFC no disponible"}
        except Exception as e:
            self.logger.error(f"Error conectando con servicio NFC: {e}")
            return {"connected": False, "reader_info": None, "error": str(e)}
    
    def wait_for_card(self, timeout: int = 10) -> Dict[str, Any]:
        """Esperar tarjeta NFC con timeout"""
        try:
            response = requests.post(
                f"{self.nfc_base_url}/wait-for-card", 
                json={"timeout": timeout}, 
                timeout=timeout + 5
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "uid": data["data"]["uid"],
                    "timeout": False,
                    "error": None,
                    "logs": data.get("logs", [])
                }
            else:
                return {
                    "success": False,
                    "uid": None,
                    "timeout": True,
                    "error": "Timeout o tarjeta no detectada",
                    "logs": []
                }
        except Exception as e:
            self.logger.error(f"Error leyendo tarjeta NFC: {e}")
            return {
                "success": False,
                "uid": None,
                "timeout": False,
                "error": str(e),
                "logs": []
            }