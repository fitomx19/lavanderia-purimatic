// ========================================
// EJEMPLOS DE TRANSACCIONES PARA MONGODB
// ========================================
// Copiar y pegar estos documentos en MongoDB Compass o mongo shell
// para probar el sistema de registro de transacciones de tarjetas

// NOTA: Reemplaza los IDs de ejemplo con IDs reales de tu base de datos:
// - card_id: ID de una tarjeta existente en la colección 'cards'
// - employee_id: ID de un empleado existente en la colección 'user_employees'
// - sale_id: ID de una venta existente en la colección 'sales' (solo para pago_venta)

// ========================================
// EJEMPLO 1: RECARGA MANUAL
// ========================================
// Transacción generada cuando un empleado recarga saldo manualmente a una tarjeta
{
  "card_id": "507f1f77bcf86cd799439011",  // Reemplazar con ID real de tarjeta
  "amount": 100.00,
  "transaction_type": "recarga_manual",
  "balance_before": 50.00,
  "balance_after": 150.00,
  "employee_id": "507f1f77bcf86cd799439012",  // Reemplazar con ID real de empleado
  "related_card_id": null,
  "sale_id": null,
  "notes": "",
  "created_at": new Date("2025-10-20T10:30:00.000Z"),
  "updated_at": new Date("2025-10-20T10:30:00.000Z")
}

// ========================================
// EJEMPLO 2: PAGO EN VENTA CON NFC
// ========================================
// Transacción generada cuando un cliente paga con su tarjeta NFC en el punto de venta
{
  "card_id": "507f1f77bcf86cd799439011",  // Reemplazar con ID real de tarjeta
  "amount": 35.50,
  "transaction_type": "pago_venta",
  "balance_before": 150.00,
  "balance_after": 114.50,
  "employee_id": "507f1f77bcf86cd799439012",  // Reemplazar con ID real de empleado
  "related_card_id": null,
  "sale_id": "507f1f77bcf86cd799439013",  // Reemplazar con ID real de venta
  "notes": "Pago en venta con NFC",
  "created_at": new Date("2025-10-20T14:15:30.000Z"),
  "updated_at": new Date("2025-10-20T14:15:30.000Z")
}

// ========================================
// EJEMPLO 3: TRANSFERENCIA ENTRE TARJETAS
// ========================================
// Dos transacciones generadas cuando se transfiere saldo entre tarjetas del mismo cliente

// Transacción 3A: Salida de la tarjeta origen (transferencia_out)
{
  "card_id": "507f1f77bcf86cd799439011",  // ID de tarjeta ORIGEN
  "amount": 25.00,
  "transaction_type": "transferencia_out",
  "balance_before": 114.50,
  "balance_after": 89.50,
  "employee_id": "507f1f77bcf86cd799439012",  // Reemplazar con ID real de empleado
  "related_card_id": "507f1f77bcf86cd799439014",  // ID de tarjeta DESTINO
  "sale_id": null,
  "notes": "Transferencia a tarjeta 123456789012",
  "created_at": new Date("2025-10-20T16:45:00.000Z"),
  "updated_at": new Date("2025-10-20T16:45:00.000Z")
}

// Transacción 3B: Entrada a la tarjeta destino (transferencia_in)
{
  "card_id": "507f1f77bcf86cd799439014",  // ID de tarjeta DESTINO
  "amount": 25.00,
  "transaction_type": "transferencia_in",
  "balance_before": 20.00,
  "balance_after": 45.00,
  "employee_id": "507f1f77bcf86cd799439012",  // Reemplazar con ID real de empleado
  "related_card_id": "507f1f77bcf86cd799439011",  // ID de tarjeta ORIGEN
  "sale_id": null,
  "notes": "Transferencia desde tarjeta 987654321098",
  "created_at": new Date("2025-10-20T16:45:00.000Z"),
  "updated_at": new Date("2025-10-20T16:45:00.000Z")
}

// ========================================
// CONSULTAS ÚTILES PARA REPORTES
// ========================================

// 1. Ver todas las transacciones de una tarjeta específica (ordenadas por fecha)
db.card_transactions.find({
  "card_id": "507f1f77bcf86cd799439011"  // Reemplazar con ID real
}).sort({ "created_at": -1 })

// 2. Calcular total de recargas del mes actual
db.card_transactions.aggregate([
  {
    $match: {
      "transaction_type": { $in: ["recarga_manual", "recarga_nfc"] },
      "created_at": {
        $gte: new Date("2025-10-01T00:00:00.000Z"),
        $lt: new Date("2025-11-01T00:00:00.000Z")
      }
    }
  },
  {
    $group: {
      _id: "$transaction_type",
      total: { $sum: "$amount" },
      count: { $sum: 1 }
    }
  }
])

// 3. Ver transacciones realizadas por un empleado específico
db.card_transactions.find({
  "employee_id": "507f1f77bcf86cd799439012"  // Reemplazar con ID real
}).sort({ "created_at": -1 }).limit(50)

// 4. Obtener resumen diario de ingresos por recargas (para control de caja)
db.card_transactions.aggregate([
  {
    $match: {
      "transaction_type": { $in: ["recarga_manual", "recarga_nfc", "saldo_inicial"] }
    }
  },
  {
    $group: {
      _id: {
        $dateToString: { format: "%Y-%m-%d", date: "$created_at" }
      },
      total_ingresos: { $sum: "$amount" },
      num_transacciones: { $sum: 1 }
    }
  },
  {
    $sort: { "_id": -1 }
  }
])

// 5. Ver todas las transferencias entre tarjetas
db.card_transactions.find({
  "transaction_type": { $in: ["transferencia_out", "transferencia_in"] }
}).sort({ "created_at": -1 })

// ========================================
// TIPOS DE TRANSACCIONES DISPONIBLES
// ========================================
/*
1. saldo_inicial      - Saldo inicial al crear una tarjeta nueva
2. recarga_manual     - Recarga de saldo manual por empleado (operación "add")
3. recarga_nfc        - Recarga de saldo usando lector NFC
4. pago_venta         - Pago de productos/servicios en punto de venta con NFC
5. transferencia_out  - Salida de saldo por transferencia a otra tarjeta
6. transferencia_in   - Entrada de saldo por transferencia desde otra tarjeta
7. ajuste_manual      - Ajuste/reducción manual de saldo por empleado (operación "subtract")
*/

// ========================================
// INSTRUCCIONES DE USO
// ========================================
/*
1. Abre MongoDB Compass o conecta a tu base de datos MongoDB
2. Selecciona tu base de datos (ej: lavanderia_db)
3. Ve a la colección "card_transactions"
4. Haz clic en "INSERT DOCUMENT"
5. Copia y pega uno de los ejemplos de arriba
6. IMPORTANTE: Reemplaza los IDs de ejemplo con IDs reales de tu base de datos
7. Haz clic en "Insert"

Para obtener IDs reales de tu base de datos:
- Tarjetas: db.cards.find({}, {_id: 1, card_number: 1})
- Empleados: db.user_employees.find({}, {_id: 1, username: 1})
- Ventas: db.sales.find({}, {_id: 1}).sort({created_at: -1}).limit(5)
*/

