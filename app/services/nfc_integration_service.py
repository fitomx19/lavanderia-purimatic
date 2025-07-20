from app.services.nfc_client_service import NFCClientService
from app.repositories.card_repository import CardRepository
from app.repositories.user_client_repository import UserClientRepository
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NFCIntegrationService:
    """Lógica de negocio para integración NFC"""
    
    def __init__(self):
        self.nfc_client = NFCClientService()
        self.card_repository = CardRepository()
        self.client_repository = UserClientRepository()
        self.logger = logger
    
    def link_card_to_nfc(self, card_id: str) -> Dict[str, Any]:
        """Vincular tarjeta lógica con UID físico"""
        try:
            # 1. Verificar que tarjeta existe
            card = self.card_repository.find_by_id(card_id)
            if not card:
                return {"success": False, "message": "Tarjeta no encontrada", "data": None}
            
            # 2. Verificar que no tenga UID ya vinculado
            if card.get('nfc_uid'):
                return {"success": False, "message": "Tarjeta ya tiene UID NFC vinculado", "data": None}
            
            # 3. Leer UID del lector NFC
            self.logger.info(f"Esperando tarjeta NFC para vincular con tarjeta {card_id}")
            nfc_result = self.nfc_client.wait_for_card(timeout=15)
            
            if not nfc_result["success"]:
                return {
                    "success": False, 
                    "message": nfc_result["error"] or "No se detectó tarjeta NFC",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            uid = nfc_result["uid"]
            
            # 4. Verificar que UID no esté usado
            if self.card_repository.nfc_uid_exists(uid):
                return {"success": False, "message": f"UID {uid} ya está vinculado a otra tarjeta", "data": None}
            
            # 5. Actualizar tarjeta con nfc_uid
            updated_card = self.card_repository.update_nfc_uid(card_id, uid)
            
            if updated_card:
                self.logger.info(f"Tarjeta {card_id} vinculada exitosamente con UID {uid}")
                return {
                    "success": True,
                    "message": f"Tarjeta vinculada exitosamente con UID {uid}",
                    "data": {
                        "card_id": card_id,
                        "nfc_uid": uid,
                        "card_number": updated_card["card_number"]
                    },
                    "logs": nfc_result["logs"]
                }
            else:
                return {"success": False, "message": "Error al actualizar tarjeta", "data": None}
                
        except Exception as e:
            self.logger.error(f"Error vinculando tarjeta NFC: {e}")
            return {"success": False, "message": "Error interno del servidor", "data": None}
    
    def reload_card_via_nfc(self, amount: float) -> Dict[str, Any]:
        """Recargar tarjeta detectando UID físico"""
        try:
            # 1. Validar monto
            if amount <= 0:
                return {"success": False, "message": "Monto debe ser mayor a 0", "data": None}
            
            # 2. Leer UID del lector NFC
            self.logger.info(f"Esperando tarjeta NFC para recargar ${amount}")
            nfc_result = self.nfc_client.wait_for_card(timeout=15)
            
            if not nfc_result["success"]:
                return {
                    "success": False,
                    "message": nfc_result["error"] or "No se detectó tarjeta NFC",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            uid = nfc_result["uid"]
            
            # 3. Buscar tarjeta por nfc_uid
            card = self.card_repository.find_by_nfc_uid(uid)
            if not card:
                return {
                    "success": False,
                    "message": f"No se encontró tarjeta vinculada al UID {uid}",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            # 4. Verificar que tarjeta está activa
            if not card.get('is_active', False):
                return {"success": False, "message": "Tarjeta inactiva", "data": None}
            
            # 5. Agregar saldo
            old_balance = float(card.get('balance', 0))
            updated_card = self.card_repository.update_balance(card['_id'], amount, 'add')
            
            if updated_card:
                new_balance = float(updated_card['balance'])
                self.logger.info(f"Tarjeta {uid} recargada: ${old_balance} -> ${new_balance}")
                return {
                    "success": True,
                    "message": f"Recarga exitosa. Nuevo saldo: ${new_balance}",
                    "data": {
                        "card_id": str(updated_card['_id']),
                        "card_number": updated_card['card_number'],
                        "old_balance": old_balance,
                        "new_balance": new_balance,
                        "amount_added": amount,
                        "nfc_uid": uid
                    },
                    "logs": nfc_result["logs"]
                }
            else:
                return {"success": False, "message": "Error al actualizar saldo", "data": None}
                
        except Exception as e:
            self.logger.error(f"Error recargando tarjeta NFC: {e}")
            return {"success": False, "message": "Error interno del servidor", "data": None}

    def query_balance_via_nfc(self) -> Dict[str, Any]:
        """Consultar saldo de tarjeta detectando UID físico"""
        try:
            # 1. Leer UID del lector NFC
            self.logger.info("Esperando tarjeta NFC para consultar saldo")
            nfc_result = self.nfc_client.wait_for_card(timeout=15)
            
            if not nfc_result["success"]:
                return {
                    "success": False,
                    "message": nfc_result["error"] or "No se detectó tarjeta NFC",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            uid = nfc_result["uid"]
            
            # 2. Buscar tarjeta por nfc_uid
            card = self.card_repository.find_by_nfc_uid(uid)
            if not card:
                return {
                    "success": False,
                    "message": f"No se encontró tarjeta vinculada al UID {uid}",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            # 3. Verificar que tarjeta está activa
            if not card.get('is_active', False):
                return {
                    "success": False, 
                    "message": "Tarjeta inactiva", 
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            # 4. Buscar información del cliente propietario
            client_id = card.get('client_id')
            if not client_id:
                return {
                    "success": False,
                    "message": "Tarjeta sin cliente asignado",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            client = self.client_repository.find_by_id(client_id)
            if not client:
                return {
                    "success": False,
                    "message": "Cliente propietario no encontrado",
                    "data": None,
                    "logs": nfc_result["logs"]
                }
            
            # 5. Preparar respuesta con información completa
            balance = float(card.get('balance', 0))
            client_name = f"{client.get('nombre', '')} {client.get('apellido', '')}".strip()
            
            self.logger.info(f"Consulta de saldo exitosa - Tarjeta {uid}: ${balance} - Cliente: {client_name}")
            
            return {
                "success": True,
                "message": f"Saldo consultado exitosamente",
                "data": {
                    "card_id": str(card['_id']),
                    "card_number": card['card_number'],
                    "balance": balance,
                    "nfc_uid": uid,
                    "client_info": {
                        "client_id": str(client['_id']),
                        "name": client_name,
                        "email": client.get('email', ''),
                        "telefono": client.get('telefono', '')
                    },
                    "last_used": card.get('last_used'),
                    "is_nfc_enabled": card.get('is_nfc_enabled', False)
                },
                "logs": nfc_result["logs"]
            }
                
        except Exception as e:
            self.logger.error(f"Error consultando saldo via NFC: {e}")
            return {"success": False, "message": "Error interno del servidor", "data": None}