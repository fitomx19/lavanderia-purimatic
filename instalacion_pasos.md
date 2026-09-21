# Instalación de Purimatic en una tienda (paso a paso)

Esta guía es para una computadora de tienda **sin Python**. Cada tienda usa **su propia** base de MongoDB Atlas.

Al terminar deben estar corriendo dos programas:

| Programa | Puerto | Qué hace |
|---|---|---|
| Purimatic (API + pantalla) | `http://localhost:5000` | Login, ventas, lavadoras, placas ESP32, MongoDB Atlas |
| Purimatic NFC (puente) | `http://localhost:5001` | Lector NFC + envío de comandos a las placas ESP32 |

---

## 0. Antes de ir a la tienda (en la máquina de desarrollo)

Solo quien arma el instalador necesita Python y Node. En la tienda **no**.

1. Compilar el frontend (si omites este paso, el .exe no muestra la pantalla de login):
   - `cd frontend/lavanderia-frontend`
   - `npm install`
   - `npm run build`
2. Empaquetar la API + UI:
   - En la raíz del proyecto: `pyinstaller --noconfirm --clean purimatic.spec`
3. Empaquetar el puente NFC/ESP32 (el `.exe` debe quedar en `nfc-service/dist`, no en `dist/` de la raíz):
   - En `nfc-service/`: `pyinstaller --noconfirm --clean --distpath dist --workpath build nfc-service.spec`
4. Abrir `installer/purimatic.iss` con Inno Setup Compiler y pulsar **Build**.
5. Copiar `dist-installer/Purimatic-Setup.exe` a una USB.

---

## 1. Instalar el software en la computadora de la tienda

1. Ejecutar `Purimatic-Setup.exe` (no pide administrador).
2. Dejar marcada la opción **Iniciar Purimatic al iniciar sesión de Windows**.
3. Al final, marcar ambas opciones de inicio:
   - **Iniciar puente NFC y ESP32**
   - **Iniciar Purimatic y configurar MongoDB Atlas de esta tienda**
4. Se instala en `%LOCALAPPDATA%\Purimatic` (ejemplo: `C:\Users\TIENDA\AppData\Local\Purimatic`).

Si Windows pide permiso de red (firewall) para Python/Purimatic, aceptar **redes privadas**.

---

## 2. Configurar MongoDB Atlas de ESTA tienda

Cada tienda tiene **otro** clúster / otra URI. Si se pega la URI de otra sucursal, la app arranca pero muestra datos ajenos o no conecta.

### 2.1 En MongoDB Atlas (cuenta de esta tienda)

1. Entrar a [https://cloud.mongodb.com](https://cloud.mongodb.com) con la cuenta de **esta** sucursal.
2. **Database Access**: crear un usuario con contraseña. Si la contraseña tiene `@ : / # ?`, hay que usar la versión URL-encoded (`@` → `%40`).
3. **Network Access**: agregar la IP pública de la tienda, o `0.0.0.0/0` si la IP cambia seguido (cualquier IP).
4. Confirmar que el clúster **no esté pausado**.
5. **Connect → Drivers**: copiar la URI completa. Debe verse así:

```
mongodb+srv://USUARIO:PASSWORD@clusterXXXX.mongodb.net/?retryWrites=true&w=majority
```

El asistente le pone solo el nombre de la base (por defecto `lavanderia_purimatic`).

### 2.2 En la computadora de la tienda

Al primer arranque se abre **Purimatic — Configurar esta tienda**:

1. Pegar la URI de Atlas.
2. Nombre de la base: `lavanderia_purimatic` (o el que use esta tienda).
3. Pulsar **Probar conexión**. Tiene que decir "Conexión correcta".
4. Pulsar **Guardar y continuar**.

El archivo se guarda junto al ejecutable:

`%LOCALAPPDATA%\Purimatic\.env`

Ahí queda `MONGODB_URI` y `ESP32_BRIDGE_URL=http://localhost:5001`.

### Si falla la conexión (lo más frecuente)

| Mensaje | Qué revisar |
|---|---|
| URI mal formada | Copiar otra vez desde Atlas → Connect → Drivers. Completa, con `mongodb+srv://`. |
| Atlas rechazó usuario o contraseña | Database Access: usuario, password, y que tenga permisos sobre la base. |
| No se pudo contactar el clúster | 1) Internet de esa PC. 2) Network Access: IP de la tienda o `0.0.0.0/0`. 3) El clúster no está pausado. |

Para reabrir el asistente: menú Inicio → **Lavanderia Purimatic → Reconfigurar MongoDB Atlas** (o ejecutar `Purimatic.exe --setup`).

---

## 3. Emparejar cada placa ESP32 (trabajo físico en la tienda)

Cada lavadora/secadora tiene un módulo ESP32. Hay que meterlo a la red WiFi **de la tienda** y anotar la IP que le da el router.

Contraseña de la red que emite la placa (modo configuración): **`setup123456`**

