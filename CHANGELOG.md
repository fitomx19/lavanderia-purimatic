# Changelog

## 2026-09-27 — UX de cobro, tickets limpios y docs

Ajustes de experiencia en el wizard de ventas, tickets más legibles para el cliente, y documentación al día.

### Wizard de ventas (pago)

- Por defecto el total completo va en **Efectivo** (primer método), sin teclear el monto.
- Al **dividir el pago**, los montos se limpian a `$0` para repartir a mano; se muestra Pagado / Resta.
- **Cancelar dividir** (o quitar métodos hasta uno) restaura un solo pago con el total completo.
- Al salir del paso Pagar y volver, se reinicia el default en efectivo.

### Tickets (venta y encargo)

- Ya no se imprimen identificadores internos (ObjectId, `product_id`, `service_cycle_id`, id de catálogo) ni IDs de máquina junto al renglón.
- El cliente ve solo nombres legibles (producto / ciclo / servicio de encargo); el peso en kg sí se muestra cuando aplica.

### Ciclos de servicio (seguimiento)

- Fix adicional al editar: `_id` es `dump_only` en Marshmallow; se excluye del `load` y se reinyecta para el UPSERT (evita `422 Unknown field`).

### Documentación

- `README.md` reescrito: stack completo (API, React, NFC/ESP32, tickets, encargos, instalador), rutas UI/API y enlaces a guías.
- Este changelog actualizado con los ajustes del 26–27.

---

## 2026-09-26 — Tickets 80 mm, encargos, placas multi-ID y rediseño de hub

Cambios del día: impresión térmica al cobrar, módulo de encargos, placas ESP32 con varios IDs por URL, rediseño de Dashboard/Header, y base de beneficios de tarjeta (bono en recarga / descuento al pagar).

### Impresión de tickets térmicos 80 mm

- Servicio ESC/POS en Windows (`ticket_print_service.py`) con Pillow + `pywin32` (`requirements.txt`).
- CRUD admin en `/ticket-settings`: nombre de tienda, dirección, logo (PNG/JPEG/WebP), WiFi (SSID + clave), promoción del mes, mensaje final, impresora y horario L–D configurable.
- Al cobrar una venta (`create_sale`) se imprime el ticket **antes** de encender la máquina; si falla la impresión, el cobro sigue y se avisa en la respuesta (`ticket_printed` / `ticket_message`).
- Folio de venta secuencial mensual `YYYYMM-NNNN` (ej. `202609-0001`) con índice único; código de barras CODE128 en el ticket.
- Ticket con secciones claras (detalle, horario, WiFi, promo), “Te atendió”, acentos CP850 y saldo restante si pagó con `tarjeta_recargable`.
- Impresión de prueba desde la UI de configuración.

### Placas ESP32 (multi-ID por URL)

- Modelo unificado: **una placa = una URL** + lista `esp32_ids` (ej. `W001`…`W010` en `http://192.168.0.110/laundry-update`).
- UI `/esp32-config`: crear placa (nombre + URL), agregar máquinas una a una, Encender/Apagar por ID, desactivar.
- Varias placas pueden coexistir (distintas IPs); al cargar se fusionan docs duplicados con la misma URL.
- El encendido sigue resolviendo la URL por `esp32_id` de la máquina.

### Módulo Encargos

- Pantalla operativa `/encargos` (admin y empleado) y precios admin `/encargos-precios`.
- Flujo: cliente (buscar / crear / NFC) → kilos + servicios del catálogo → cobro → ticket.
- Estatus: recibida → en lavado → terminada → entregada; reimpresión de ticket.
- Folio de encargo `E-YYYYMM-NNNN`; ticket de cliente + etiqueta de bolsa (folio grande) configurable.
- Pagos combinados (efectivo / tarjeta / NFC) con montos parciales.
- Buscador con autocomplete por folio o nombre de cliente.
- Pestañas: **Nuevo encargo** (por defecto) y **Buscar / estatus**.
- Al pasar a “En lavado”: modal para elegir lavadora + ciclo e encender la ESP32.
- Config: precio/kg, catálogo de servicios, flags `print_bag_label` e `print_notes`.
- Autoservicio de ventas **sin cambios** de flujo principal.

### Historial de ventas

- En Historial (pestaña Ventas): búsqueda por folio / escanear código + columna Folio.

### Rediseño Dashboard y Header

- Dashboard sin sidebar; CTA central de **Ventas** y secciones agrupadas (Operación rápida, Gestión, Técnico).
- “Reactivar máquinas” en la sección Técnico.
- Header compartido: marca, Ventas / Historial / Encargos, menú Administración (ESP32, Ticket, Precios encargos), usuario y logout; menú hamburguesa en móvil.

### Equipo (máquinas)

- UI más sobria (sin emojis informales).
- Campo ESP32 ya no es texto libre: **select** solo con IDs registrados en Placas ESP32 (sin inventar IDs).
- IDs ya asignados a otra máquina no se ofrecen (salvo el actual al editar).

### Ciclos de servicio

- UI alineada con Equipo/Encargos (cards, teal, filtros por tipo, modal limpio).
- **Editar** ciclo (precios, duración, máquinas, activo) vía UPSERT con `_id`.
- Fix backend: al actualizar se conserva el `_id` para no crear un documento duplicado.

### Beneficios de tarjeta (base / en curso)

- Colección y API `card_benefits_settings`: bono en recarga y descuento al pagar (combinables); modos de promo (paquetes / paquetes+libre / % + libre) y de descuento (% / precio por ciclo / elegir).
- UI `CardBenefitsPage` y schemas con `price_tarjeta` / `price_per_kg_tarjeta` en ciclos y precios de encargo.
- Pendiente de cerrar: pantalla ágil de recarga como venta, aplicación del descuento en cobro e impresión del ahorro en ticket.

### Dependencias

- Añadidos `Pillow` y `pywin32` para raster de logo e impresión Windows.

---

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
