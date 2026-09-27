# Lavandería Purimatic

Sistema de gestión para lavandería autoservicio: ventas, encargos, máquinas ESP32, tarjetas NFC, tickets térmicos 80 mm e historial.

Stack: **Flask + MongoDB Atlas** (API) · **React + Vite** (frontend) · **puente NFC/ESP32** en Windows (puerto 5001).

## Qué incluye

| Módulo | Descripción |
|--------|-------------|
| **Ventas** | Wizard de cobro (servicios + productos), pago efectivo / tarjeta / NFC, activación de máquinas |
| **Encargos** | Lavado por kg + catálogo de servicios, estatus, ticket + etiqueta de bolsa |
| **Ciclos** | Precios, duración y máquinas permitidas (lavado / secado / encargo); crear y editar |
| **Equipo** | Lavadoras y secadoras; `esp32_id` solo desde placas registradas |
| **Placas ESP32** | Una URL por placa + varios IDs (`W001`…`W010`); prueba Encender/Apagar |
| **Tickets 80 mm** | ESC/POS en Windows; folio, barcode, logo, WiFi, horario, promo |
| **Clientes / tarjetas** | Saldo NFC, historial; base de beneficios (bono recarga / descuento al pagar) |
| **Dashboard** | Hub sin sidebar: Ventas, Historial, Encargos, Administración |

Detalle de cambios recientes: [`CHANGELOG.md`](CHANGELOG.md).

## Arquitectura

```
Ruta (HTTP) → Servicio (negocio) → Repositorio (MongoDB / UPSERT)
```

En tienda (producción empaquetada):

```
PC sucursal
├── Purimatic.exe          → API :5000 + frontend embebido
└── PurimaticNFC.exe       → NFC ACR122U + puente ESP32 :5001
        └── placas LC-10CH → http://IP/laundry-update
```

Desarrollo:

| Proceso | Puerto | Cómo arrancar |
|---------|--------|----------------|
| API Flask | 5000 | `python run.py` |
| Frontend Vite | 5173 (o el de Vite) | `cd frontend/lavanderia-frontend && npm run dev` |
| Puente NFC/ESP32 | 5001 | ver `nfc-service/README.md` |

## Requisitos

- Python 3.8+
- Node.js 18+ (solo desarrollo frontend)
- MongoDB Atlas
- Windows (impresión térmica `pywin32` y lector NFC `pyscard`)

## Instalación (desarrollo)

### 1. Backend

```bash
git clone <repository-url>
cd lavanderia-purimatic
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Crear `.env` en la raíz:

```env
FLASK_ENV=development
FLASK_DEBUG=True
MONGODB_URI=mongodb+srv://USER:PASS@cluster.mongodb.net/lavanderia_purimatic?retryWrites=true&w=majority
JWT_SECRET_KEY=cambia-esta-clave
JWT_ACCESS_TOKEN_EXPIRES=86400
SECRET_KEY=cambia-esta-clave
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:5000
PORT=5000
HOST=0.0.0.0
ESP32_BRIDGE_URL=http://localhost:5001
```

```bash
python run.py
```

API: `http://localhost:5000`

### 2. Frontend

```bash
cd frontend/lavanderia-frontend
npm install
npm run dev
```

La base URL de la API está en `src/services/apiConfig.js` (vacía en build de producción / `.exe`).

### 3. Puente NFC + ESP32 (opcional en local)

Ver [`nfc-service/README.md`](nfc-service/README.md). En tienda va empaquetado como `PurimaticNFC.exe`.

## Instalación en tienda (sin Python)

Guía operativa: [`INSTALACION_FINAL.md`](INSTALACION_FINAL.md)  
Regenerar instaladores: [`instalacion_pasos.md`](instalacion_pasos.md)

Resumen:

1. Generar `Purimatic.exe` (PyInstaller) y `PurimaticNFC.exe`.
2. Compilar Inno Setup (`installer/purimatic.iss` → `Purimatic-Setup.exe`).
3. Instalar en `%LOCALAPPDATA%\Purimatic`; configurar `.env` / asistente de Mongo por tienda.
4. Registrar placas ESP32 (URL + IDs) y asignar `esp32_id` a cada máquina.

## Módulos de la API (prefijo `/api` salvo auth)

