"""
Excepciones personalizadas para operaciones NFC
"""

from .nfc_exceptions import (
    NFCBaseException,
    NFCReaderNotFound,
    NFCCardNotDetected,
    NFCTimeout,
    NFCConnectionError,
    NFCReadError,
    NFCMultipleReadersError
)

__all__ = [
    'NFCBaseException',
    'NFCReaderNotFound',
    'NFCCardNotDetected',
    'NFCTimeout',
    'NFCConnectionError',
    'NFCReadError',
    'NFCMultipleReadersError'
]
