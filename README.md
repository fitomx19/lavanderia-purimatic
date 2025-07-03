# Lavandería Purimatic - MVP Backend

Sistema de gestión integral para lavandería con arquitectura Full Stack usando Python Flask + MongoDB Atlas.

## 🏗️ Arquitectura

El proyecto sigue el patrón arquitectónico **Ruta → Servicio → Repositorio**:

- **Rutas**: Endpoints HTTP que manejan requests/responses
- **Servicios**: Lógica de negocio y validaciones
- **Repositorios**: Operaciones de base de datos con patrón UPSERT

## 🚀 Características

### Funcionalidades Principales
- ✅ Sistema de autenticación JWT con roles (admin/empleado)
- ✅ Gestión de empleados con control de acceso
- ✅ Gestión de clientes con tarjetas recargables
- ✅ Inventario de productos con control de stock
- ✅ Gestión de lavadoras y secadoras por tienda
- ✅ Operaciones UPSERT en todos los módulos
- ✅ Paginación en listados grandes
- ✅ Respuestas JSON estandarizadas
- ✅ Manejo centralizado de errores
- ✅ Validación con Marshmallow schemas

### Tecnologías
- **Backend**: Flask 2.3.3
- **Base de Datos**: MongoDB Atlas
- **Autenticación**: JWT (Flask-JWT-Extended 4.5.3)
- **ORM/ODM**: PyMongo 4.5.0
- **Validación**: Marshmallow 3.20.1
- **Seguridad**: Bcrypt 4.0.1
- **CORS**: Flask-CORS 4.0.0

## 📊 Entidades del Sistema

### 1. Usuarios Empleados
- username, email, password_hash, role, store_id
- Roles: admin, empleado
- Autenticación JWT

### 2. Usuarios Clientes
- nombre, telefono, email, saldo_tarjeta_recargable
- Sistema de tarjeta recargable con operaciones

### 3. Productos
- nombre, descripcion, precio, tipo, stock
- Tipos: jabon, bolsas, suavizante, quitamanchas, blanqueador
- Control de stock con operaciones (agregar, reducir, establecer)

### 4. Lavadoras/Secadoras
- numero, marca, capacidad, estado, store_id
- Estados: disponible, ocupada, mantenimiento
- Gestión por tienda

### 5. Tiendas
- nombre, direccion, telefono, email, gerente, horario

## 🛠️ Instalación y Configuración

### Prerequisitos
- Python 3.8+
- MongoDB Atlas (cuenta gratuita)
- Git

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd lavanderia-purimatic
```

### 2. Crear Entorno Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
# Configuración del entorno
FLASK_ENV=development
FLASK_DEBUG=True

# MongoDB Atlas - Reemplazar con tu URI real
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/lavanderia_purimatic?retryWrites=true&w=majority

# JWT - Generar claves seguras para producción
JWT_SECRET_KEY=tu-clave-secreta-jwt-aqui
JWT_ACCESS_TOKEN_EXPIRES=86400

# Flask
SECRET_KEY=tu-clave-secreta-flask-aqui

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Configuración del servidor
PORT=5000
HOST=0.0.0.0

# Configuración adicional
BCRYPT_LOG_ROUNDS=12
DEFAULT_PAGE_SIZE=10
MAX_PAGE_SIZE=100
```

### 5. Configurar MongoDB Atlas

