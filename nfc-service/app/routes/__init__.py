"""
Rutas HTTP del microservicio NFC + puente ESP32
"""

from .nfc_routes import nfc_bp
from .esp32_routes import esp32_bp

__all__ = ['nfc_bp', 'esp32_bp']
