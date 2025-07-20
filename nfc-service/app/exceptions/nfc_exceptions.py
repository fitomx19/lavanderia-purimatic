"""
Excepciones personalizadas para operaciones NFC
Define errores específicos del lector ACR122U y operaciones de tarjetas
"""

class NFCBaseException(Exception):
    """Excepción base para errores NFC"""
    
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)

class NFCReaderNotFound(NFCBaseException):
    """Error cuando no se encuentra el lector ACR122U"""
    
    def __init__(self, message="Lector ACR122U no encontrado o desconectado"):
        super().__init__(message, "READER_NOT_FOUND")

class NFCCardNotDetected(NFCBaseException):
    """Error cuando no se detecta ninguna tarjeta NFC"""
    
    def __init__(self, message="No se detectó ninguna tarjeta NFC en el lector"):
        super().__init__(message, "CARD_NOT_DETECTED")

class NFCTimeout(NFCBaseException):
    """Error por timeout en operaciones NFC"""
    
    def __init__(self, message="Timeout en operación NFC", timeout_seconds=None):
        if timeout_seconds:
            message = f"Timeout después de {timeout_seconds} segundos"
        super().__init__(message, "NFC_TIMEOUT")
        self.timeout_seconds = timeout_seconds

class NFCConnectionError(NFCBaseException):
    """Error de conexión con el lector NFC"""
    
    def __init__(self, message="Error de conexión con el lector NFC"):
        super().__init__(message, "CONNECTION_ERROR")

class NFCReadError(NFCBaseException):
    """Error al leer datos de la tarjeta NFC"""
    
    def __init__(self, message="Error al leer datos de la tarjeta NFC"):
        super().__init__(message, "READ_ERROR")

class NFCMultipleReadersError(NFCBaseException):
    """Error cuando hay múltiples lectores conectados"""
    
    def __init__(self, message="Múltiples lectores NFC detectados", reader_count=None):
        if reader_count:
            message = f"Se detectaron {reader_count} lectores NFC"
        super().__init__(message, "MULTIPLE_READERS")
        self.reader_count = reader_count
