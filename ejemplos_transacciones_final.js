// ========================================
// EJEMPLOS DE TRANSACCIONES PARA MONGODB - VERSION FINAL
// ========================================
// Copiar y pegar estos documentos en MongoDB Compass o mongo shell
// para probar el sistema de registro de transacciones de tarjetas

// IDs reales utilizados:
// - Tarjeta 1: 6866df6054802d62f0032d31
// - Tarjeta 2: 6866e10354802d62f0032d45
// - Empleado: 6866ced114f19bf5e0dd6bf5

// ========================================
// EJEMPLO 1: RECARGA MANUAL DE $100
// ========================================
{
  "card_id": "6866df6054802d62f0032d31",
  "amount": 100.00,
  "transaction_type": "recarga_manual",
  "balance_before": 93.00,
  "balance_after": 193.00,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": null,
  "sale_id": null,
  "notes": "Recarga manual de saldo",
  "created_at": {
    "$date": "2025-10-20T10:30:00.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T10:30:00.000Z"
  }
}

// ========================================
// EJEMPLO 2: PAGO EN VENTA DE $45.50
// ========================================
{
  "card_id": "6866df6054802d62f0032d31",
  "amount": 45.50,
  "transaction_type": "pago_venta",
  "balance_before": 193.00,
  "balance_after": 147.50,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": null,
  "sale_id": "TU_SALE_ID_AQUI",
  "notes": "Pago en venta con NFC - UID: 91AC001E",
  "created_at": {
    "$date": "2025-10-20T14:15:30.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T14:15:30.000Z"
  }
}

// ========================================
// EJEMPLO 3: TRANSFERENCIA DE $50 ENTRE TARJETAS
// ========================================

// 3A: Salida de la tarjeta origen
{
  "card_id": "6866df6054802d62f0032d31",
  "amount": 50.00,
  "transaction_type": "transferencia_out",
  "balance_before": 147.50,
  "balance_after": 97.50,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": "6866e10354802d62f0032d45",
  "sale_id": null,
  "notes": "Transferencia a tarjeta 970610607166",
  "created_at": {
    "$date": "2025-10-20T16:45:00.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T16:45:00.000Z"
  }
}

// 3B: Entrada a la tarjeta destino
{
  "card_id": "6866e10354802d62f0032d45",
  "amount": 50.00,
  "transaction_type": "transferencia_in",
  "balance_before": 130.00,
  "balance_after": 180.00,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": "6866df6054802d62f0032d31",
  "sale_id": null,
  "notes": "Transferencia desde tarjeta 412174099687",
  "created_at": {
    "$date": "2025-10-20T16:45:00.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T16:45:00.000Z"
  }
}

// ========================================
// EJEMPLO 4: RECARGA NFC DE $75
// ========================================
{
  "card_id": "6866e10354802d62f0032d45",
  "amount": 75.00,
  "transaction_type": "recarga_nfc",
  "balance_before": 180.00,
  "balance_after": 255.00,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": null,
  "sale_id": null,
  "notes": "Recarga via NFC - UID: 2761011E",
  "created_at": {
    "$date": "2025-10-20T17:30:00.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T17:30:00.000Z"
  }
}

// ========================================
// EJEMPLO 5: AJUSTE MANUAL DE -$20
// ========================================
{
  "card_id": "6866df6054802d62f0032d31",
  "amount": 20.00,
  "transaction_type": "ajuste_manual",
  "balance_before": 97.50,
  "balance_after": 77.50,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": null,
  "sale_id": null,
  "notes": "Ajuste manual: reducción de saldo",
  "created_at": {
    "$date": "2025-10-20T18:00:00.000Z"
  },
  "updated_at": {
    "$date": "2025-10-20T18:00:00.000Z"
  }
}

// ========================================
// EJEMPLO 6: SALDO INICIAL DE $50
// ========================================
{
  "card_id": "6866df6054802d62f0032d31",
  "amount": 50.00,
  "transaction_type": "saldo_inicial",
  "balance_before": 0.00,
  "balance_after": 50.00,
  "employee_id": "6866ced114f19bf5e0dd6bf5",
  "related_card_id": null,
  "sale_id": null,
  "notes": "Saldo inicial al crear tarjeta",
  "created_at": {
    "$date": "2025-10-15T05:03:54.459Z"
  },
  "updated_at": {
    "$date": "2025-10-15T05:03:54.459Z"
  }
}

// ========================================
// CONSULTAS ÚTILES PARA VERIFICAR
// ========================================

// Ver todas las transacciones de la tarjeta 412174099687
db.card_transactions.find({
  "card_id": "6866df6054802d62f0032d31"
}).sort({ "created_at": -1 })

// Ver todas las transacciones de la tarjeta 970610607166
db.card_transactions.find({
  "card_id": "6866e10354802d62f0032d45"
}).sort({ "created_at": -1 })

// Ver solo las transferencias
db.card_transactions.find({
  "transaction_type": { $in: ["transferencia_out", "transferencia_in"] }
}).sort({ "created_at": -1 })

// Calcular total de ingresos por recargas este mes
db.card_transactions.aggregate([
  {
    $match: {
      "transaction_type": { $in: ["recarga_manual", "recarga_nfc", "saldo_inicial"] },
      "created_at": {
        $gte: new Date("2025-10-01"),
        $lt: new Date("2025-11-01")
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

// Ver transacciones realizadas por un empleado específico
db.card_transactions.find({
  "employee_id": "6866ced114f19bf5e0dd6bf5"
}).sort({ "created_at": -1 }).limit(20)

// ========================================
// INSTRUCCIONES PARA INSERTAR
// ========================================
/*
1. Abre MongoDB Compass
2. Conecta a tu base de datos de lavandería
3. Ve a la colección "card_transactions"
4. Haz clic en "ADD DATA" → "Insert Document"
5. Cambia el modo a "JSON" (arriba a la derecha)
6. Copia y pega CADA objeto JSON individualmente (uno por uno)
7. Haz clic en "Insert" para cada uno
8. NOTA: Si quieres insertar múltiples documentos a la vez,
   usa este array:

[
  {documento 1},
  {documento 2},
  ...
]

Pero MongoDB Compass limita la cantidad de documentos por inserción.
*/

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
// VERIFICACIÓN FINAL
// ========================================
/*
Después de insertar los documentos, verifica que todo funciona:

1. Ve al dashboard → Haz clic en "📊 Transacciones"
2. Deberías ver las transacciones en la tabla
3. Prueba los filtros: por tipo, por tarjeta, por fecha
4. La paginación debería funcionar
5. Los colores deberían indicar ingresos (verde) vs egresos (rojo)

¡Sistema completamente funcional! 🎉
*/
