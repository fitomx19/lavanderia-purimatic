"""
Rutas HTTP para el microservicio NFC
Define todos los endpoints para operaciones con lector ACR122U
"""

import logging
import time
from flask import Blueprint, request, jsonify

from app.nfc_manager import NFCManager
from app.utils.response_utils import success_response, error_response
from app.exceptions.nfc_exceptions import (
    NFCReaderNotFound, NFCCardNotDetected, NFCTimeout,
    NFCConnectionError, NFCReadError
)
from app.config import Config

# Crear blueprint para rutas NFC
nfc_bp = Blueprint('nfc', __name__)

# Instancia global del NFC Manager
nfc_manager = NFCManager()
logger = logging.getLogger(__name__)

@nfc_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de health check básico"""
    start_time = time.time()
    logger.info("🏥 Health check solicitado")
    
    return success_response(
        message="Microservicio NFC funcionando correctamente",
        data={
            "service": "nfc-service",
            "version": "1.0.0",
            "status": "healthy"
        },
        start_time=start_time
    )

@nfc_bp.route('/status', methods=['GET'])
def get_status():
    """Obtener estado completo del lector y servicio"""
    start_time = time.time()
    logger.info("📊 Estado del servicio solicitado")
    
    try:
        # Obtener estado del lector
        reader_status = nfc_manager.get_reader_status()
        reader_info = nfc_manager.get_reader_info()
        
        # Obtener configuración del servicio
        config_summary = Config.get_summary()
        
        # Obtener información adicional de troubleshooting
        detailed_info = nfc_manager.get_detailed_reader_info()
        
        # Generar estado de conexión mejorado
        connection_status = "unknown"
        troubleshooting = []
        
        if reader_status["connected"]:
            # Probar comunicación si hay lector conectado
            try:
                comm_test = nfc_manager.test_reader_communication()
                if comm_test["success"]:
                    connection_status = "fully_operational"
                else:
                    connection_status = "detected_but_not_communicating"
                    troubleshooting.extend([
                        "🔧 Verificar que ninguna otra aplicación esté usando el lector",
                        "🔄 Usar endpoint POST /reset-reader para reiniciar conexión",
                        "🧪 Usar endpoint POST /test-connection para pruebas"
                    ])
            except:
                connection_status = "detected_but_communication_error"
                troubleshooting.append("❌ Error al probar comunicación con lector")
        else:
            connection_status = "no_readers_detected"
            troubleshooting.extend([
                "🔌 Conectar lector ACR122U via USB",
                "🔧 Verificar instalación de drivers PC/SC",
                "🔍 Usar endpoint GET /diagnostics para análisis completo"
            ])
        
        data = {
            "service_status": "running",
            "connection_status": connection_status,
            "reader_status": reader_status,
            "reader_info": reader_info,
            "hardware_summary": {
                "total_readers": detailed_info.get("total_readers", 0),
                "acr122u_count": len(detailed_info.get("acr122u_readers", [])),
                "driver_status": detailed_info.get("driver_status", "unknown"),
                "pyscard_version": detailed_info.get("pyscard_version", "unknown")
            },
            "configuration": config_summary,
            "capabilities": [
                "read_card_uid",
                "wait_for_card", 
                "reader_status_check",
                "hardware_initialization",
                "connection_testing",
                "full_diagnostics"
            ],
            "troubleshooting": troubleshooting,
            "last_error": None,
            "connection_attempts": 0
        }
        
        # Determinar mensaje principal
        if connection_status == "fully_operational":
            message = "Servicio NFC completamente operativo"
        elif connection_status == "detected_but_not_communicating":
            message = "Lector detectado pero con problemas de comunicación"
        elif connection_status == "no_readers_detected":
            message = "Servicio activo - No se detectaron lectores ACR122U"
        else:
            message = "Servicio NFC funcionando - Estado de conexión desconocido"
        
        return success_response(
            message=message,
            data=data,
            start_time=start_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo estado: {str(e)}")
        return error_response(
            message=f"Error obteniendo estado del servicio: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/read-card', methods=['POST'])
def read_card():
    """Leer UID de tarjeta NFC inmediatamente"""
    start_time = time.time()
    logger.info("🔍 Lectura inmediata de tarjeta solicitada")
    
    try:
        # Verificar estado del lector primero
        if not nfc_manager.is_reader_connected():
            logger.warning("⚠️ Intento de lectura sin lector conectado")
            return error_response(
                message="Lector ACR122U no conectado",
                status_code=503,
                error_code="SERVICE_UNAVAILABLE",
                start_time=start_time
            )
        
        # Leer UID de la tarjeta
        uid = nfc_manager.read_card_uid()
        reader_info = nfc_manager.get_reader_info()
        
        data = {
            "uid": uid,
            "uid_length": len(uid),
            "format": "hexadecimal",
            "reader_info": reader_info
        }
        
        return success_response(
            message=f"Tarjeta NFC leída exitosamente: {uid}",
            data=data,
            start_time=start_time
        )
        
    except NFCCardNotDetected as e:
        return error_response(
            message=str(e),
            status_code=404,
            error_code=e.error_code,
            start_time=start_time
        )
    except NFCReaderNotFound as e:
        return error_response(
            message=str(e),
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            start_time=start_time
        )
    except (NFCConnectionError, NFCReadError) as e:
        return error_response(
            message=str(e),
            status_code=500,
            error_code=e.error_code,
            start_time=start_time
        )
    except Exception as e:
        logger.error(f"❌ Error inesperado en read-card: {str(e)}")
        return error_response(
            message=f"Error inesperado: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/wait-for-card', methods=['POST'])
def wait_for_card():
    """Esperar hasta que una tarjeta sea detectada"""
    start_time = time.time()
    logger.info("⏳ Espera de tarjeta solicitada")
    
    try:
        # Obtener parámetros de la request
        data = request.get_json() or {}
        timeout = data.get('timeout', Config.NFC_TIMEOUT)
        
        # Validar timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return error_response(
                "Timeout debe ser un número positivo",
                status_code=400,
                start_time=start_time
            )
        
        if timeout > 60:  # Máximo 60 segundos
            return error_response(
                "Timeout máximo permitido es 60 segundos",
                status_code=400,
                start_time=start_time
            )
        
        # Verificar estado del lector
        if not nfc_manager.is_reader_connected():
            logger.warning("⚠️ Intento de espera sin lector conectado")
            return error_response(
                message="Lector ACR122U no conectado",
                status_code=503,
                error_code="SERVICE_UNAVAILABLE",
                start_time=start_time
            )
        
        # Esperar por la tarjeta
        logger.info(f"⏰ Iniciando espera por tarjeta (timeout: {timeout}s)")
        card_info = nfc_manager.wait_for_card(timeout)
        
        data = {
            "card_detected": True,
            "uid": card_info["uid"],
            "detection_time": card_info["detection_time"],
            "timeout_used": timeout,
            "retry_count": card_info["retry_count"],
            "reader": card_info["reader"]
        }
        
        return success_response(
            message=f"Tarjeta detectada en {card_info['detection_time']}s: {card_info['uid']}",
            data=data,
            start_time=start_time
        )
        
    except NFCTimeout as e:
        return error_response(
            message=str(e),
            status_code=408,  # Request Timeout
            error_code=e.error_code,
            start_time=start_time
        )
    except NFCReaderNotFound as e:
        return error_response(
            message=str(e),
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            start_time=start_time
        )
    except (NFCConnectionError, NFCReadError) as e:
        return error_response(
            message=str(e),
            status_code=500,
            error_code=e.error_code,
            start_time=start_time
        )
    except Exception as e:
        logger.error(f"❌ Error inesperado en wait-for-card: {str(e)}")
        return error_response(
            message=f"Error inesperado: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/initialize', methods=['POST'])
def initialize_reader():
    """Forzar inicialización del lector ACR122U"""
    start_time = time.time()
    logger.info("🔧 Inicialización del lector solicitada")
    
    try:
        # Intentar inicializar el lector
        init_result = nfc_manager.initialize_reader()
        
        if init_result["initialized"]:
            return success_response(
                message="Lector ACR122U inicializado correctamente",
                data=init_result,
                start_time=start_time
            )
        else:
            return error_response(
                message=f"Error inicializando lector: {init_result.get('error', 'Unknown error')}",
                status_code=503,
                error_code="INITIALIZATION_FAILED",
                start_time=start_time
            )
            
    except Exception as e:
        logger.error(f"❌ Error inesperado en initialize: {str(e)}")
        return error_response(
            message=f"Error inesperado durante inicialización: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Probar comunicación con el hardware"""
    start_time = time.time()
    logger.info("🧪 Prueba de conexión solicitada")
    
    try:
        # Verificar si hay lector disponible
        if not nfc_manager.is_reader_connected():
            return error_response(
                message="No hay lector ACR122U conectado para probar",
                status_code=503,
                error_code="NO_READER_AVAILABLE",
                start_time=start_time
            )
        
        # Realizar prueba de comunicación
        test_result = nfc_manager.test_reader_communication()
        
        if test_result["success"]:
            return success_response(
                message="Comunicación con lector exitosa",
                data=test_result,
                start_time=start_time
            )
        else:
            return error_response(
                message=f"Fallo en comunicación: {test_result.get('error', 'Communication failed')}",
                status_code=503,
                error_code="COMMUNICATION_FAILED",
                start_time=start_time
            )
            
    except Exception as e:
        logger.error(f"❌ Error inesperado en test-connection: {str(e)}")
        return error_response(
            message=f"Error inesperado durante prueba: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/reset-reader', methods=['POST'])
def reset_reader():
    """Reiniciar conexión del lector"""
    start_time = time.time()
    logger.info("🔄 Reset del lector solicitado")
    
    try:
        # Reiniciar conexión
        reset_result = nfc_manager.reset_reader_connection()
        
        if reset_result["reset_successful"]:
            return success_response(
                message="Lector reiniciado correctamente",
                data=reset_result,
                start_time=start_time
            )
        else:
            return error_response(
                message=f"Error reiniciando lector: {reset_result.get('error', 'Reset failed')}",
                status_code=503,
                error_code="RESET_FAILED",
                start_time=start_time
            )
            
    except Exception as e:
        logger.error(f"❌ Error inesperado en reset-reader: {str(e)}")
        return error_response(
            message=f"Error inesperado durante reset: {str(e)}",
            status_code=500,
            start_time=start_time
        )

@nfc_bp.route('/diagnostics', methods=['GET'])
def get_diagnostics():
    """Información completa del sistema y diagnóstico"""
    start_time = time.time()
    logger.info("🔍 Diagnóstico del sistema solicitado")
    
    try:
        # Obtener información detallada
        detailed_info = nfc_manager.get_detailed_reader_info()
        reader_status = nfc_manager.get_reader_status()
        config_summary = Config.get_summary()
        
        # Generar recomendaciones de troubleshooting
        troubleshooting = []
        
        if detailed_info.get("driver_status") == "not_installed_or_no_readers":
            troubleshooting.extend([
                "🔧 Instalar drivers PC/SC para el sistema",
                "🔌 Conectar lector ACR122U via USB",
                "🔄 Reiniciar servicio PC/SC del sistema"
            ])
        
        if detailed_info.get("total_readers", 0) > 0 and len(detailed_info.get("acr122u_readers", [])) == 0:
            troubleshooting.append("⚠️ Se detectaron lectores pero ninguno es ACR122U")
        
        if len(detailed_info.get("acr122u_readers", [])) > 0:
            # Verificar estado de conexión de lectores ACR122U
            connectable_readers = [r for r in detailed_info.get("acr122u_readers", []) 
                                 if r.get("connection_status") == "connectable"]
            if not connectable_readers:
                troubleshooting.extend([
                    "🔧 Verificar que ninguna otra aplicación esté usando el lector",
                    "🔄 Desconectar y reconectar el lector USB",
                    "👤 Verificar permisos de usuario para acceder al hardware"
                ])
        
        if not troubleshooting:
            troubleshooting.append("✅ Sistema parece estar configurado correctamente")
        
        # Determinar estado general del sistema
        system_health = "unknown"
        if detailed_info.get("driver_status") == "installed" and len(detailed_info.get("acr122u_readers", [])) > 0:
            connectable_count = len([r for r in detailed_info.get("acr122u_readers", []) 
                                   if r.get("connection_status") == "connectable"])
            if connectable_count > 0:
                system_health = "healthy"
            else:
                system_health = "readers_found_but_not_connectable"
        else:
            system_health = "no_readers_or_drivers"
        
        data = {
            "system_health": system_health,
            "hardware_info": detailed_info,
            "reader_status": reader_status,
            "service_config": config_summary,
            "troubleshooting": troubleshooting,
            "recommendations": {
                "windows": [
                    "Verificar 'sc query SCardSvr' en cmd",
                    "Reinstalar drivers desde Windows Update"
                ],
                "linux": [
                    "sudo systemctl status pcscd",
                    "sudo apt-get install pcscd pcsc-tools"
                ],
                "general": [
                    "Probar con endpoint POST /initialize",
                    "Verificar conexión USB del lector",
                    "Reiniciar el microservicio"
                ]
            }
        }
        
        return success_response(
            message=f"Diagnóstico completo - Estado: {system_health}",
            data=data,
            start_time=start_time
        )
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo diagnóstico: {str(e)}")
        return error_response(
            message=f"Error generando diagnóstico: {str(e)}",
            status_code=500,
            start_time=start_time
        )
