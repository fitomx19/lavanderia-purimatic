from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Dict, Any

class UserEmployeeSchema(Schema):
    """
    Schema para validación de usuarios empleados
    """
    
    # Campos de entrada
    _id = fields.Str(dump_only=True)
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=50),
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'El email es requerido'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        load_only=True,
        error_messages={'required': 'La contraseña es requerida'}
    )
    password_hash = fields.Str(dump_only=True)
    role = fields.Str(
        required=True,
        validate=validate.OneOf(['admin', 'empleado']),
        error_messages={'required': 'El rol es requerido'}
    )
    store_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID de tienda es requerido'}
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('username')
    def validate_username(self, value: str) -> None:
        """
        Validar nombre de usuario
        
        Args:
            value: Nombre de usuario
            
        Raises:
            ValidationError: Si el nombre de usuario no es válido
        """
        if not value.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('El nombre de usuario solo puede contener letras, números, guiones y guiones bajos')
    
    @validates('password')
    def validate_password(self, value: str) -> None:
        """
        Validar contraseña
        
        Args:
            value: Contraseña
            
        Raises:
            ValidationError: Si la contraseña no es válida
        """
        from app.utils.validation_utils import validate_password_strength
        
        is_valid, errors = validate_password_strength(value)
        if not is_valid:
            raise ValidationError(errors)

class UserEmployeeUpdateSchema(Schema):
    """
    Schema para actualización de usuarios empleados
    """
    
    _id = fields.Str(dump_only=True)
    username = fields.Str(
        validate=validate.Length(min=3, max=50),
        allow_none=True
    )
    email = fields.Email(allow_none=True)
    password = fields.Str(
        validate=validate.Length(min=8),
        load_only=True,
        allow_none=True
    )
    password_hash = fields.Str(dump_only=True)
    role = fields.Str(
        validate=validate.OneOf(['admin', 'empleado']),
        allow_none=True
    )
    store_id = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('username')
    def validate_username(self, value: str) -> None:
        """
        Validar nombre de usuario
        
        Args:
            value: Nombre de usuario
            
        Raises:
            ValidationError: Si el nombre de usuario no es válido
        """
        if value and not value.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('El nombre de usuario solo puede contener letras, números, guiones y guiones bajos')
    
    @validates('password')
    def validate_password(self, value: str) -> None:
        """
        Validar contraseña
        
        Args:
            value: Contraseña
            
        Raises:
            ValidationError: Si la contraseña no es válida
        """
        if value:
            from app.utils.validation_utils import validate_password_strength
            
            is_valid, errors = validate_password_strength(value)
            if not is_valid:
                raise ValidationError(errors)

class UserEmployeeLoginSchema(Schema):
    """
    Schema para login de usuarios empleados
    """
    
    username = fields.Str(
        required=True,
        error_messages={'required': 'El nombre de usuario es requerido'}
    )
    password = fields.Str(
        required=True,
        load_only=True,
        error_messages={'required': 'La contraseña es requerida'}
    )

class UserEmployeeResponseSchema(Schema):
    """
    Schema para respuesta de usuarios empleados (sin información sensible)
    """
    
    _id = fields.Str()
    username = fields.Str()
    email = fields.Str()
    role = fields.Str()
    store_id = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

# Instancias de esquemas para uso en la aplicación
user_employee_schema = UserEmployeeSchema()
user_employee_update_schema = UserEmployeeUpdateSchema()
user_employee_login_schema = UserEmployeeLoginSchema()
user_employee_response_schema = UserEmployeeResponseSchema()
users_employee_response_schema = UserEmployeeResponseSchema(many=True)
