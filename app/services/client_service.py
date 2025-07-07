from typing import Dict, Any, Optional
from app.repositories.user_client_repository import UserClientRepository
from app.schemas.user_client_schema import (
    user_client_schema,
    user_client_update_schema,
    user_client_balance_schema,
    user_client_response_schema,
    users_client_response_schema
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

class ClientService:
    """
    Servicio para manejo de clientes con lógica de negocio
    """
    
    def __init__(self):
        self.client_repository = UserClientRepository()
    
    def create_or_update_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear o actualizar cliente usando UPSERT
        
        Args:
            client_data: Datos del cliente
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos según si es creación o actualización
            if '_id' in client_data:
                # Actualización
                client_id = client_data['_id']
                
                # Crear una copia mutable y eliminar _id para la validación del esquema
                data_for_validation = client_data.copy()
                del data_for_validation['_id']

                # Cargar y validar datos
                # Asertar que el resultado de load es un diccionario si no hay ValidationError
                validated_data = user_client_update_schema.load(data_for_validation)
                assert isinstance(validated_data, dict)
                
                # Añadir _id de vuelta a validated_data para el upsert
                validated_data['_id'] = client_id 
                
                # Verificar que el cliente existe
                existing_client = self.client_repository.find_by_id(client_id)
                if not existing_client:
                    return {
                        'success': False,
                        'message': 'Cliente no encontrado'
                    }
                
                # Verificar unicidad de campos si se están actualizando
                if 'email' in validated_data and isinstance(validated_data['email'], str):
                    if self.client_repository.email_exists(validated_data['email'], client_id):
                        return {
                            'success': False,
                            'message': 'El email ya existe'
                        }
                
                if 'telefono' in validated_data and isinstance(validated_data['telefono'], str):
                    if self.client_repository.telefono_exists(validated_data['telefono'], client_id):
                        return {
                            'success': False,
                            'message': 'El teléfono ya existe'
                        }
                
            else:
                # Creación
                validated_data = user_client_schema.load(client_data)
                assert isinstance(validated_data, dict)
                
                # Verificar unicidad de campos
                if self.client_repository.email_exists(validated_data['email']):
                    return {
                        'success': False,
                        'message': 'El email ya existe'
                    }
                
                if self.client_repository.telefono_exists(validated_data['telefono']):
                    return {
                        'success': False,
                        'message': 'El teléfono ya existe'
                    }
            
            # Realizar upsert
            client = self.client_repository.upsert(validated_data)
            
            if client:
                client_response = user_client_response_schema.dump(client)
                return {
                    'success': True,
                    'message': 'Cliente guardado exitosamente',
                    'data': client_response
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al guardar el cliente'
                }
                
        except ValidationError as e:
            logger.error(f"Error de validación en cliente: {e.messages}")
            return {
                'success': False,
                'message': 'Datos de entrada inválidos',
                'errors': e.messages
            }
        except Exception as e:
            logger.error(f"Error en servicio de cliente: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_client_by_id(self, client_id: str) -> Dict[str, Any]:
        """
        Obtener cliente por ID
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Dict: Información del cliente
        """
        try:
            client = self.client_repository.find_by_id(client_id)
            
            if not client:
                return {
                    'success': False,
                    'message': 'Cliente no encontrado'
                }
            
            client_response = user_client_response_schema.dump(client)
            return {
                'success': True,
                'message': 'Cliente encontrado',
                'data': client_response
            }
            
        except Exception as e:
            logger.error(f"Error al obtener cliente: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def get_clients_list(self, page: int = 1, per_page: int = 10, search: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener lista de clientes con paginación
        
        Args:
            page: Página actual
            per_page: Elementos por página
            search: Término de búsqueda por nombre
            
        Returns:
            Dict: Lista de clientes
        """
        try:
            result = self.client_repository.find_clients_with_card_balance(search, page, per_page)
            
            clients_response = users_client_response_schema.dump(result['documents'])
            
            return {
                'success': True,
                'message': 'Clientes obtenidos exitosamente',
                'data': clients_response,
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages']
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener lista de clientes: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def delete_client(self, client_id: str) -> Dict[str, Any]:
        """
        Eliminar cliente (soft delete)
        
        Args:
            client_id: ID del cliente
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Verificar que el cliente existe
            client = self.client_repository.find_by_id(client_id)
            if not client:
                return {
                    'success': False,
                    'message': 'Cliente no encontrado'
                }
            
            # Realizar soft delete
            deleted = self.client_repository.soft_delete(client_id)
            
            if deleted:
                return {
                    'success': True,
                    'message': 'Cliente eliminado exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al eliminar el cliente'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar cliente: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def update_client_balance(self, client_id: str, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar saldo de tarjeta recargable del cliente
        
        Args:
            client_id: ID del cliente
            balance_data: Datos del saldo (saldo_tarjeta_recargable, operacion)
            
        Returns:
            Dict: Resultado de la operación
        """
        try:
            # Validar datos de entrada
            validated_data = user_client_balance_schema.load(balance_data)
            assert isinstance(validated_data, dict)

            # Verificar que el cliente existe
            client = self.client_repository.find_by_id(client_id)
            if not client:
                return {
                    'success': False,
                    'message': 'Cliente no encontrado'
                }
            
            # Actualizar saldo
            updated_client = self.client_repository.update_balance(
                client_id,
                float(validated_data['saldo_tarjeta_recargable']),
                validated_data['operacion']
            )
            
            if updated_client:
                client_response = user_client_response_schema.dump(updated_client)
                return {
                    'success': True,
                    'message': 'Saldo actualizado exitosamente',
                    'data': client_response
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
            logger.error(f"Error al actualizar saldo: {e}")
            return {
                'success': False,
                'message': 'Error interno del servidor'
            }
    
    def search_clients(self, search_term: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Buscar clientes por nombre
        
        Args:
            search_term: Término de búsqueda
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Lista de clientes encontrados
        """
        return self.get_clients_list(page, per_page, search=search_term)
