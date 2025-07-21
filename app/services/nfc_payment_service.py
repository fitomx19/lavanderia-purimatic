# CREAR NUEVO ARCHIVO: app/services/nfc_payment_service.py

from typing import Dict, Any
from app.services.nfc_client_service import NFCClientService
from app.repositories.card_repository import CardRepository
import logging

logger = logging.getLogger(__name__)

class NFCPaymentService:
    """
    Servicio para manejar pagos con tarjetas NFC
    """
    
    def __init__(self):
        self.nfc_client = NFCClientService()
        self.card_repository = CardRepository()
    
    def validate_payment_with_nfc(self, amount: float, timeout: int = 30) -> Dict[str, Any]:
        """
        Esperar tarjeta NFC y validar para pago
        
        Args:
            amount: Monto del pago a validar
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Dict: Resultado de la validación
        """
        try:
            # Verificar estado del lector NFC
            status = self.nfc_client.get_status()
            if not status.get('connected', False):
                return {
                    'success': False,
                    'message': 'Lector NFC no disponible',
                    'error_type': 'nfc_unavailable'
                }
            
            # Esperar detección de tarjeta
            read_result = self.nfc_client.wait_for_card(timeout=timeout)
            
            if not read_result.get('success', False):
                return {
                    'success': False,
                    'message': read_result.get('message', 'No se detectó tarjeta'),
                    'error_type': 'no_card_detected',
                    'logs': read_result.get('logs', [])
                }
            
            # Obtener UID de la tarjeta detectada
            nfc_uid = read_result.get('uid')
            if not nfc_uid:
                return {
                    'success': False,
                    'message': 'Error al leer UID de la tarjeta',
                    'error_type': 'read_error'
                }
            
            # Validar tarjeta para el pago
            validation_result = self.card_repository.validate_nfc_payment(nfc_uid, amount)
            
            if validation_result['valid']:
                return {
                    'success': True,
                    'message': validation_result['message'],
                    'card_data': validation_result['card_data'],
                    'nfc_uid': nfc_uid,
                    'logs': read_result.get('logs', [])
                }
            else:
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'error_type': 'validation_failed',
                    'card_data': validation_result.get('card_data'),
                    'nfc_uid': nfc_uid,
                    'logs': read_result.get('logs', [])
                }
                
        except Exception as e:
            logger.error(f"Error en validación de pago NFC: {e}")
            return {
                'success': False,
                'message': 'Error interno en validación NFC',
                'error_type': 'internal_error'
            }
    
    def process_nfc_payment(self, nfc_uid: str, amount: float) -> Dict[str, Any]:
        """
        Procesar pago NFC con UID ya validado
        
        Args:
            nfc_uid: UID de la tarjeta NFC
            amount: Monto a descontar
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            # Procesar el pago
            payment_result = self.card_repository.process_nfc_payment(nfc_uid, amount)
            
            if payment_result['success']:
                return {
                    'success': True,
                    'message': payment_result['message'],
                    'card_data': payment_result['card_data']
                }
            else:
                return {
                    'success': False,
                    'message': payment_result['message'],
                    'error_type': 'payment_failed'
                }
                
        except Exception as e:
            logger.error(f"Error procesando pago NFC: {e}")
            return {
                'success': False,
                'message': 'Error interno al procesar pago',
                'error_type': 'internal_error'
            }
    
    def get_nfc_status(self) -> Dict[str, Any]:
        """
        Obtener estado del sistema NFC
        
        Returns:
            Dict: Estado del lector NFC
        """
        return self.nfc_client.get_status()