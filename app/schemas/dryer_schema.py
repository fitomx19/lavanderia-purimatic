from marshmallow import Schema, fields, validate, validates, ValidationError

class DryerSchema(Schema):
    """Schema para validación de secadoras"""
    
    _id = fields.Str(dump_only=True)
    numero = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=99),
        error_messages={'required': 'El número de secadora es requerido'}
    )
    marca = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=50),
        error_messages={'required': 'La marca es requerida'}
    )
    capacidad = fields.Decimal(
        required=True,
        places=1,
        validate=validate.Range(min=5.0, max=50.0),
        error_messages={'required': 'La capacidad es requerida'}
    )
    estado = fields.Str(
        required=True,
        validate=validate.OneOf(['disponible', 'ocupada', 'mantenimiento']),
        error_messages={'required': 'El estado es requerido'}
    )
    store_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID de tienda es requerido'}
    )
    is_active = fields.Bool(missing=True)
    tipo = fields.Str(missing='secadora')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class DryerUpdateSchema(Schema):
    """Schema para actualización de secadoras"""
    
    _id = fields.Str(required=True, error_messages={'required': 'El ID de la secadora es requerido para actualizar'})
    numero = fields.Integer(validate=validate.Range(min=1, max=99), allow_none=True)
    marca = fields.Str(validate=validate.Length(min=2, max=50), allow_none=True)
    capacidad = fields.Decimal(places=1, validate=validate.Range(min=5.0, max=50.0), allow_none=True)
    estado = fields.Str(validate=validate.OneOf(['disponible', 'ocupada', 'mantenimiento']), allow_none=True)
    store_id = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)
    tipo = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class DryerStatusSchema(Schema):
    """Schema para cambio de estado de secadora"""
    
    estado = fields.Str(
        required=True,
        validate=validate.OneOf(['disponible', 'ocupada', 'mantenimiento']),
        error_messages={'required': 'El estado es requerido'}
    )

class DryerResponseSchema(Schema):
    """Schema para respuesta de secadoras"""
    
    _id = fields.Str()
    numero = fields.Integer()
    marca = fields.Str()
    capacidad = fields.Decimal(places=1)
    estado = fields.Str()
    store_id = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    tipo = fields.Str()
    
    def get_machine_type(self, obj):
        """
        Determinar el tipo de máquina para secadoras
        
        Args:
            obj: Objeto secadora
            
        Returns:
            str: 'secadora' si capacidad <= 10, 'secadora-grande' si capacidad > 10
        """
        capacidad = float(obj.get('capacidad', 0))
        if capacidad > 10.0:
            return 'secadora-grande'
        return 'secadora'

# Instancias
dryer_schema = DryerSchema()
dryer_update_schema = DryerUpdateSchema()
dryer_status_schema = DryerStatusSchema()
dryer_response_schema = DryerResponseSchema()
dryers_response_schema = DryerResponseSchema(many=True)
