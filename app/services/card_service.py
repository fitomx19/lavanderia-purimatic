from typing import Dict, Any, Optional
from app.repositories.card_repository import CardRepository
from app.repositories.user_client_repository import UserClientRepository
from app.schemas.card_schema import (
    card_schema,
    card_update_schema,
    card_balance_schema,
    card_transfer_schema,
    card_response_schema,
    cards_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class CardService:
    """
    Servicio para manejo de tarjetas recargables con lógica de negocio.
    Incluye operaciones de vinculación y recarga mediante NFC.
    """
    
    def __init__(self):
        self.card_repository = CardRepository()
        self.client_repository = UserClientRepository()
    
    def create_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear nueva tarjeta recargable
        
        Args:
            card_data: Datos de la tarjeta
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el cliente existe
            client = self.client_repository.find_by_id(card_data['client_id'])
            if not client:
                return {
                    'success': False,
                    'message': 'Cliente no encontrado'
                }
            
            # Generar número de tarjeta si no se proporciona
            if 'card_number' not in card_data:
                card_data['card_number'] = self.card_repository.generate_card_number()
            
            # Validar datos
            validated_data = card_schema.load(card_data)
            if not isinstance(validated_data, dict):
                return {
                    'success': False,
                    'message': 'Datos de entrada inválidos después de validación'
                }
            
            # Verificar que el número de tarjeta no exista
            if self.card_repository.card_number_exists(validated_data.get('card_number')):
                return {
                    'success': False,
                    'message': 'El número de tarjeta ya existe'
                }
            
            # Crear tarjeta
            card = self.card_repository.upsert(validated_data)
            
            if card:
                # Si la tarjeta tiene saldo inicial, actualizar el saldo del cliente
                card_balance = validated_data.get('balance', 0)
                if card_balance > 0:
                    # Actualizar saldo del cliente con el saldo inicial de la tarjeta
                    current_balance = client.get('saldo_tarjeta_recargable', 0) if client else 0
                    new_balance = current_balance + float(card_balance)
                    
                    # Actualizar cliente con el nuevo saldo
                    self.client_repository.update_balance(
                        card_data['client_id'],
                        new_balance,
                        'establecer'
                    )
                
                card_response = card_response_schema.dump(card)
                return {
                    'success': True,
                    'message': 'Tarjeta creada exitosamente',
                    'data': card_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al crear la tarjeta'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en tarjeta: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de tarjeta: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_client_cards(self, client_id: str) -> Dict[str, Any]:
        """
        Obtener tarjetas de un cliente
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Dict: Lista de tarjetas del cliente
        """
        try:
            # Verificar que el cliente existe
            client = self.client_repository.find_by_id(client_id)
            if not client:
                return {
                    'success': False,
                    'message': 'Cliente no encontrado'
                }
            
            cards = self.card_repository.find_by_client_id(client_id)
            cards_response = cards_response_schema.dump(cards)
            
            return {
                'success': True,
                'message': 'Tarjetas obtenidas exitosamente',
                'data': cards_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener tarjetas del cliente: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def add_balance(self, card_id: str, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agregar saldo a una tarjeta
        
        Args:
            card_id: ID de la tarjeta
            balance_data: Datos del saldo a agregar
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos
            validated_data = card_balance_schema.load(balance_data)
            
            # Verificar que la tarjeta existe
            card = self.card_repository.find_by_id(card_id)
            if not card:
                return {
                    'success': False,
                    'message': 'Tarjeta no encontrada'
                }
            
            # Actualizar saldo
            updated_card = self.card_repository.update_balance(
                card_id, 
                float(validated_data.get('amount', 0)), 
                str(validated_data.get('operation', ''))
            )
            
            if updated_card:
                card_response = card_response_schema.dump(updated_card)
                return {
                    'success': True,
                    'message': 'Saldo actualizado exitosamente',
                    'data': card_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar el saldo'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en saldo: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de saldo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def transfer_balance(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transferir saldo entre tarjetas
        
        Args:
            transfer_data: Datos de la transferencia
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos
            validated_data = card_transfer_schema.load(transfer_data)
            
            # Realizar transferencia
            result = self.card_repository.transfer_balance(
                str(validated_data.get('from_card_id', '')),
                str(validated_data.get('to_card_id', '')),
                float(validated_data.get('amount', 0))
            )
            
            return result
            
        except ValidationError as e:
            logger.error(f"Error de validación en transferencia: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de transferencia: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_card_balance(self, card_id: str) -> Dict[str, Any]:
        """
        Obtener saldo de una tarjeta
        
        Args:
            card_id: ID de la tarjeta
            
        Returns:
            Dict: Información del saldo
        """
        try:
            card = self.card_repository.find_by_id(card_id)
            
            if not card:
                return {
                    'success': False,
                    'message': 'Tarjeta no encontrada'
                }
            
            return {
                'success': True,
                'message': 'Saldo obtenido exitosamente',
                'data': {
                    'card_id': card['_id'],
                    'card_number': card['card_number'],
                    'balance': card['balance'],
                    'is_active': card['is_active']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener saldo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_card(self, card_id: str) -> Dict[str, Any]:
        """
        Eliminar tarjeta (soft delete)
        
        Args:
            card_id: ID de la tarjeta
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que la tarjeta existe
            card = self.card_repository.find_by_id(card_id)
            if not card:
                return {
                    'success': False,
                    'message': 'Tarjeta no encontrada'
                }
            
            # Verificar que el saldo sea 0
            if float(card.get('balance', 0)) > 0:
                return {
                    'success': False,
                    'message': 'No se puede eliminar una tarjeta con saldo positivo'
                }
            
            # Realizar soft delete
            success = self.card_repository.soft_delete(card_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Tarjeta eliminada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar la tarjeta'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar tarjeta: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def validate_card_for_payment(self, card_id: str, amount: float) -> Dict[str, Any]:
        """
        Validar tarjeta para pago
        
        Args:
            card_id: ID de la tarjeta
            amount: Monto del pago
            
        Returns:
            Dict: Resultado de la validación
        """
        try:
            return self.card_repository.validate_card_for_payment(card_id, amount)
            
        except Exception as e:
            logger.error(f"Error en validación de tarjeta: {e}")
            return {
                'valid': False,
                'message': 'Error interno del servidor'
            } 

    def link_nfc_to_card(self, card_id: str) -> Dict[str, Any]:
        """
        Vincular tarjeta con UID NFC físico.
        
        Args:
            card_id: ID de la tarjeta a vincular con un dispositivo NFC.
        
        Returns:
            Dict: Resultado de la operación de vinculación.
        """
        try:
            from app.services.nfc_integration_service import NFCIntegrationService
            nfc_service = NFCIntegrationService()
            # Se delega la lógica de vinculación al servicio de integración NFC.
            return nfc_service.link_card_to_nfc(card_id)
        except Exception as e:
            logger.error(f"Error vinculando NFC: {e}")
            return {
                'success': False,
                'message': 'Error al vincular tarjeta NFC'
            }

    def reload_card_via_nfc(self, amount: float) -> Dict[str, Any]:
        """
        Recargar tarjeta mediante lectura NFC.
        
        Args:
            amount: Monto a recargar en la tarjeta detectada por NFC.
        
        Returns:
            Dict: Resultado de la operación de recarga.
        """
        try:
            from app.services.nfc_integration_service import NFCIntegrationService
            nfc_service = NFCIntegrationService()
            # Se delega la lógica de recarga al servicio de integración NFC.
            return nfc_service.reload_card_via_nfc(amount)
        except Exception as e:
            logger.error(f"Error recargando via NFC: {e}")
            return {
                'success': False,
                'message': 'Error al recargar tarjeta NFC'
            }

    def query_balance_via_nfc(self) -> Dict[str, Any]:
        """
        Consultar saldo de tarjeta mediante lectura NFC.
        
        Returns:
            Dict: Información del saldo y propietario de la tarjeta.
        """
        try:
            from app.services.nfc_integration_service import NFCIntegrationService
            nfc_service = NFCIntegrationService()
            # Se delega la lógica de consulta al servicio de integración NFC.
            return nfc_service.query_balance_via_nfc()
        except Exception as e:
            logger.error(f"Error consultando saldo via NFC: {e}")
            return {
                'success': False,
                'message': 'Error al consultar saldo via NFC'
            }