from marshmallow import Schema, fields, validate, ValidationError

class CardTransactionSchema(Schema):
    """Schema para transacciones de tarjetas"""
    
    card_id = fields.Str(required=True)
    amount = fields.Float(required=True, validate=validate.Range(min=0))
    transaction_type = fields.Str(
        required=True,
        validate=validate.OneOf([
            'recarga_manual',
            'recarga_nfc',
            'pago_venta',
            'transferencia_out',
            'transferencia_in',
            'saldo_inicial',
            'ajuste_manual'
        ])
    )
    balance_before = fields.Float(required=True)
    balance_after = fields.Float(required=True)
    employee_id = fields.Str(required=True)
    related_card_id = fields.Str(required=False, allow_none=True)
    sale_id = fields.Str(required=False, allow_none=True)
    notes = fields.Str(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

# Instancias del schema
card_transaction_schema = CardTransactionSchema()
card_transactions_schema = CardTransactionSchema(many=True)

