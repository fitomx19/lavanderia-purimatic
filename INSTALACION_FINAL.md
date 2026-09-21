# Instalación final de Purimatic (tienda)

Guía para poner en marcha una sucursal **sin Python**. Un solo instalador deja la pantalla, la API, el lector NFC y el puente hacia las placas ESP32.

Cada tienda usa **su propia** base de MongoDB Atlas.

| Programa | Dónde queda | Puerto | Qué hace |
|---|---|---|---|
| Purimatic | `%LOCALAPPDATA%\Purimatic\Purimatic.exe` | `http://localhost:5000` | Login, ventas, equipo, placas ESP32, Atlas |
| Purimatic NFC | `%LOCALAPPDATA%\Purimatic\nfc-service\PurimaticNFC.exe` | `http://localhost:5001` | Lector ACR122U + envío a las placas ESP32 |

Solo se instala **un** archivo: `dist-installer/Purimatic-Setup.exe`. Ese Setup ya incluye el servicio del lector NFC. No hay un instalador aparte de NFC.

---

## 1. Instalar el software

1. Ejecutar `Purimatic-Setup.exe` (no pide administrador).
2. Dejar marcada **Iniciar Purimatic al iniciar sesión de Windows**.
3. Al final, marcar las dos opciones:
   - **Iniciar puente NFC y ESP32**
   - **Iniciar Purimatic y configurar MongoDB Atlas de esta tienda**
4. Si Windows pregunta por el firewall, aceptar **redes privadas**.

Deben quedar **dos ventanas**: Purimatic (5000) y PurimaticNFC (5001). El lector ACR122U se conecta por USB; Windows suele traer el driver PC/SC.

---

## 2. MongoDB Atlas de esta tienda

Al primer arranque se abre **Purimatic — Configurar esta tienda**.

1. En [cloud.mongodb.com](https://cloud.mongodb.com) copiar la URI de **esta** sucursal (`mongodb+srv://...`).
2. Pegarla en el asistente, nombre de base `lavanderia_purimatic`.
3. **Probar conexión** y luego **Guardar y continuar**.

El `.env` queda en `%LOCALAPPDATA%\Purimatic\.env` (`MONGODB_URI` y `ESP32_BRIDGE_URL=http://localhost:5001`).

Para reabrir el asistente: menú Inicio → **Reconfigurar MongoDB Atlas**, o `Purimatic.exe --setup`.

---

## 3. Configuración del dispositivo ESP32 externo (con la IP)

Este es el orden en sitio. Una placa LC-10CH-ESP32 controla **varios relés** (canales `W001` a `W010`). Hay que registrar **cada puerto / cada id** que se vaya a usar en las máquinas, en **Placas ESP32** (`esp32_config`).

Contraseña del Access Point de la placa: **`setup123456`**

### Paso 1 — Conectarse al aparato (URL base)

1. Encender el ESP32.
2. En el celular, unirse a la WiFi que emite la placa.
3. Contraseña: `setup123456`. Es normal que el teléfono diga “sin internet”.
4. En el navegador abrir la URL base del ESP32:

```
http://192.168.4.1
```

Ahí se carga el **WiFi de la tienda** (SSID y contraseña, el mismo de la PC de caja). Guardar. La placa se reinicia y se une a esa red.

### Paso 2 — Anotar la IP desde el celular

Volver al WiFi de la tienda. En el celular abrir el hostname de esa placa, por ejemplo:

```
http://laundry-53dfac.local/
```

(El nombre cambia según el aparato; en `/status` aparece como `hostname`, ejemplo `laundry-53dfac`.)

Anotar la **IP local** que muestra (ejemplo `192.168.0.110`). Se puede confirmar en:

```
http://192.168.0.110/status
```

Ahí se ven los canales reales: `W001`, `W002`, … `W010`. **No** se usa `110` como id de relé: `110` es solo el último número de la IP.

### Paso 3 — Configurar la IP en el configurador ESP32 de Purimatic

1. En la PC de caja: `http://localhost:5000` → login admin → **Placas ESP32**.
2. Por **cada canal que se vaya a usar** en Equipo, guardar un registro:

| Campo | Ejemplo |
|---|---|
| `esp32_id` | `W001` (el id del relé, no la IP) |
| `esp32_url` | `http://192.168.0.110/laundry-update` |

3. Repetir para `W002`, `W003`, … solo los puertos que existan en las lavadoras/secadoras. **Todos comparten la misma URL** (la misma IP de esa placa). La URL de comando es `/laundry-update`, no `/status`.
4. **Encender** / **Apagar** prueba ese relé sin hacer una venta. PurimaticNFC debe estar en el puerto 5001.

El POST que espera la placa es:

```
POST http://192.168.0.110/laundry-update
{"washer_id":"W001","status":"starting","start_time":"...","end_time":"..."}
```

Purimatic manda `washer_id` igual al `esp32_id` de la ficha. Por eso hay que registrar `W001`, no `110`.

**Listo.** Eso es toda la configuración física + registro en el sistema.

### Vincular cada máquina en Equipo

En **Equipo**, cada lavadora o secadora lleva el **mismo** `esp32_id` del canal (`W001` en la máquina 1, `W002` en la 2, etc.).

Si el id de Equipo no coincide con el de Placas ESP32, la venta se guarda pero el relé no prende.

### Cómo viaja el comando

```
Venta / botón Encender
    → washers.esp32_id  (ej. W001)
    → esp32_config.esp32_url  (ej. http://192.168.0.110/laundry-update)
    → API :5000 llama POST http://localhost:5001/send-to-esp32
    → PurimaticNFC hace POST a la placa
    → el relé de ese canal enciende
```

Si el router cambia IPs, reservar la IP de la placa en el DHCP (por MAC). PC y ESP32 deben estar en el **mismo WiFi**.

---

## 4. Comprobar

1. Dos consolas: Purimatic en 5000 y PurimaticNFC en 5001.
2. Placas ESP32 → Encender / Apagar en `W001` (el relé de ese canal debe activarse).
3. Lector: `GET http://localhost:5001/health` con el ACR122U conectado.
4. Una venta de prueba en la lavadora que tenga `esp32_id` = `W001`.

---

## Resumen en sitio

1. Instalar **solo** `Purimatic-Setup.exe` (incluye NFC).
2. Pegar la URI de Atlas de **esta** tienda → Probar → Guardar.
3. ESP32: `http://192.168.4.1` (clave `setup123456`) → WiFi de la tienda → `http://laundry-XXXXXX.local/` en el celular → anotar IP.
4. En el configurador de Purimatic, un registro por cada puerto (`W001`…`W010`) con `http://IP/laundry-update`.
5. En Equipo, el mismo `esp32_id` en cada máquina.
6. Encender/Apagar y luego una venta.
