# 🔍 Microservicio NFC - ACR122U

Microservicio Flask para manejo de lectores NFC ACR122U en el sistema de lavandería Purimatic.

## 🚀 Características

- ✅ **Detección automática** de lectores ACR122U
- ✅ **Lectura de UID** de tarjetas NFC/RFID
- ✅ **Timeouts configurables** para operaciones
- ✅ **Logs coloridos** y explicativos
- ✅ **APIs REST** con respuestas estandarizadas
- ✅ **Manejo robusto de errores**
- ✅ **Health checks** y monitoreo
- 🆕 **Inicialización forzada** de lectores
- 🆕 **Pruebas de comunicación** en tiempo real
- 🆕 **Reset automático** de conexiones
- 🆕 **Diagnóstico completo** del sistema
- 🆕 **Troubleshooting integrado** con recomendaciones
- 🆕 **Script de pruebas** automatizado

## 📦 Instalación

### Prerrequisitos

- Python 3.8+
- Lector ACR122U conectado via USB
- Drivers PC/SC instalados:
  - **Windows**: Automático con Windows Update
  - **Linux**: `sudo apt-get install pcscd pcsc-tools`
  - **macOS**: Incluido en el sistema

### Configuración

```bash
# 1. Clonar y navegar al directorio
cd nfc-service

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear archivo .env (opcional)
# Copiar variables del ejemplo en config.py
```

## 🔧 Configuración

El microservicio usa variables de entorno con valores por defecto:

```bash
# Configuración del servicio NFC
FLASK_PORT=5001
FLASK_DEBUG=True
LOG_LEVEL=INFO
NFC_TIMEOUT=10
NFC_RETRY_ATTEMPTS=3
```

## 🚦 Uso

### Iniciar el Servicio

```bash
python main.py
```

El servicio iniciará en `http://localhost:5001`

### APIs Disponibles

#### 🏥 Health Check
```bash
GET /health
```

#### 📊 Estado del Servicio
```bash
GET /status
```

#### 📖 Leer Tarjeta Inmediatamente
```bash
POST /read-card
```

#### ⏳ Esperar por Tarjeta
```bash
POST /wait-for-card
Content-Type: application/json

{
  "timeout": 15
}
```

#### 🔧 Inicializar Lector (NUEVO)
```bash
POST /initialize
```

#### 🧪 Probar Comunicación (NUEVO)
```bash
POST /test-connection
```

#### 🔄 Reiniciar Lector (NUEVO)
```bash
POST /reset-reader
```

#### 🔍 Diagnóstico Completo (NUEVO)
```bash
GET /diagnostics
```

## 📋 Ejemplos de Respuesta

### Éxito - Tarjeta Leída
```json
{
  "success": true,
  "message": "Tarjeta NFC leída exitosamente: A1B2C3D4",
  "data": {
    "uid": "A1B2C3D4",
    "uid_length": 8,
    "format": "hexadecimal",
    "reader_info": {
      "name": "ACS ACR122U PICC Interface 0",
      "type": "ACR122U",
      "status": "connected"
    }
  },
  "logs": [
    "[2024-01-01T10:00:00] INFO - Verificando estado del lector ACR122U...",
    "[2024-01-01T10:00:01] INFO - Lector ACR122U encontrado: ACS ACR122U...",
    "[2024-01-01T10:00:02] INFO - UID leído exitosamente: A1B2C3D4"
  ],
  "timestamp": "2024-01-01T10:00:02.123Z",
  "duration_ms": 156.78
}
```

### Error - Sin Lector
```json
{
  "success": false,
  "message": "Lector ACR122U no conectado",
  "error_code": "SERVICE_UNAVAILABLE",
  "status_code": 503,
  "logs": [
    "[2024-01-01T10:00:00] WARNING - No se encontraron lectores NFC conectados"
  ],
  "timestamp": "2024-01-01T10:00:00.456Z",
  "duration_ms": 23.45
}
```

