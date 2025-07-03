from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Dict, Any
import re

class CardSchema(Schema):
    """
    Schema para validación de tarjetas recargables
    """
    
    _id = fields.Str(dump_only=True)
    client_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID del cliente es requerido'}
    )
    card_number = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=16),
        error_messages={'required': 'El número de tarjeta es requerido'}
    )
    balance = fields.Decimal(
        places=2,
        missing=0.00,
        validate=validate.Range(min=0, max=1000),
        error_messages={'invalid': 'El saldo debe ser un número válido entre 0 y 1000'}
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    last_used = fields.DateTime(dump_only=True)
    
    @validates('card_number')
    def validate_card_number(self, value: str) -> None:
        """
        Validar número de tarjeta
        
        Args:
            value: Número de tarjeta
            
        Raises:
            ValidationError: Si el número de tarjeta no es válido
        """
        if not re.match(r'^[0-9]{10,16}$', value):
            raise ValidationError('El número de tarjeta debe contener solo dígitos (10-16 caracteres)')

class CardUpdateSchema(Schema):
    """
    Schema para actualización de tarjetas
    """
    
    _id = fields.Str(dump_only=True)
    balance = fields.Decimal(
        places=2,
        validate=validate.Range(min=0, max=1000),
        allow_none=True
    )
    is_active = fields.Bool(allow_none=True)
    last_used = fields.DateTime(allow_none=True)

class CardBalanceSchema(Schema):
    """
    Schema para operaciones de saldo
    """
    
    amount = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0.01, max=1000),
        error_messages={'required': 'El monto es requerido'}
    )
    operation = fields.Str(
        required=True,
        validate=validate.OneOf(['add', 'subtract']),
        error_messages={'required': 'El tipo de operación es requerido'}
    )

class CardTransferSchema(Schema):
    """
    Schema para transferencias entre tarjetas
    """
    
    from_card_id = fields.Str(
        required=True,
        error_messages={'required': 'La tarjeta origen es requerida'}
    )
    to_card_id = fields.Str(
        required=True,
        error_messages={'required': 'La tarjeta destino es requerida'}
    )
    amount = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0.01, max=1000),
        error_messages={'required': 'El monto es requerido'}
    )

class CardResponseSchema(Schema):
    """
    Schema para respuesta de tarjetas
    """
    
    _id = fields.Str()
    client_id = fields.Str()
    card_number = fields.Str()
    balance = fields.Decimal(places=2)
    is_active = fields.Bool()
    created_at = fields.DateTime()
    last_used = fields.DateTime()

# Instancias de esquemas para uso en la aplicación
card_schema = CardSchema()
card_update_schema = CardUpdateSchema()
card_balance_schema = CardBalanceSchema()
card_transfer_schema = CardTransferSchema()
card_response_schema = CardResponseSchema()
cards_response_schema = CardResponseSchema(many=True) 