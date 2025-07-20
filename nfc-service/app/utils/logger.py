"""
Sistema de logging personalizado con colores
Proporciona logs tanto en consola como para incluir en responses
"""

import logging
import colorama
from colorama import Fore, Style
from datetime import datetime
import threading

# Inicializar colorama para Windows
colorama.init(autoreset=True)

# Buffer thread-safe para logs
class LogBuffer:
    """Buffer thread-safe para almacenar logs recientes"""
    
    def __init__(self, max_size=100):
        self._logs = []
        self._lock = threading.Lock()
        self._max_size = max_size
    
    def add_log(self, message):
        """Agregar log al buffer"""
        with self._lock:
            timestamp = datetime.now().isoformat()
            self._logs.append(f"[{timestamp}] {message}")
            if len(self._logs) > self._max_size:
                self._logs.pop(0)
    
    def get_recent_logs(self, count=10):
        """Obtener logs recientes"""
        with self._lock:
            return self._logs[-count:] if self._logs else []
    
    def clear(self):
        """Limpiar buffer"""
        with self._lock:
            self._logs.clear()

# Buffer global para logs
log_buffer = LogBuffer()

class ColoredFormatter(logging.Formatter):
    """Formatter personalizado con colores"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT
    }
    
    def format(self, record):
        # Agregar al buffer
        message = super().format(record)
        log_buffer.add_log(f"{record.levelname} - {record.getMessage()}")
        
        # Colorear para consola
        color = self.COLORS.get(record.levelname, '')
        colored_levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        
        # Formato personalizado
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"[{timestamp}] [{colored_levelname}] [{record.name}] - {record.getMessage()}"
        
        return formatted

def setup_logging():
    """Configurar el sistema de logging"""
    from app.config import Config
    
    # Configurar nivel de log
    level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    
    # Crear formatter
    formatter = ColoredFormatter()
    
    # Configurar handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Configurar logger específico del microservicio
    nfc_logger = logging.getLogger('nfc_service')
    nfc_logger.setLevel(level)
    
    return nfc_logger

def get_recent_logs(count=10):
    """Obtener logs recientes para incluir en responses"""
    return log_buffer.get_recent_logs(count)

def clear_logs():
    """Limpiar buffer de logs"""
    log_buffer.clear()