## 🔍 Testing

### Script de Prueba Automático (NUEVO)

```bash
# Ejecutar todas las pruebas automáticamente
python test_endpoints.py
```

### Comandos de Prueba Manuales

```bash
# Health check básico
curl http://localhost:5001/health

# Estado del servicio (mejorado)
curl http://localhost:5001/status

# Diagnóstico completo del sistema
curl http://localhost:5001/diagnostics

# Inicializar lector ACR122U
curl -X POST http://localhost:5001/initialize

# Probar comunicación con hardware
curl -X POST http://localhost:5001/test-connection

# Reiniciar conexión del lector
curl -X POST http://localhost:5001/reset-reader

# Leer tarjeta inmediatamente
curl -X POST http://localhost:5001/read-card

# Esperar tarjeta por 5 segundos
curl -X POST http://localhost:5001/wait-for-card \
  -H "Content-Type: application/json" \
  -d '{"timeout": 5}'
```

### Flujo de Troubleshooting Recomendado

```bash
# 1. Verificar estado general
curl http://localhost:5001/status

# 2. Si hay problemas, obtener diagnóstico completo
curl http://localhost:5001/diagnostics

# 3. Intentar inicializar el lector
curl -X POST http://localhost:5001/initialize

# 4. Probar comunicación específica
curl -X POST http://localhost:5001/test-connection

# 5. Si sigue fallando, reiniciar conexión
curl -X POST http://localhost:5001/reset-reader
```

### Sin Hardware

El servicio funciona sin lector conectado:
- `/health` siempre responde ✅
- `/status` reporta estado sin hardware ⚠️
- Operaciones de lectura fallan con código 503 ❌

## 🐛 Solución de Problemas

### Lector No Detectado

```bash
# Verificar drivers PC/SC
# Windows:
sc query SCardSvr

# Linux:
sudo systemctl status pcscd
pcsc_scan

# macOS:
system_profiler SPUSBDataType | grep -A 5 ACR122
```

### Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `SERVICE_UNAVAILABLE` | Sin lector conectado | Conectar ACR122U |
| `CARD_NOT_DETECTED` | Sin tarjeta en lector | Colocar tarjeta NFC |
| `NFC_TIMEOUT` | Operación excedió tiempo | Reducir timeout o revisar hardware |
| `CONNECTION_ERROR` | Fallo de comunicación | Reconectar lector, verificar drivers |

## 📁 Estructura del Proyecto

```
nfc-service/
├── app/
│   ├── __init__.py              # Configuración del paquete
│   ├── config.py                # Variables de entorno
│   ├── nfc_manager.py           # Lógica principal NFC
│   ├── routes/
│   │   ├── __init__.py
│   │   └── nfc_routes.py        # Endpoints HTTP
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py            # Sistema de logging
│   │   └── response_utils.py    # Respuestas HTTP
│   └── exceptions/
│       ├── __init__.py
│       └── nfc_exceptions.py    # Excepciones personalizadas
├── requirements.txt             # Dependencias Python
├── main.py                     # Punto de entrada
├── .gitignore                  # Archivos ignorados
└── README.md                   # Este archivo
```

## 🔗 Integración

### Con Sistema Principal

```python
import requests

# Verificar estado
response = requests.get('http://localhost:5001/status')
if response.json()['data']['reader_status']['connected']:
    # Leer tarjeta
    card_response = requests.post('http://localhost:5001/read-card')
    uid = card_response.json()['data']['uid']
    print(f"UID detectado: {uid}")
```

### Configuración de Producción

```bash
# Variables de entorno recomendadas para producción
FLASK_DEBUG=False
LOG_LEVEL=WARNING
NFC_TIMEOUT=5
NFC_RETRY_ATTEMPTS=2
```

## 📄 Licencia

Sistema propietario - Lavandería Purimatic

## 👥 Soporte

Para soporte técnico o reportar problemas, contacta al equipo de desarrollo del sistema de lavandería.
