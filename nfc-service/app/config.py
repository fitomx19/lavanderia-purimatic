"""
Configuración del microservicio NFC + puente ESP32
Maneja variables de entorno y constantes del sistema
"""

import os
import sys
from dotenv import load_dotenv


def _load_env():
    """
    Cargar .env junto al .exe (tienda) o junto al código (desarrollo).
    Si el puente está en una subcarpeta, también busca el .env del padre
    (el mismo que usa Purimatic.exe).
    """
    candidates = []
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, '.env'))
        candidates.append(os.path.join(os.path.dirname(exe_dir), '.env'))
    else:
        service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(service_dir, '.env'))
        candidates.append(os.path.join(os.path.dirname(service_dir), '.env'))

    for path in candidates:
        if os.path.exists(path):
            load_dotenv(dotenv_path=path)
            return
    load_dotenv()


_load_env()

class Config:
    """Configuración principal del microservicio"""
    
    # Configuración Flask
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))
    _frozen = getattr(sys, 'frozen', False)
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False' if _frozen else 'True').lower() == 'true'
    
    # Configuración Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configuración NFC
    NFC_TIMEOUT = int(os.getenv('NFC_TIMEOUT', 10))
    NFC_RETRY_ATTEMPTS = int(os.getenv('NFC_RETRY_ATTEMPTS', 3))
    
    # Configuración del lector ACR122U
    READER_NAME_PATTERN = "ACR122"  # Coincide con "ACS ACR122 0", "ACR122U", etc.

    # Tiempo máximo para el POST a la placa ESP32 física
    ESP32_TIMEOUT = int(os.getenv('ESP32_TIMEOUT', 10))
    
    @classmethod
    def get_summary(cls):
        """Obtener resumen de configuración para logs"""
        return {
            "flask_port": cls.FLASK_PORT,
            "debug_mode": cls.FLASK_DEBUG,
            "log_level": cls.LOG_LEVEL,
            "nfc_timeout": cls.NFC_TIMEOUT,
            "retry_attempts": cls.NFC_RETRY_ATTEMPTS,
            "esp32_timeout": cls.ESP32_TIMEOUT,
        }
