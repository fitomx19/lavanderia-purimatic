"""
Configuración del microservicio NFC
Maneja variables de entorno y constantes del sistema
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración principal del microservicio"""
    
    # Configuración Flask
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5001))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Configuración NFC
    NFC_TIMEOUT = int(os.getenv('NFC_TIMEOUT', 10))
    NFC_RETRY_ATTEMPTS = int(os.getenv('NFC_RETRY_ATTEMPTS', 3))
    
    # Configuración del lector ACR122U
    READER_NAME_PATTERN = "ACR122"  # Coincide con "ACS ACR122 0", "ACR122U", etc.
    
    @classmethod
    def get_summary(cls):
        """Obtener resumen de configuración para logs"""
        return {
            "flask_port": cls.FLASK_PORT,
            "debug_mode": cls.FLASK_DEBUG,
            "log_level": cls.LOG_LEVEL,
            "nfc_timeout": cls.NFC_TIMEOUT,
            "retry_attempts": cls.NFC_RETRY_ATTEMPTS
        }