Página de configuración de la placa: **`http://192.168.4.1`**

### 3.1 Conectar el celular o laptop a la placa

1. Encender el ESP32 (la máquina / el módulo).
2. En el celular o laptop, abrir WiFi. Debe aparecer una red del ESP32 (Access Point).
3. Conectarse a esa red. Contraseña: `setup123456`.
4. El teléfono puede avisar "sin internet": es normal, no volver al WiFi de la tienda todavía.
5. En el navegador abrir: `http://192.168.4.1`

### 3.2 Decirle a la placa cuál es el WiFi de la tienda

1. En esa página, escribir el **nombre (SSID)** y la **contraseña** del WiFi de la sucursal (el mismo que usa la PC de la caja).
2. Guardar. La placa se reinicia y se une a esa red.
3. Volver a conectar el celular al WiFi de la tienda.

### 3.3 Anotar la IP local de esa placa

La placa queda con una IP del router de la tienda, por ejemplo `192.168.1.76`.

Formas de verla:

- En la página de la placa, si la muestra después de conectar.
- En el router (lista de clientes DHCP), buscando el ESP32.
- En algunos firmwares, al reconectarse un momento al AP de la placa.

La URL que usa Purimatic siempre es:

```
http://IP_DE_LA_PLACA/laundry-update
```

Ejemplo: `http://192.168.1.76/laundry-update`

**Importante:** esa IP debe ser de la **misma red** que la PC de la caja. Si el router reasigna IPs, conviene reservar esa IP en el DHCP del router (IP fija por MAC).

Repetir 3.1–3.3 por cada máquina.

---

## 4. Registrar la placa en el sistema

1. Abre `http://localhost:5000`, entra como admin.
2. Dashboard → **Placas ESP32** (o el botón del encabezado).
3. Escribe el `esp32_id` (ejemplo `76`) y la URL `http://192.168.1.76/laundry-update`.
4. Guardar placa.
5. Pulsa **Encender** y **Apagar** para probar el relé **sin hacer una venta**. La consola de PurimaticNFC debe mostrar el POST a esa IP.

El `esp32_id` es el identificador de esa placa. **El mismo valor** hay que ponerlo después en Equipo (lavadora o secadora).

Si prefieres Postman:

```
POST http://localhost:5000/api/esp32-config
Authorization: Bearer <token>

{ "esp32_id": "76", "esp32_url": "http://192.168.1.76/laundry-update", "is_active": true }
```

Prueba de relé:

```
POST http://localhost:5000/api/esp32-config/76/test
{ "action": "start" }
```

`action` puede ser `start` o `stop`.

---

## 5. Vincular la lavadora lógica (`washers`) con esa placa

1. Dashboard → **Equipo**.
2. Crear o editar la lavadora/secadora y poner el **mismo** `esp32_id` (ejemplo `76`).

Si `esp32_id` de la máquina no coincide con el de Placas ESP32, la venta se guarda pero **la máquina física no prende**.

### Cómo se conectan las piezas

```
Venta / botón Encender
    → washers.esp32_id  (ej. "76")
    → esp32_config.esp32_url  (ej. http://192.168.1.76/laundry-update)
    → API (puerto 5000) llama POST http://localhost:5001/send-to-esp32
    → nfc-service hace POST a la placa
    → el relé enciende la lavadora
```

---

## 6. Verificar que todo funciona

1. Confirmar que hay **dos ventanas de consola**:
   - Purimatic abre el navegador en `http://127.0.0.1:5000` (login)
   - PurimaticNFC en puerto `5001`
2. Login de admin → Placas ESP32 → Encender / Apagar.
3. Lector NFC: si hay ACR122U por USB, `GET http://localhost:5001/health` debe responder bien.
4. En Ventas, activar un servicio en esa lavadora y confirmar que prende igual que la prueba.

### Si la venta se guarda pero la máquina no prende

1. ¿Está corriendo PurimaticNFC? Sin el puerto 5001 la API no llega a la placa.
2. En Placas ESP32, ¿la URL es `http://IP/laundry-update` y está activa?
3. ¿El `esp32_id` de Equipo coincide exactamente? (`"76"` y `"W002"` son distintos.)
4. Desde la PC de la caja, abre `http://192.168.1.76/` o haz ping. Si no responde, la placa no está en esa red o cambió la IP.
5. PC y ESP32 deben estar en el **mismo WiFi**.

---

## Resumen rápido para el técnico en sitio

1. Instalar `Purimatic-Setup.exe`.
2. Pegar la URI de Atlas de **esta** tienda y **Probar conexión** / **Guardar**. Se abre `http://localhost:5000`.
3. Por cada máquina: WiFi de la placa → contraseña `setup123456` → `http://192.168.4.1` → SSID de la tienda → anotar IP.
4. Admin → Placas ESP32 → guardar `esp32_id` + `http://IP/laundry-update` → Encender/Apagar.
5. Equipo → el **mismo** `esp32_id` en la lavadora.
6. Probar una venta.

