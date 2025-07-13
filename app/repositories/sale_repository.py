from typing import Dict, Any, Optional, List
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING, DESCENDING
from bson import ObjectId
from datetime import datetime, timedelta

class SaleRepository(BaseRepository):
    """
    Repositorio para ventas con operaciones UPSERT y manejo de transacciones
    """
    
    def __init__(self):
        super().__init__('sales')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para ventas
        
        Args:
            data: Datos de la venta
            
        Returns:
            Dict: Filtro basado en _id
        """
        filter_criteria = {}
        
        if '_id' in data:
            filter_criteria['_id'] = ObjectId(data['_id']) if isinstance(data['_id'], str) else data['_id']
        
        return filter_criteria
    
    def find_by_employee(self, employee_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar ventas por empleado
        
        Args:
            employee_id: ID del empleado
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ventas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'employee_id': employee_id},
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def find_by_client(self, client_id: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar ventas por cliente
        
        Args:
            client_id: ID del cliente
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ventas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'client_id': client_id},
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def find_by_status(self, status: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar ventas por estado
        
        Args:
            status: Estado de la venta (pending, completed, cancelled)
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ventas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'status': status},
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar ventas por rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ventas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={
                'created_at': {
                    '$gte': start_date,
                    '$lte': end_date
                }
            },
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1
        )
    
    def find_today_sales(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar ventas del día actual
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Ventas encontradas con información de paginación
        """
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        
        return self.find_by_date_range(today, tomorrow, page, per_page)
    
    def get_sales_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Obtener resumen de ventas por rango de fechas
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Dict: Resumen de ventas
        """
        pipeline = [
            {
                '$match': {
                    'created_at': {
                        '$gte': start_date,
                        '$lte': end_date
                    }
                }
            },
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1},
                    'total_amount': {'$sum': '$total_amount'}
                }
            }
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        summary = {
            'total_sales': 0,
            'total_amount': 0,
            'by_status': {}
        }
        
        for result in results:
            status = result['_id']
            count = result['count']
            amount = result['total_amount']
            
            summary['total_sales'] += count
            summary['total_amount'] += amount
            summary['by_status'][status] = {
                'count': count,
                'amount': amount
            }
        
        return summary
    
    def update_sale_status(self, sale_id: str, new_status: str) -> Optional[Dict[str, Any]]:
        """
        Actualizar estado de una venta
        
        Args:
            sale_id: ID de la venta
            new_status: Nuevo estado
            
        Returns:
            Dict: Venta actualizada o None
        """
        update_data = {
            '_id': sale_id,
            'status': new_status
        }
        
        # Agregar completed_at si el estado es completed
        if new_status == 'completed':
            update_data['completed_at'] = datetime.utcnow() # Guardar como objeto datetime
        
        return self.upsert(update_data)
    
    def update_service_status(self, sale_id: str, service_index: int, new_status: str, started_at: Optional[datetime] = None, estimated_end_at: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Actualizar estado de un servicio específico en una venta, incluyendo tiempos de inicio y fin.
        
        Args:
            sale_id: ID de la venta
            service_index: Índice del servicio en la lista
            new_status: Nuevo estado del servicio
            started_at: Hora de inicio del servicio (opcional)
            estimated_end_at: Hora estimada de finalización del servicio (opcional)
            
        Returns:
            Dict: Venta actualizada o None
        """
        try:
            # Obtener la venta actual
            sale = self.find_by_id(sale_id)
            if not sale:
                return None
            
            # Actualizar el estado del servicio
            services = sale.get('items', {}).get('services', [])
            if service_index < len(services):
                # Crear una nueva lista de servicios
                updated_services = []
                for i, svc in enumerate(services):
                    if i == service_index:
                        # Crear servicio actualizado
                        updated_service = dict(svc)
                        updated_service['status'] = new_status
                        
                        # Agregar timestamps según el estado
                        current_time = datetime.utcnow()
                        if new_status == 'active':
                            updated_service['started_at'] = started_at if started_at else current_time
                            updated_service['estimated_end_at'] = estimated_end_at # Asegura que estimated_end_at se guarde
                        elif new_status == 'completed':
                            updated_service['completed_at'] = current_time
                        
                        updated_services.append(updated_service)
                    else:
                        updated_services.append(dict(svc))
                
                # Usar la lista actualizada
                services = updated_services
                
                # Actualizar la venta
                update_data = {
                    '_id': sale_id,
                    'items': {
                        'products': sale.get('items', {}).get('products', []),
                        'services': services
                    }
                }
                
                return self.upsert(update_data)
            
            return None
            
        except Exception as e:
            print(f"Error updating service status: {e}")
            return None
    
    def get_active_services(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los servicios activos
        
        Returns:
            List: Lista de servicios activos con información de venta
        """
        pipeline = [
            {
                '$match': {
                    'status': {'$ne': 'cancelled'},
                    'items.services': {'$exists': True}
                }
            },
            {
                '$unwind': {
                    'path': '$items.services',
                    'includeArrayIndex': 'service_index' # Añade el índice del array
                }
            },
            {
                '$match': {
                    'items.services.status': 'active'
                }
            },
            {
                '$project': {
                    'sale_id': '$_id',
                    'client_id': '$client_id',
                    'employee_id': '$employee_id',
                    'service': '$items.services',
                    'service_index': '$service_index', # Incluir el service_index
                    'created_at': '$created_at'
                }
            }
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def get_pending_services(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los servicios pendientes
        
        Returns:
            List: Lista de servicios pendientes con información de venta
        """
        pipeline = [
            {
                '$match': {
                    'status': {'$ne': 'cancelled'},
                    'items.services': {'$exists': True}
                }
            },
            {
                '$unwind': '$items.services'
            },
            {
                '$match': {
                    'items.services.status': 'pending'
                }
            },
            {
                '$project': {
                    'sale_id': '$_id',
                    'client_id': '$client_id',
                    'employee_id': '$employee_id',
                    'service': '$items.services',
                    'created_at': '$created_at'
                }
            }
        ]
        
        return list(self.collection.aggregate(pipeline))
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('employee_id', ASCENDING)]),
            IndexModel([('client_id', ASCENDING)]),
            IndexModel([('status', ASCENDING)]),
            IndexModel([('created_at', DESCENDING)]),
            IndexModel([('completed_at', DESCENDING)]),
            IndexModel([('items.services.status', ASCENDING)]),
            IndexModel([('items.services.machine_id', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes) 