| Área | Rutas principales |
|------|-------------------|
| Auth | `/auth/login`, `/auth/verify`, perfil |
| Empleados | `/employees` |
| Clientes | `/clients` |
| Productos | `/products` |
| Lavadoras / secadoras | `/washers`, `/dryers` |
| Ciclos de servicio | `/service-cycles` (POST = crear o actualizar con `_id`) |
| Ventas | `/sales` |
| Encargos | `/encargos`, precios `/encargos/settings` |
| Placas ESP32 | `/esp32-config` |
| Ticket | `/ticket-settings` |
| Tarjetas / beneficios | `/cards`, `/card-benefits-settings` |

Documentación extra de ventas: [`API_VENTAS.md`](API_VENTAS.md).

## Frontend (rutas útiles)

| Ruta UI | Uso |
|---------|-----|
| `/` | Dashboard |
| `/sales` | Cobro / ventas |
| `/encargos` | Encargos operativos |
| `/encargos-precios` | Precio/kg y catálogo (admin) |
| `/service-cycles` | Ciclos de servicio |
| `/machines` | Equipo |
| `/esp32-config` | Placas ESP32 |
| `/ticket-settings` | Ticket térmico |
| `/transactions` | Historial |
| `/card-benefits` | Beneficios de tarjeta (en curso) |

## Tickets térmicos

- Configuración en **Ticket** (tienda, logo, WiFi, promo, impresora, horario).
- Al cobrar venta o encargo se imprime automáticamente (si falla la impresión, el cobro no se cancela).
- El ticket muestra **nombres** de productos/servicios (sin IDs internos ni IDs de máquina).
- Folios: venta `YYYYMM-NNNN`, encargo `E-YYYYMM-NNNN`, con código de barras CODE128.

Dependencias Windows: `Pillow`, `pywin32` (en `requirements.txt`).

## Placas ESP32 (LC-10CH)

1. Configurar la placa (AP / hostname local) y anotar la IP.
2. En Purimatic: **una placa = una URL** + lista de `esp32_ids` (`W001`…`W010`).
3. Body hacia la placa: `{"washer_id":"W001","status":"starting",...}` vía puente `:5001`.

Más detalle en el changelog (sección 2026-09-20) e `INSTALACION_FINAL.md`.

## Estructura del repo

```
lavanderia-purimatic/
├── app/                      # API Flask
│   ├── routes/
│   ├── services/             # incl. ticket_print_service, sale, encargo, ESP32…
│   ├── repositories/
│   ├── schemas/
│   └── utils/
├── frontend/lavanderia-frontend/   # React + Vite
├── nfc-service/              # Puente NFC + ESP32
├── installer/                # Inno Setup
├── run.py
├── requirements.txt
├── CHANGELOG.md
├── INSTALACION_FINAL.md
└── README.md
```

## Autenticación

JWT Bearer. Roles: `admin` | `empleado`.

Crear admin de prueba: notebook `crear_usuario_admin.ipynb` (o tu flujo de seed).

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"TU_ADMIN\", \"password\": \"TU_PASSWORD\"}"
```

## Troubleshooting

| Problema | Qué revisar |
|----------|-------------|
| No conecta a Mongo | `MONGODB_URI`, red/IP allowlist en Atlas |
| Login / CORS en `.exe` | `API_BASE_URL` vacío; mismo origen Flask |
| Máquina no enciende | Puente `:5001`, `esp32_id` en placa y en la máquina, URL reachable |
| Ticket no imprime | Impresora en Ticket settings, `pywin32`, permisos Windows |
| NFC | ACR122U, `PurimaticNFC` / `pyscard` |

## Documentación relacionada

- [`CHANGELOG.md`](CHANGELOG.md) — historial de cambios
- [`INSTALACION_FINAL.md`](INSTALACION_FINAL.md) — despliegue en tienda
- [`instalacion_pasos.md`](instalacion_pasos.md) — build de instaladores
- [`API_VENTAS.md`](API_VENTAS.md) — API de ventas
- [`nfc-service/README.md`](nfc-service/README.md) — puente NFC/ESP32
- [`WEBSOCKET_MONITORING_SETUP.md`](WEBSOCKET_MONITORING_SETUP.md) — monitor de máquinas

## Licencia

Desarrollado para Lavandería Purimatic.
