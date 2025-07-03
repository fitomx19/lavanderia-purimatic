from marshmallow import Schema, fields, validate, validates, ValidationError

class ProductSchema(Schema):
    """Schema para validación de productos"""
    
    _id = fields.Str(dump_only=True)
    nombre = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre del producto es requerido'}
    )
    descripcion = fields.Str(
        validate=validate.Length(max=500),
        allow_none=True
    )
    precio = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0),
        error_messages={'required': 'El precio es requerido'}
    )
    tipo = fields.Str(
        required=True,
        validate=validate.OneOf(['jabon', 'suavizante', 'bolsas', 'detergente', 'blanqueador', 'quitamanchas', 'otros']),
        error_messages={'required': 'El tipo de producto es requerido'}
    )
    stock = fields.Integer(
        required=True,
        validate=validate.Range(min=0),
        error_messages={'required': 'El stock es requerido'}
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductUpdateSchema(Schema):
    """Schema para actualización de productos"""
    
    _id = fields.Str(dump_only=True)
    nombre = fields.Str(validate=validate.Length(min=2, max=100), allow_none=True)
    descripcion = fields.Str(validate=validate.Length(max=500), allow_none=True)
    precio = fields.Decimal(places=2, validate=validate.Range(min=0), allow_none=True)
    tipo = fields.Str(validate=validate.OneOf(['jabon', 'suavizante', 'bolsas', 'detergente', 'blanqueador', 'quitamanchas', 'otros']), allow_none=True)
    stock = fields.Integer(validate=validate.Range(min=0), allow_none=True)
    is_active = fields.Bool(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ProductResponseSchema(Schema):
    """Schema para respuesta de productos"""
    
    _id = fields.Str()
    nombre = fields.Str()
    descripcion = fields.Str()
    precio = fields.Decimal(places=2)
    tipo = fields.Str()
    stock = fields.Integer()
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

# Instancias
product_schema = ProductSchema()
product_update_schema = ProductUpdateSchema()
product_response_schema = ProductResponseSchema()
products_response_schema = ProductResponseSchema(many=True)
