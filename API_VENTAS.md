# API de Ventas - Documentación Completa

## Descripción General
La API de ventas permite gestionar todas las operaciones relacionadas con ventas de productos y servicios en la lavandería. Incluye funcionalidades para crear ventas, consultar historial, actualizar estados y obtener resúmenes.

## Autenticación
Todos los endpoints requieren autenticación JWT. Los empleados pueden acceder a la mayoría de funciones, mientras que los administradores tienen acceso completo.

## Endpoints Disponibles

### 1. Crear Venta
**POST** `/api/sales`

Crea una nueva venta con productos y/o servicios.

#### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

#### Estructura del Body (Simplificada)
```json
{
  "client_id": "client_id_opcional",
  "store_id": "store_001",
  "items": [
    {
      "product_id": "6866d53114f19bf5e0dd6c3f",
      "quantity": 2
    },
    {
      "service_cycle_id": "6866e3f854802d62f0032d6e",
      "machine_id": "6866d5a814f19bf5e0dd6c47"
    }
  ],
  "payment_methods": [
    {
      "payment_type": "efectivo",
      "amount": 56.00
    }
  ]
}
```

#### Campos Obligatorios
- `store_id`: ID de la tienda
- `items`: Lista de productos y/o servicios (mínimo 1)
- `payment_methods`: Lista de métodos de pago (mínimo 1)

#### Campos Opcionales
- `client_id`: ID del cliente (si es venta asociada)
- `employee_id`: Se asigna automáticamente al empleado actual
- `total_amount`: Se calcula automáticamente si no se proporciona

#### Tipos de Items

**Producto:**
```json
{
  "product_id": "ID_del_producto",
  "quantity": 2
}
```
- El sistema obtiene automáticamente el precio del producto
- Se calcula automáticamente el subtotal (precio × cantidad)
- Se valida el stock disponible

**Servicio:**
```json
{
  "service_cycle_id": "ID_del_ciclo_de_servicio",
  "machine_id": "ID_de_la_máquina"
}
```
- El sistema obtiene automáticamente el precio del ciclo
- Se valida la compatibilidad entre ciclo y máquina
- Se asigna automáticamente la duración del ciclo

#### Métodos de Pago
```json
{
  "payment_type": "efectivo|tarjeta_credito|tarjeta_recargable",
  "amount": 25.00,
  "card_id": "ID_tarjeta" // Solo para tarjeta_recargable
}
```

