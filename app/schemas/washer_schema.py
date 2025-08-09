from marshmallow import Schema, fields, validate, validates, ValidationError, post_load

class WasherSchema(Schema):
    """Schema para validación de lavadoras"""
    
    _id = fields.Str(dump_only=True)
    numero = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=99),
        error_messages={'required': 'El número de lavadora es requerido'}
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
    esp32_id = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(min=1, max=50),
        missing=None
    )
    is_active = fields.Bool(missing=True)
    tipo = fields.Str(missing='lavadora')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class WasherUpdateSchema(Schema):
    """Schema para actualización de lavadoras"""
    
    _id = fields.Str(required=True, error_messages={'required': 'El ID de la lavadora es requerido para actualizar'})
    numero = fields.Integer(validate=validate.Range(min=1, max=99), allow_none=True)
    marca = fields.Str(validate=validate.Length(min=2, max=50), allow_none=True)
    capacidad = fields.Decimal(places=1, validate=validate.Range(min=5.0, max=50.0), allow_none=True)
    estado = fields.Str(validate=validate.OneOf(['disponible', 'ocupada', 'mantenimiento']), allow_none=True)
    store_id = fields.Str(allow_none=True)
    is_active = fields.Bool(allow_none=True)
    tipo = fields.Str(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class WasherStatusSchema(Schema):
    """Schema para cambio de estado de lavadora"""
    
    estado = fields.Str(
        required=True,
        validate=validate.OneOf(['disponible', 'ocupada', 'mantenimiento']),
        error_messages={'required': 'El estado es requerido'}
    )

class WasherResponseSchema(Schema):
    """Schema para respuesta de lavadoras"""
    
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
        Determinar el tipo de máquina basándose en la capacidad
        
        Args:
            obj: Objeto lavadora
            
        Returns:
            str: Tipo de máquina ('chica' o 'grande')
        """
        capacidad = float(obj.get('capacidad', 0))
        
        # Clasificación basada en capacidad
        if capacidad <= 10.0:
            return 'chica'
        else:
            return 'grande'

# Instancias
washer_schema = WasherSchema()
washer_update_schema = WasherUpdateSchema()
washer_status_schema = WasherStatusSchema()
washer_response_schema = WasherResponseSchema()
washers_response_schema = WasherResponseSchema(many=True)
