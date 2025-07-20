from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Dict, Any

class UserClientSchema(Schema):
    """
    Schema para validación de usuarios clientes
    """
    
    # Campos de entrada
    _id = fields.Str(dump_only=True)
    nombre = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre es requerido'}
    )
    telefono = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=15),
        error_messages={'required': 'El teléfono es requerido'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'El email es requerido'}
    )
    direccion = fields.Str(
        validate=validate.Length(min=5, max=200),
        allow_none=True
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('nombre')
    def validate_nombre(self, value: str) -> None:
        """
        Validar nombre del cliente
        
        Args:
            value: Nombre del cliente
            
        Raises:
            ValidationError: Si el nombre no es válido
        """
        if not value.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise ValidationError('El nombre solo puede contener letras, espacios, guiones y apostrofes')
    
    @validates('telefono')
    def validate_telefono(self, value: str) -> None:
        """
        Validar teléfono del cliente
        
        Args:
            value: Teléfono del cliente
            
        Raises:
            ValidationError: Si el teléfono no es válido
        """
        from app.utils.validation_utils import validate_phone
        
        if not validate_phone(value):
            raise ValidationError('El formato del teléfono no es válido')

class UserClientUpdateSchema(Schema):
    """
    Schema para actualización de usuarios clientes
    """
    
    _id = fields.Str(dump_only=True)
    nombre = fields.Str(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    telefono = fields.Str(
        validate=validate.Length(min=10, max=15),
        allow_none=True
    )
    email = fields.Email(allow_none=True)
    direccion = fields.Str(
        validate=validate.Length(min=5, max=200),
        allow_none=True
    )
    saldo_tarjeta_recargable = fields.Decimal(
        places=2,
        validate=validate.Range(min=0),
        allow_none=True
    )
    is_active = fields.Bool(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('nombre')
    def validate_nombre(self, value: str) -> None:
        """
        Validar nombre del cliente
        
        Args:
            value: Nombre del cliente
            
        Raises:
            ValidationError: Si el nombre no es válido
        """
        if value and not value.replace(' ', '').replace('-', '').replace("'", '').isalpha():
            raise ValidationError('El nombre solo puede contener letras, espacios, guiones y apostrofes')
    
    @validates('telefono')
    def validate_telefono(self, value: str) -> None:
        """
        Validar teléfono del cliente
        
        Args:
            value: Teléfono del cliente
            
        Raises:
            ValidationError: Si el teléfono no es válido
        """
        if value:
            from app.utils.validation_utils import validate_phone
            
            if not validate_phone(value):
                raise ValidationError('El formato del teléfono no es válido')

class UserClientBalanceSchema(Schema):
    """
    Schema para actualización del saldo de tarjeta recargable
    """
    
    saldo_tarjeta_recargable = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0),
        error_messages={'required': 'El saldo es requerido'}
    )
    operacion = fields.Str(
        required=True,
        validate=validate.OneOf(['agregar', 'reducir', 'establecer']),
        error_messages={'required': 'El tipo de operación es requerido'}
    )

class UserClientResponseSchema(Schema):
    """
    Schema para respuesta de usuarios clientes
    """
    
    _id = fields.Str()
    nombre = fields.Str()
    telefono = fields.Str()
    email = fields.Str()
    direccion = fields.Str()
    saldo_tarjeta_recargable = fields.Decimal(places=2)
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    client_cards = fields.List(fields.Nested('CardSchemaForClientResponse'), dump_only=True)

class CardSchemaForClientResponse(Schema):
    """
    Schema para la serialización de tarjetas dentro de la respuesta del cliente.
    """
    _id = fields.Str()
    card_number = fields.Str()
    balance = fields.Decimal(places=2)
    client_id = fields.Str()
    created_at = fields.DateTime()
    is_active = fields.Bool()
    updated_at = fields.DateTime()
    last_used = fields.DateTime(allow_none=True)
    is_nfc_enabled = fields.Bool(allow_none=True)
    nfc_uid = fields.Str(allow_none=True)

# Instancias de esquemas para uso en la aplicación
user_client_schema = UserClientSchema()
user_client_update_schema = UserClientUpdateSchema()
user_client_balance_schema = UserClientBalanceSchema()
user_client_response_schema = UserClientResponseSchema()
users_client_response_schema = UserClientResponseSchema(many=True)
