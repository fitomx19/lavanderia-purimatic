from datetime import datetime
import logging
from typing import Dict, Any
from app.services.sale_service import SaleService
from app import socketio

logger = logging.getLogger(__name__)

class MachineMonitorService:
    """
    Servicio para monitorear automáticamente el estado de las máquinas
    y emitir eventos WebSocket cuando los servicios terminen
    """
    
    def __init__(self):
        self.sale_service = SaleService()
        self.last_check = datetime.utcnow()
    
    def check_and_notify_completed_services(self) -> Dict[str, Any]:
        """
        Verificar servicios completados y emitir notificaciones WebSocket
        
        Returns:
            Dict: Resultado de la verificación
        """
        try:
            logger.info("🔍 Verificando servicios completados...")
            
            # Verificar y desactivar máquinas que han terminado su ciclo
            result = self.sale_service.check_and_deactivate_machines()
            
            if result['success']:
                # Extraer el número de máquinas actualizadas del mensaje
                message = result['message']
                updated_count = 0
                if message:
                    try:
                        # Extraer número del mensaje ej: "5 máquinas y servicios actualizados."
                        updated_count = int(message.split(' ')[0])
                    except:
                        updated_count = 0
                
                if updated_count > 0:
                    logger.info(f"✅ {updated_count} servicios completados detectados")
                    
                    # Emitir eventos WebSocket para notificar cambios
                    socketio.emit('services_completed', {
                        'count': updated_count,
                        'timestamp': datetime.utcnow().isoformat(),
                        'message': f'{updated_count} servicios han sido completados'
                    })
                    
                    # También emitir el evento estándar de actualización de máquinas
                    socketio.emit('machine_status_updated', {
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': 'services_completed'
                    })
                    
                    logger.info(f"📡 Eventos WebSocket emitidos para {updated_count} servicios completados")
                else:
                    logger.debug("ℹ️ No se detectaron servicios completados")
                
                self.last_check = datetime.utcnow()
                
                return {
                    'success': True,
                    'updated_count': updated_count,
                    'message': f'Verificación completada. {updated_count} servicios actualizados.'
                }
            else:
                logger.error(f"❌ Error en verificación de servicios: {result['message']}")
                return {
                    'success': False,
                    'message': f"Error en verificación: {result['message']}"
                }
                
        except Exception as e:
            logger.error(f"❌ Error en monitoreo de máquinas: {e}")
            return {
                'success': False,
                'message': f'Error interno en monitoreo: {str(e)}'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtener estado del monitor
        
        Returns:
            Dict: Estado actual del monitor
        """
        return {
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'status': 'active',
            'service': 'machine_monitor'
        }

# Instancia global del monitor
machine_monitor = MachineMonitorService() 