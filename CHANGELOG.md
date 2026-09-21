# Changelog

## 2026-09-20 — Instalador de tienda, puente NFC/ESP32 y placas de 10 canales

Cambios del día para dejar Purimatic instalable en una PC de sucursal **sin Python**, con MongoDB Atlas por tienda, lector NFC y control de ESP32.

### Instalador y empaquetado

- Instalador único Inno Setup (`installer/purimatic.iss` → `dist-installer/Purimatic-Setup.exe`) que copia:
  - API + frontend (`dist/Purimatic`)
  - puente NFC + ESP32 (`nfc-service/dist/PurimaticNFC`)
- Instalación en `%LOCALAPPDATA%\Purimatic` (sin administrador), iconos de inicio y arranque automático de **los dos** `.exe`.
- `purimatic.spec`: frontend Vite embebido, SocketIO en `threading` (se excluye `gevent` para que el `.exe` no rompa Werkzeug).
- `nfc-service/nfc-service.spec`: empaqueta `pyscard`/`smartcard` (incluido `_scard.pyd`); fuerza salida a `nfc-service/dist` y saca la raíz del repo del `sys.path` para no congelar el paquete `app` del backend (`product_routes`).
- Asistente `setup_wizard.py` y reintentos de Mongo al arrancar; cada tienda guarda su `.env` junto al `.exe`.

### Backend (API puerto 5000)

- CORS y frontend en el mismo origen en producción (`apiConfig.js` con `API_BASE_URL` vacío en el `.exe`) para que el login no se quede en OPTIONS / error de conexión.
- Colección `esp32_config` (`esp32_id`, `esp32_url`, `is_active`) con índice único y CRUD (`GET/POST/PUT/DELETE` + prueba de relé).
- `washers` / `dryers` con campo `esp32_id`.
- `ESP32Service` apunta al puente `http://localhost:5001` (`ESP32_BRIDGE_URL`) y envía `POST /send-to-esp32`.
- Fix: crear lavadora insertaba en Mongo pero respondía **500** (`Decimal` no serializable). Las respuestas JSON convierten `Decimal` a número.

### Puente NFC + ESP32 (puerto 5001)

- `nfc-service` unifica lector ACR122U y reenvío a placas (`esp32_manager.py`, `POST /send-to-esp32`).
- `pyscard` es obligatorio y va dentro de `PurimaticNFC.exe` (ya no es opcional).
- Pause en consola si el `.exe` falla al arrancar, para ver el traceback.

### Frontend

- Pantalla **Placas ESP32**: alta de placa, URL, Encender/Apagar (prueba sin venta), desactivar.
- Equipo: campo `esp32_id` al crear/editar lavadora y secadora.
- Login y menú apuntan al mismo host que sirve Flask cuando está empaquetado.

### Configuración real de la placa LC-10CH-ESP32

- Flujo físico documentado: AP `http://192.168.4.1` (clave `setup123456`) → hostname tipo `http://laundry-53dfac.local/` en el celular → anotar IP → registrar en el configurador de Purimatic.
- Un registro en `esp32_config` **por cada canal** que se use (`W001`…`W010`), todos con `http://IP/laundry-update`. El `esp32_id` es el id del relé, no el último octeto de la IP (`110` ≠ `W001`).
- Body que acepta la placa: `{"washer_id":"W001","status":"starting","start_time":"...","end_time":"..."}`.

### Documentación

- `INSTALACION_FINAL.md`: guía de instalación en tienda + redacción del ESP32 externo con la IP.
- `instalacion_pasos.md` y comentarios de Inno: cómo regenerar los `.exe` (PyInstaller del NFC con `--distpath dist` dentro de `nfc-service`).
