# Guía de Compatibilidad entre Máquinas y Ciclos de Servicio

## Problema Resuelto

El sistema tenía una inconsistencia entre cómo se definían los tipos de máquinas y cómo los ciclos de servicio especificaban qué máquinas podían usar cada ciclo.

### Antes del Cambio:
- **Máquinas**: Solo tenían campos como `numero`, `marca`, `capacidad`, `estado`, `store_id`
- **Ciclos**: Tenían `machine_types_allowed` con valores como `['chica', 'grande', 'secadora']`
- **Problema**: No había forma de determinar si una máquina específica era compatible con un ciclo

### Después del Cambio:
- **Máquinas**: Ahora incluyen un campo calculado `machine_type` en las respuestas
- **Compatibilidad**: Sistema completo para validar y obtener ciclos compatibles
- **Utilidades**: Funciones centralizadas para manejar la lógica de compatibilidad

## Clasificación de Máquinas

### Lavadoras
- **Chica**: Capacidad ≤ 10.0 kg → `machine_type: 'chica'`
- **Grande**: Capacidad > 10.0 kg → `machine_type: 'grande'`

### Secadoras
- **Secadora**: Cualquier capacidad → `machine_type: 'secadora'`

## Compatibilidad por Tipo de Servicio

### Lavado
- **Máquinas compatibles**: `['chica', 'grande']`
- **Descripción**: Solo lavadoras

### Secado
- **Máquinas compatibles**: `['secadora']`
- **Descripción**: Solo secadoras

### Combo
- **Máquinas compatibles**: `['chica', 'grande', 'secadora']`
- **Descripción**: Lavadoras y secadoras

## Ejemplo de Datos

### Lavadora (14.0 kg de capacidad)
```json
{
  "_id": "6866d5a814f19bf5e0dd6c47",
  "numero": 5,
  "store_id": "store_001",
  "capacidad": 14.0,
  "estado": "ocupada",
  "is_active": true,
  "marca": "Bosch",
  "machine_type": "grande"
}
```

### Secadora (14.0 kg de capacidad)
```json
{
  "_id": "6866d5e814f19bf5e0dd6c4a",
  "store_id": "store_001",
  "numero": 4,
  "capacidad": 14.0,
  "estado": "mantenimiento",
  "is_active": true,
  "marca": "Bosch",
  "machine_type": "secadora"
}
```

### Ciclo de Servicio
```json
{
  "name": "Lavado Grande",
  "service_type": "lavado",
  "duration_minutes": 45,
  "price": 35.00,
  "machine_types_allowed": ["grande"],
  "is_active": true
}
```

## Nuevas APIs

### Para Lavadoras

#### Obtener Ciclos Compatibles
```
GET /api/washers/{washer_id}/compatible-cycles
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Ciclos compatibles obtenidos exitosamente",
  "data": {
    "washer_id": "6866d5a814f19bf5e0dd6c47",
    "machine_type": "grande",
    "compatible_cycles": [
      {
        "name": "Lavado Grande",
        "service_type": "lavado",
        "duration_minutes": 45,
        "price": 35.00,
        "machine_types_allowed": ["grande"]
      }
    ],
    "total_compatible": 1
  }
}
```

#### Validar Compatibilidad
```
GET /api/washers/{washer_id}/validate-cycle/{cycle_id}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Validación completada",
  "data": {
    "valid": true,
    "message": "Ciclo compatible con la máquina",
    "machine_type": "grande",
    "allowed_types": ["grande"]
  }
}
```

### Para Secadoras

#### Obtener Ciclos Compatibles
```
GET /api/dryers/{dryer_id}/compatible-cycles
```

#### Validar Compatibilidad
```
GET /api/dryers/{dryer_id}/validate-cycle/{cycle_id}
```

### Información de Clasificación

#### Obtener Información de Clasificación
```
GET /api/service-cycles/machine-classification
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Información de clasificación de máquinas obtenida exitosamente",
  "data": {
    "washer_types": {
      "chica": {
        "description": "Lavadora chica",
        "capacity_range": "5.0 - 10.0 kg",
        "condition": "capacidad <= 10.0"
      },
      "grande": {
        "description": "Lavadora grande",
        "capacity_range": "10.1+ kg",
        "condition": "capacidad > 10.0"
      }
    },
    "dryer_types": {
      "secadora": {
        "description": "Secadora estándar",
        "capacity_range": "Cualquier capacidad",
        "condition": "Siempre secadora"
      }
    },
    "service_types": {
      "lavado": {
        "compatible_machines": ["chica", "grande"],
        "description": "Solo lavadoras"
      },
      "secado": {
        "compatible_machines": ["secadora"],
        "description": "Solo secadoras"
      },
      "combo": {
        "compatible_machines": ["chica", "grande", "secadora"],
        "description": "Lavadoras y secadoras"
      }
    }
  }
}
```

## Archivos Modificados

### Nuevos Archivos
- `app/utils/machine_utils.py` - Utilidades para compatibilidad de máquinas

### Archivos Modificados
- `app/schemas/washer_schema.py` - Agregado campo `machine_type` calculado
- `app/schemas/dryer_schema.py` - Agregado campo `machine_type` calculado
- `app/services/washer_service.py` - Agregados métodos de compatibilidad
- `app/services/dryer_service.py` - Agregados métodos de compatibilidad
- `app/routes/washer_routes.py` - Agregadas rutas de compatibilidad
- `app/routes/dryer_routes.py` - Agregadas rutas de compatibilidad
- `app/routes/service_cycle_routes.py` - Agregada ruta de clasificación

## Uso en el Frontend

Ahora puedes:

1. **Obtener máquinas con su tipo**: Las respuestas incluyen `machine_type`
2. **Validar antes de crear servicios**: Verificar si un ciclo es compatible con una máquina
3. **Mostrar solo ciclos compatibles**: Filtrar ciclos según la máquina seleccionada
4. **Informar al usuario**: Mostrar por qué un ciclo no es compatible

## Ejemplo de Flujo de Trabajo

1. Usuario selecciona una máquina
2. Sistema determina el tipo de máquina basándose en la capacidad
3. Sistema obtiene ciclos compatibles con esa máquina
4. Usuario selecciona un ciclo de la lista filtrada
5. Sistema valida la compatibilidad antes de crear el servicio 