1. Crear cuenta gratuita en [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Crear cluster gratuito
3. Configurar usuario de base de datos
4. Obtener URI de conexión
5. Actualizar `MONGODB_URI` en el archivo `.env`

### 6. Cargar Datos de Prueba
```bash
python tests/test_data.py
```

### 7. Ejecutar la Aplicación
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

## 📚 API Endpoints

### Autenticación
```
POST   /auth/login           - Login de empleado
POST   /auth/logout          - Logout
GET    /auth/verify          - Verificar token
PUT    /auth/change-password - Cambiar contraseña
GET    /auth/profile         - Obtener perfil
```

### Empleados (Requiere autenticación)
```
POST   /employees/              - Crear empleado (solo admin)
GET    /employees/              - Listar empleados
GET    /employees/{id}          - Obtener empleado
PUT    /employees/{id}          - Actualizar empleado (solo admin)
DELETE /employees/{id}          - Eliminar empleado (solo admin)
GET    /employees/store/{id}    - Empleados por tienda
GET    /employees/current       - Datos del empleado actual
PUT    /employees/current       - Actualizar datos propios
```

### Clientes (Requiere autenticación)
```
POST   /clients/                - Crear cliente
GET    /clients/                - Listar clientes
GET    /clients/{id}            - Obtener cliente
PUT    /clients/{id}            - Actualizar cliente
DELETE /clients/{id}            - Eliminar cliente
PUT    /clients/{id}/balance    - Actualizar saldo de tarjeta
GET    /clients/search          - Buscar clientes
```

### Productos (Requiere autenticación)
```
POST   /products/               - Crear producto
GET    /products/               - Listar productos
GET    /products/{id}           - Obtener producto
PUT    /products/{id}           - Actualizar producto
DELETE /products/{id}           - Eliminar producto
PUT    /products/{id}/stock     - Actualizar stock
GET    /products/low-stock      - Productos con stock bajo
GET    /products/search         - Buscar productos
```

### Lavadoras (Requiere autenticación)
```
POST   /washers/                      - Crear lavadora
GET    /washers/?store_id={id}        - Listar lavadoras por tienda
GET    /washers/{id}                  - Obtener lavadora
PUT    /washers/{id}                  - Actualizar lavadora
DELETE /washers/{id}                  - Eliminar lavadora
PUT    /washers/{id}/status           - Actualizar estado
GET    /washers/store/{id}            - Lavadoras por tienda
GET    /washers/store/{id}/available  - Lavadoras disponibles
GET    /washers/store/{id}/statistics - Estadísticas por tienda
```

### Secadoras (Requiere autenticación)
```
POST   /dryers/                      - Crear secadora
GET    /dryers/?store_id={id}        - Listar secadoras por tienda
GET    /dryers/{id}                  - Obtener secadora
PUT    /dryers/{id}                  - Actualizar secadora
DELETE /dryers/{id}                  - Eliminar secadora
PUT    /dryers/{id}/status           - Actualizar estado
GET    /dryers/store/{id}            - Secadoras por tienda
GET    /dryers/store/{id}/available  - Secadoras disponibles
GET    /dryers/store/{id}/statistics - Estadísticas por tienda
```

## 🔐 Autenticación

### Usuarios de Prueba
```
Admin:
  username: admin
  password: AdminPurimatic2024!

Empleado Centro:
  username: empleado_centro
  password: Empleado123!

Empleado Norte:
  username: empleado_norte
  password: Empleado123!
```

### Uso de Tokens JWT
```bash
# 1. Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "AdminPurimatic2024!"}'

# 2. Usar token en requests
curl -X GET http://localhost:5000/employees/ \
  -H "Authorization: Bearer <tu-token-aqui>"
```

## 📝 Ejemplos de Uso

### Crear Cliente
```bash
curl -X POST http://localhost:5000/clients/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "telefono": "+58-412-5555555",
    "email": "juan.perez@email.com",
    "saldo_tarjeta_recargable": 25.00
  }'
```

### Actualizar Stock de Producto
```bash
curl -X PUT http://localhost:5000/products/{product_id}/stock \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10,
    "operation": "agregar"
  }'
```

### Cambiar Estado de Lavadora
```bash
curl -X PUT http://localhost:5000/washers/{washer_id}/status \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "ocupada"
  }'
```

## 🏗️ Estructura del Proyecto

```
lavanderia-purimatic/
├── app/
│   ├── __init__.py              # Factory pattern y configuración
│   ├── repositories/            # Capa de datos
│   │   ├── base_repository.py   # Repositorio base con UPSERT
│   │   ├── user_employee_repository.py
│   │   ├── user_client_repository.py
│   │   ├── product_repository.py
│   │   ├── washer_repository.py
│   │   ├── dryer_repository.py
│   │   └── store_repository.py
│   ├── services/                # Lógica de negocio
│   │   ├── auth_service.py
│   │   ├── employee_service.py
│   │   ├── client_service.py
│   │   ├── product_service.py
│   │   ├── washer_service.py
│   │   └── dryer_service.py
│   ├── routes/                  # Endpoints HTTP
│   │   ├── auth_routes.py
│   │   ├── employee_routes.py
│   │   ├── client_routes.py
│   │   ├── product_routes.py
│   │   ├── washer_routes.py
│   │   └── dryer_routes.py
│   ├── schemas/                 # Validación con Marshmallow
│   │   ├── user_employee_schema.py
│   │   ├── user_client_schema.py
│   │   ├── product_schema.py
│   │   ├── washer_schema.py
│   │   └── dryer_schema.py
│   └── utils/                   # Utilidades
│       ├── auth_utils.py        # JWT y autenticación
│       ├── response_utils.py    # Respuestas estandarizadas
│       └── validation_utils.py  # Validaciones personalizadas
├── tests/
│   └── test_data.py            # Datos de prueba
├── config.py                   # Configuración de la app
├── run.py                      # Punto de entrada
├── requirements.txt            # Dependencias
└── README.md                   # Documentación
```

## 🔧 Próximas Mejoras

- [ ] Frontend React/Vue.js
- [ ] Sistema de órdenes/tickets de lavado
- [ ] Reportes y analytics
- [ ] Notificaciones en tiempo real
- [ ] Sistema de pagos
- [ ] API para app móvil
- [ ] Docker containerization
- [ ] Testing automatizado
- [ ] CI/CD pipeline
- [ ] Logs estructurados

## 🐛 Troubleshooting

### Error de Conexión a MongoDB
- Verificar URI de MongoDB Atlas
- Revisar configuración de red en Atlas
- Confirmar credenciales de usuario

### Error de JWT Token
- Verificar configuración de JWT_SECRET_KEY
- Confirmar que el token no ha expirado
- Revisar formato del header Authorization

### Error de Importación
- Activar entorno virtual
- Reinstalar dependencias: `pip install -r requirements.txt`
- Verificar versión de Python (3.8+)

## 📄 Licencia

Este proyecto es desarrollado para Lavandería Purimatic.

## 👥 Contacto

Para soporte técnico o consultas sobre el sistema, contactar al equipo de desarrollo. 