#### Respuesta Exitosa (201)
```json
{
  "success": true,
  "message": "Venta creada exitosamente",
  "data": {
    "_id": "sale_id_generado",
    "client_id": "client_id_opcional",
    "employee_id": "employee_id",
    "store_id": "store_001",
    "total_amount": 56.00,
    "items": {
      "products": [
        {
          "product_id": "6866d53114f19bf5e0dd6c3f",
          "quantity": 2,
          "unit_price": 15.50,
          "subtotal": 31.00
        }
      ],
      "services": [
        {
          "service_cycle_id": "6866e3f854802d62f0032d6e",
          "machine_id": "6866d5a814f19bf5e0dd6c47",
          "machine_type": "washer",
          "duration": 30,
          "price": 25.00,
          "status": "pending"
        }
      ]
    },
    "payment_methods": [
      {
        "payment_type": "efectivo",
        "amount": 56.00
      }
    ],
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Errores Comunes
- **400**: Datos inválidos, producto no encontrado, máquina no disponible
- **401**: Token inválido o expirado
- **403**: Permisos insuficientes

---

### 2. Listar Ventas
**GET** `/api/sales`

Obtiene una lista paginada de ventas con filtros opcionales.

#### Parámetros de Consulta
- `page`: Número de página (default: 1)
- `per_page`: Elementos por página (default: 10)
- `status`: Filtrar por estado (`pending`, `completed`, `cancelled`)
- `employee_id`: Filtrar por empleado
- `client_id`: Filtrar por cliente
- `today`: Filtrar ventas del día actual (`true`/`false`)

#### Ejemplos de Uso
```
GET /api/sales?page=1&per_page=20
GET /api/sales?status=pending
GET /api/sales?employee_id=emp_123&today=true
GET /api/sales?client_id=client_456
```

#### Respuesta Exitosa (200)
```json
{
  "success": true,
  "message": "Ventas obtenidas exitosamente",
  "data": [
    {
      "_id": "sale_id_1",
      "client_id": "client_123",
      "employee_id": "emp_456",
      "store_id": "store_001",
      "total_amount": 45.00,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T11:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "total_pages": 3
  }
}
```

---

### 3. Obtener Venta por ID
**GET** `/api/sales/{sale_id}`

Obtiene los detalles completos de una venta específica.

#### Respuesta Exitosa (200)
```json
{
  "success": true,
  "message": "Venta encontrada",
  "data": {
    "_id": "sale_id",
    "client_id": "client_123",
    "employee_id": "emp_456",
    "store_id": "store_001",
    "total_amount": 56.00,
    "items": {
      "products": [...],
      "services": [...]
    },
    "payment_methods": [...],
    "status": "completed",
    "created_at": "2024-01-15T10:30:00Z",
    "completed_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Errores
- **404**: Venta no encontrada

---

### 4. Actualizar Estado de Venta
**PUT** `/api/sales/{sale_id}/status`

Actualiza el estado de una venta específica.

#### Body
```json
{
  "status": "pending|completed|cancelled"
}
```

#### Respuesta Exitosa (200)
```json
{
  "success": true,
  "message": "Estado de venta actualizado a completed",
  "data": {
    "_id": "sale_id",
    "status": "completed",
    "completed_at": "2024-01-15T11:00:00Z"
  }
}
```

---

### 5. Completar Venta
**POST** `/api/sales/{sale_id}/complete`

Completa una venta y activa todos los servicios asociados.

#### Funcionalidad
- Cambia el estado de la venta a "completed"
- Activa todos los servicios (de "pending" a "active")
- Marca las máquinas como ocupadas
- Registra timestamps de activación

#### Respuesta Exitosa (200)
```json
{
  "success": true,
  "message": "Venta completada y servicios activados",
  "data": {
    "_id": "sale_id",
    "status": "completed",
    "completed_at": "2024-01-15T11:00:00Z",
    "items": {
      "services": [
        {
          "service_cycle_id": "cycle_123",
          "machine_id": "machine_456",
          "status": "active",
          "started_at": "2024-01-15T11:00:00Z"
        }
      ]
    }
  }
}
```

---

### 6. Resumen de Ventas (Solo Administradores)
**GET** `/api/sales/summary`

Obtiene un resumen estadístico de ventas por rango de fechas.

#### Parámetros Requeridos
- `start_date`: Fecha de inicio (YYYY-MM-DD)
- `end_date`: Fecha de fin (YYYY-MM-DD)

#### Ejemplo de Uso
```
GET /api/sales/summary?start_date=2024-01-01&end_date=2024-01-31
```

#### Respuesta Exitosa (200)
```json
{
  "success": true,
  "message": "Resumen de ventas obtenido exitosamente",
  "data": {
    "total_sales": 150,
    "total_amount": 7500.00,
    "by_status": {
      "completed": {
        "count": 120,
        "amount": 6800.00
      },
      "pending": {
        "count": 25,
        "amount": 650.00
      },
      "cancelled": {
        "count": 5,
        "amount": 50.00
      }
    }
  }
}
```

---

## Estados de Venta

### pending
- Venta creada pero no procesada
- Servicios en estado "pending"
- Máquinas aún no ocupadas

### completed
- Venta procesada exitosamente
- Servicios activados
- Máquinas ocupadas y funcionando

### cancelled
- Venta cancelada
- Servicios no se ejecutan
- Reembolsos procesados si aplica

---

## Estados de Servicio

### pending
- Servicio pagado pero no iniciado
- Máquina disponible para uso

### active
- Servicio en ejecución
- Máquina ocupada
- Timestamp de inicio registrado

### completed
- Servicio finalizado
- Máquina liberada
- Timestamp de finalización registrado

---

## Validaciones Automáticas

### Productos
- Existencia del producto
- Estado activo del producto
- Disponibilidad de stock
- Cálculo automático de precios

### Servicios
- Existencia del ciclo de servicio
- Disponibilidad de la máquina
- Compatibilidad ciclo-máquina
- Estado activo de la máquina

### Pagos
- Suma total coincide con monto de venta
- Saldo suficiente en tarjetas recargables
- Validación de métodos de pago

---

## Códigos de Error

| Código | Descripción |
|--------|-------------|
| 400 | Datos inválidos o reglas de negocio no cumplidas |
| 401 | Token de autenticación inválido o expirado |
| 403 | Permisos insuficientes para la operación |
| 404 | Recurso no encontrado |
| 500 | Error interno del servidor |

---

## Ejemplos de Uso Completos

### Venta Solo con Productos
```json
{
  "store_id": "store_001",
  "items": [
    {
      "product_id": "detergente_123",
      "quantity": 3
    },
    {
      "product_id": "suavizante_456",
      "quantity": 1
    }
  ],
  "payment_methods": [
    {
      "payment_type": "efectivo",
      "amount": 45.00
    }
  ]
}
```

### Venta Solo con Servicios
```json
{
  "store_id": "store_001",
  "items": [
    {
      "service_cycle_id": "lavado_normal_123",
      "machine_id": "lavadora_001"
    },
    {
      "service_cycle_id": "secado_normal_456",
      "machine_id": "secadora_001"
    }
  ],
  "payment_methods": [
    {
      "payment_type": "tarjeta_recargable",
      "amount": 50.00,
      "card_id": "card_789"
    }
  ]
}
```

### Venta Mixta con Múltiples Pagos
```json
{
  "client_id": "cliente_vip_123",
  "store_id": "store_001",
  "items": [
    {
      "product_id": "detergente_premium_123",
      "quantity": 2
    },
    {
      "service_cycle_id": "lavado_premium_456",
      "machine_id": "lavadora_premium_001"
    }
  ],
  "payment_methods": [
    {
      "payment_type": "tarjeta_recargable",
      "amount": 30.00,
      "card_id": "card_456"
    },
    {
      "payment_type": "efectivo",
      "amount": 25.00
    }
  ]
}
```

---

## Notas Importantes

1. **Cálculo Automático**: Los precios se obtienen automáticamente de la base de datos
2. **Validación en Tiempo Real**: Todas las validaciones se ejecutan antes de crear la venta
3. **Transacciones**: Los pagos con tarjeta se procesan inmediatamente
4. **Auditoría**: Todos los cambios de estado se registran con timestamps
5. **Permisos**: Empleados pueden crear y ver ventas, administradores tienen acceso completo 