"""
NFC Manager - Clase principal para manejo del lector ACR122U
Proporciona funcionalidad completa para leer tarjetas NFC/RFID
"""

import logging
import time
from smartcard.System import readers
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException
from threading import Event, Thread

from app.config import Config
from app.exceptions.nfc_exceptions import (
    NFCReaderNotFound, NFCCardNotDetected, NFCTimeout,
    NFCConnectionError, NFCReadError, NFCMultipleReadersError
)

class NFCManager:
    """Gestor principal para operaciones NFC con ACR122U"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.reader = None
        self.connection = None
        self._card_detected_event = Event()
        self._last_detected_uid = None
        
    def get_reader_status(self):
        """
        Obtener estado del lector ACR122U
        
        Returns:
            dict: Estado detallado del lector
        """
        self.logger.info("🔍 Verificando estado del lector ACR122U...")
        
        try:
            available_readers = readers()
            
            if not available_readers:
                self.logger.warning("⚠️ No se encontraron lectores NFC conectados")
                return {
                    "connected": False,
                    "reader_count": 0,
                    "readers": [],
                    "active_reader": None
                }
            
            # Filtrar lectores ACR122U
            acr_readers = [r for r in available_readers if Config.READER_NAME_PATTERN in str(r)]
            
            if not acr_readers:
                self.logger.warning(f"⚠️ No se encontraron lectores {Config.READER_NAME_PATTERN}")
                return {
                    "connected": False,
                    "reader_count": len(available_readers),
                    "readers": [str(r) for r in available_readers],
                    "active_reader": None
                }
            
            # Usar el primer lector ACR122U encontrado
            self.reader = acr_readers[0]
            self.logger.info(f"✅ Lector ACR122U encontrado: {self.reader}")
            
            return {
                "connected": True,
                "reader_count": len(acr_readers),
                "readers": [str(r) for r in acr_readers],
                "active_reader": str(self.reader),
                "all_readers": [str(r) for r in available_readers]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error verificando lector: {str(e)}")
            raise NFCConnectionError(f"Error verificando lector: {str(e)}")
    
    def is_reader_connected(self):
        """Verificar si el lector está conectado"""
        try:
            status = self.get_reader_status()
            return status["connected"]
        except:
            return False
    
    def read_card_uid(self):
        """
        Leer UID de tarjeta NFC inmediatamente
        
        Returns:
            str: UID de la tarjeta en formato hexadecimal
        """
        self.logger.info("📖 Intentando leer UID de tarjeta NFC...")
        
        if not self.reader:
            raise NFCReaderNotFound()
        
        try:
            # Conectar al lector
            self.connection = self.reader.createConnection()
            self.connection.connect()
            self.logger.info("🔗 Conexión establecida con el lector")
            
            # Comando APDU para obtener UID
            # Este es un comando estándar para ISO14443-A
            get_uid_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            
            response, sw1, sw2 = self.connection.transmit(get_uid_command)
            
            if sw1 == 0x90 and sw2 == 0x00:
                uid = toHexString(response).replace(' ', '')
                self.logger.info(f"✅ UID leído exitosamente: {uid}")
                return uid
            else:
                error_msg = f"Error en respuesta APDU: SW1={sw1:02X}, SW2={sw2:02X}"
                self.logger.error(f"❌ {error_msg}")
                raise NFCReadError(error_msg)
                
        except NoCardException:
            self.logger.warning("⚠️ No hay tarjeta presente en el lector")
            raise NFCCardNotDetected()
        except CardConnectionException as e:
            self.logger.error(f"❌ Error de conexión con tarjeta: {str(e)}")
            raise NFCConnectionError(f"Error conectando con tarjeta: {str(e)}")
        except Exception as e:
            self.logger.error(f"❌ Error inesperado leyendo UID: {str(e)}")
            raise NFCReadError(f"Error leyendo UID: {str(e)}")
        finally:
            if self.connection:
                try:
                    self.connection.disconnect()
                    self.logger.debug("🔌 Conexión desconectada")
                except:
                    pass
    
    def wait_for_card(self, timeout=None):
        """
        Esperar hasta que una tarjeta sea detectada
        
        Args:
            timeout (int): Tiempo máximo de espera en segundos
            
        Returns:
            dict: Información de la tarjeta detectada
        """
        if timeout is None:
            timeout = Config.NFC_TIMEOUT
            
        self.logger.info(f"⏳ Esperando tarjeta NFC por {timeout} segundos...")
        
        if not self.reader:
            raise NFCReaderNotFound()
        
        start_time = time.time()
        retry_count = 0
        max_retries = Config.NFC_RETRY_ATTEMPTS
        
        while time.time() - start_time < timeout:
            try:
                uid = self.read_card_uid()
                detection_time = round(time.time() - start_time, 2)
                
                self.logger.info(f"🎯 Tarjeta detectada en {detection_time}s: {uid}")
                
                return {
                    "uid": uid,
                    "detection_time": detection_time,
                    "reader": str(self.reader),
                    "retry_count": retry_count
                }
                
            except NFCCardNotDetected:
                # Continuar esperando
                retry_count += 1
                time.sleep(0.5)  # Pequeña pausa entre intentos
                
            except Exception as e:
                # Para otros errores, reintentar hasta el máximo
                retry_count += 1
                if retry_count >= max_retries:
                    self.logger.error(f"❌ Máximo de reintentos alcanzado: {str(e)}")
                    raise
                
                self.logger.warning(f"⚠️ Reintento {retry_count}/{max_retries}: {str(e)}")
                time.sleep(1)
        
        # Timeout alcanzado
        elapsed_time = round(time.time() - start_time, 2)
        self.logger.warning(f"⏰ Timeout después de {elapsed_time}s esperando tarjeta")
        raise NFCTimeout(f"No se detectó tarjeta en {timeout} segundos", timeout)
    
    def initialize_reader(self):
        """
        Intentar conectar específicamente al ACR122U
        
        Returns:
            dict: Resultado de la inicialización
        """
        self.logger.info("🔧 Inicializando conexión con lector ACR122U...")
        
        try:
            # Obtener estado actual
            status = self.get_reader_status()
            
            if not status["connected"]:
                self.logger.warning("⚠️ No hay lectores ACR122U disponibles")
                return {
                    "initialized": False,
                    "error": "No ACR122U readers found",
                    "available_readers": status["readers"]
                }
            
            # Intentar conexión de prueba
            test_result = self.test_reader_communication()
            
            if test_result["success"]:
                self.logger.info("✅ Lector ACR122U inicializado correctamente")
                return {
                    "initialized": True,
                    "reader": str(self.reader),
                    "communication_test": test_result
                }
            else:
                self.logger.error("❌ Fallo en comunicación con lector")
                return {
                    "initialized": False,
                    "error": "Communication test failed",
                    "details": test_result
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error inicializando lector: {str(e)}")
            return {
                "initialized": False,
                "error": str(e),
                "troubleshooting": [
                    "Verificar que el driver PC/SC esté instalado",
                    "Comprobar que el lector esté conectado via USB",
                    "Reiniciar el servicio de PC/SC",
                    "Verificar permisos de usuario"
                ]
            }
    
    def test_reader_communication(self):
        """
        Probar comunicación básica con el lector
        
        Returns:
            dict: Resultado de la prueba
        """
        self.logger.info("🧪 Probando comunicación con lector...")
        
        if not self.reader:
            return {
                "success": False,
                "error": "No reader available",
                "test_performed": "connection_check"
            }
        
        try:
            # Intentar crear conexión
            connection = self.reader.createConnection()
            connection.connect()
            
            # Comando básico de prueba - Get Data
            test_command = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            response, sw1, sw2 = connection.transmit(test_command)
            
            connection.disconnect()
            
            # Evaluar respuesta
            if sw1 == 0x90 or sw1 == 0x63:  # 0x63 = No card, pero lector funciona
                self.logger.info("✅ Comunicación con lector exitosa")
                return {
                    "success": True,
                    "reader_response": f"SW1: {sw1:02X}, SW2: {sw2:02X}",
                    "status": "Reader responding correctly",
                    "test_performed": "apdu_command"
                }
            else:
                self.logger.warning(f"⚠️ Respuesta inesperada del lector: SW1={sw1:02X}, SW2={sw2:02X}")
                return {
                    "success": False,
                    "reader_response": f"SW1: {sw1:02X}, SW2: {sw2:02X}",
                    "status": "Unexpected response",
                    "test_performed": "apdu_command"
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error en prueba de comunicación: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "test_performed": "connection_attempt",
                "troubleshooting": [
                    "Verificar conexión USB del lector",
                    "Comprobar drivers PC/SC",
                    "Reiniciar lector físicamente"
                ]
            }
    
    def reset_reader_connection(self):
        """
        Reiniciar conexión del lector
        
        Returns:
            dict: Resultado del reset
        """
        self.logger.info("🔄 Reiniciando conexión del lector...")
        
        try:
            # Limpiar conexión actual
            if self.connection:
                try:
                    self.connection.disconnect()
                except:
                    pass
                self.connection = None
            
            self.reader = None
            self.logger.info("🧹 Conexión anterior limpiada")
            
            # Reinicializar
            time.sleep(1)  # Pequeña pausa
            init_result = self.initialize_reader()
            
            if init_result["initialized"]:
                self.logger.info("✅ Reconexión exitosa")
                return {
                    "reset_successful": True,
                    "new_connection": init_result
                }
            else:
                self.logger.warning("⚠️ Reconexión falló")
                return {
                    "reset_successful": False,
                    "error": init_result.get("error", "Unknown error")
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error reiniciando conexión: {str(e)}")
            return {
                "reset_successful": False,
                "error": str(e)
            }
    
    def get_detailed_reader_info(self):
        """Obtener información detallada del hardware"""
        self.logger.info("📋 Obteniendo información detallada del lector...")
        
        try:
            import smartcard
            available_readers = readers()
            
            info = {
                "pyscard_version": getattr(smartcard, '__version__', 'Unknown'),
                "total_readers": len(available_readers),
                "readers_detail": [],
                "acr122u_readers": [],
                "active_reader": None,
                "driver_status": "unknown"
            }
            
            # Información detallada de cada lector
            for i, reader in enumerate(available_readers):
                reader_info = {
                    "index": i,
                    "name": str(reader),
                    "is_acr122u": Config.READER_NAME_PATTERN in str(reader),
                    "connection_status": "unknown"
                }
                
                # Probar conexión
                try:
                    conn = reader.createConnection()
                    conn.connect()
                    reader_info["connection_status"] = "connectable"
                    conn.disconnect()
                except Exception as e:
                    reader_info["connection_status"] = f"error: {str(e)}"
                
                info["readers_detail"].append(reader_info)
                
                if reader_info["is_acr122u"]:
                    info["acr122u_readers"].append(reader_info)
            
            # Determinar lector activo
            if self.reader:
                info["active_reader"] = {
                    "name": str(self.reader),
                    "status": "active"
                }
            
            # Estado del driver (simplificado)
            if len(available_readers) > 0:
                info["driver_status"] = "installed"
            else:
                info["driver_status"] = "not_installed_or_no_readers"
            
            self.logger.info(f"📊 Información recopilada: {len(available_readers)} lectores encontrados")
            return info
            
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo información detallada: {str(e)}")
            return {
                "error": str(e),
                "pyscard_version": "unknown",
                "driver_status": "error"
            }
    
    def get_reader_info(self):
        """Obtener información básica del lector"""
        if not self.reader:
            return None
            
        return {
            "name": str(self.reader),
            "type": "ACR122U",
            "status": "connected" if self.is_reader_connected() else "disconnected"
        }
