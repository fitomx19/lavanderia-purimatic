"""
Utilidades para respuestas HTTP estandarizadas
Incluye logs y formato consistente para todas las respuestas
"""

from flask import jsonify
from datetime import datetime
from app.utils.logger import get_recent_logs
import time

def success_response(message, data=None, status_code=200, include_logs=True, start_time=None):
    """
    Crear respuesta de éxito estandarizada
    
    Args:
        message (str): Mensaje descriptivo
        data (dict): Datos adicionales
        status_code (int): Código HTTP
        include_logs (bool): Incluir logs recientes
        start_time (float): Tiempo de inicio para calcular duración
    """
    response_data = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    }
    
    # Agregar datos si existen
    if data is not None:
        response_data["data"] = data
    
    # Agregar duración si se proporciona tiempo de inicio
    if start_time is not None:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response_data["duration_ms"] = duration_ms
    
    # Incluir logs recientes si se solicita
    if include_logs:
        response_data["logs"] = get_recent_logs(5)
    
    return jsonify(response_data), status_code

def error_response(message, status_code=400, error_code=None, include_logs=True, start_time=None):
    """
    Crear respuesta de error estandarizada
    
    Args:
        message (str): Mensaje de error
        status_code (int): Código HTTP de error
        error_code (str): Código específico de error
        include_logs (bool): Incluir logs recientes
        start_time (float): Tiempo de inicio para calcular duración
    """
    response_data = {
        "success": False,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "status_code": status_code
    }
    
    # Agregar código de error si existe
    if error_code:
        response_data["error_code"] = error_code
    
    # Agregar duración si se proporciona tiempo de inicio
    if start_time is not None:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        response_data["duration_ms"] = duration_ms
    
    # Incluir logs recientes si se solicita
    if include_logs:
        response_data["logs"] = get_recent_logs(5)
    
    return jsonify(response_data), status_code

def service_unavailable_response(message="Servicio NFC no disponible", include_logs=True):
    """Respuesta específica para cuando el servicio NFC no está disponible"""
    return error_response(
        message=message,
        status_code=503,
        error_code="SERVICE_UNAVAILABLE",
        include_logs=include_logs
    )
