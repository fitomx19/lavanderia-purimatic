# 🚀 Sistema de Monitoreo Automático de Máquinas - WebSocket

## 📋 Resumen de la Implementación

He implementado un sistema completo de monitoreo automático que:

✅ **Verifica cada 30 segundos** si algún servicio de máquina ha terminado  
✅ **Emite eventos WebSocket** automáticamente cuando detecta servicios completados  
✅ **Notifica al frontend** en tiempo real sin necesidad de recargar la página  
✅ **Muestra notificaciones visuales** cuando los servicios terminan automáticamente  
✅ **Actualiza el estado** de máquinas y ventas instantáneamente  

## 🔧 Instalación y Configuración

### 1. Instalar Nueva Dependencia

```bash
# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar APScheduler
pip install -r requirements.txt
```

### 2. Reiniciar el Servidor

```bash
# Detener el servidor actual (Ctrl+C)
# Reiniciar con:
python run.py
```

### 3. Verificar que Funciona

Al iniciar el servidor, deberías ver este mensaje en los logs:
```
✅ Scheduler de monitoreo iniciado - verificando cada 30 segundos
```

## 🎯 Cómo Funciona

### Backend - Sistema Automático
1. **APScheduler** ejecuta una tarea cada 30 segundos
2. **MachineMonitorService** verifica si algún servicio ha terminado
3. Cuando detecta servicios completados:
   - Actualiza el estado de la máquina a "disponible"
   - Marca el servicio como "completed" 
   - Emite eventos WebSocket: `services_completed` y `machine_status_updated`

### Frontend - Actualización en Tiempo Real
1. **WebSocket conectado** permanentemente (sin reconexiones constantes)
2. Escucha eventos `services_completed`
3. **Muestra notificación automática**: "🎉 X servicio(s) completado(s) automáticamente!"
4. **Actualiza la interfaz** sin recargar la página

## 📡 Eventos WebSocket Implementados

### Eventos Existentes (mejorados)
- `new_sale` - Nueva venta creada
- `sale_updated` - Venta actualizada  
- `sale_finalized` - Venta finalizada
- `machine_status_updated` - Estado de máquinas actualizado

### Nuevo Evento
- `services_completed` - Servicios completados automáticamente
  ```json
  {
    "count": 2,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "message": "2 servicios han sido completados"
  }
  ```

## 🎨 Nuevas Características Visuales

### Indicador de Monitoreo Activo
- **Punto verde pulsante** en el Panel de Control
- Texto: "Monitoreo Automático Activo"
- Confirma que el sistema está funcionando

### Notificaciones Automáticas
- **Toast verde** cuando servicios terminan automáticamente
- Duración: 8 segundos
- Mensaje personalizado con cantidad de servicios

## 🔍 Endpoints para Debugging (Solo Admin)

### Verificar Estado del Monitor
```http
GET /api/sales/monitor-status
Authorization: Bearer <admin_token>
```

### Forzar Verificación Manual
```http
POST /api/sales/check-services-now  
Authorization: Bearer <admin_token>
```

## ⚡ Beneficios del Sistema

### Para los Usuarios
- ✅ **Sin recargar página** - Actualizaciones automáticas
- ✅ **Notificaciones inmediatas** cuando servicios terminan
- ✅ **Estado actual visible** - indicador de monitoreo activo
- ✅ **Experiencia fluida** - sin interrupciones

### Para el Negocio
- ✅ **Eficiencia operacional** - no necesita verificar manualmente
- ✅ **Gestión en tiempo real** - estado preciso de máquinas
- ✅ **Mejor servicio al cliente** - respuesta inmediata
- ✅ **Reducción de errores** - automatización completa

## 🐛 Solución de Problemas

### Si no ves el indicador de monitoreo:
1. Verificar que APScheduler esté instalado: `pip show APScheduler`
2. Revisar logs del servidor para errores de scheduler
3. Verificar que el WebSocket esté conectado (consola del navegador)

### Si no llegan notificaciones automáticas:
1. Verificar conexión WebSocket en consola: "Conectado al servidor WebSocket"
2. Crear un servicio de prueba y esperar 30 segundos  
3. Revisar logs del servidor para actividad del monitor

### Para verificar que funciona:
1. **Crear una venta** con un servicio de 1 minuto de duración
2. **Completar la venta** para activar el servicio
3. **Esperar 1 minuto + 30 segundos** (siguiente verificación del monitor)
4. **Observar notificación automática** "🎉 1 servicio(s) completado(s) automáticamente!"

## 📊 Configuración Avanzada

### Cambiar Frecuencia de Verificación
En `app/__init__.py`, línea donde se configura el scheduler:
```python
# Cambiar de 30 segundos a otro valor
scheduler.add_job(
    func=machine_monitor.check_and_notify_completed_services,
    trigger="interval",
    seconds=30,  # <- Cambiar este valor
    ...
)
```

### Personalizar Notificaciones
En `frontend/lavanderia-frontend/src/pages/sales/SalesPages.jsx`:
```javascript
socketRef.current.on('services_completed', (data) => {
  toast.success(`🎉 ${data.count} servicio(s) completado(s) automáticamente!`, {
    autoClose: 8000,  // <- Duración en milisegundos
    hideProgressBar: false,
  });
});
```

## ✅ Verificación Final

El sistema está funcionando correctamente cuando ves:

1. **En el servidor**: "✅ Scheduler de monitoreo iniciado - verificando cada 30 segundos"
2. **En el frontend**: Indicador verde "Monitoreo Automático Activo"  
3. **En la consola del navegador**: "Conectado al servidor WebSocket" (solo una vez)
4. **En funcionamiento**: Notificaciones automáticas cuando servicios terminan

---

**🎉 ¡El sistema de monitoreo automático está listo y funcionando!**

Los servicios ahora se completarán automáticamente y recibirás notificaciones en tiempo real sin necesidad de recargar la página o verificar manualmente. 