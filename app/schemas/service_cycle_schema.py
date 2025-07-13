from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Dict, Any
from bson import ObjectId

class ServiceCycleSchema(Schema):
    """
    Schema para validación de ciclos de servicio
    """
    
    _id = fields.Str(dump_only=True)
    name = fields.Str(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={'required': 'El nombre del ciclo es requerido'}
    )
    description = fields.Str(
        validate=validate.Length(max=500),
        allow_none=True
    )
    service_type = fields.Str(
        required=True,
        validate=validate.OneOf(['lavado', 'secado', 'combo', 'encargo_lavado', 'encargo_secado', 'mixto', 'mixto_encargo']),
        error_messages={'required': 'El tipo de servicio es requerido'}
    )
    duration_minutes = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=180),
        error_messages={'required': 'La duración es requerida'}
    )
    price = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0.01, max=1000),
        error_messages={'required': 'El precio es requerido'}
    )
    allowed_machines = fields.List(
        fields.Nested({
            '_id': fields.Str(required=True, validate=lambda x: ObjectId.is_valid(x)),
            'name': fields.Str(required=True)
        }),
        required=True,
        error_messages={'required': 'Los IDs de máquina permitidos son requeridos'}
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
class ServiceCycleUpdateSchema(Schema):
    """
    Schema para actualización de ciclos de servicio
    """
    
    _id = fields.Str(dump_only=True)
    name = fields.Str(
        validate=validate.Length(min=2, max=100),
        allow_none=True
    )
    description = fields.Str(
        validate=validate.Length(max=500),
        allow_none=True
    )
    service_type = fields.Str(
        validate=validate.OneOf(['lavado', 'secado', 'combo', 'encargo_lavado', 'encargo_secado', 'mixto', 'mixto_encargo']),
        allow_none=True
    )
    duration_minutes = fields.Int(
        validate=validate.Range(min=1, max=180),
        allow_none=True
    )
    price = fields.Decimal(
        places=2,
        validate=validate.Range(min=0.01, max=1000),
        allow_none=True
    )
    allowed_machines = fields.List(
        fields.Nested({
            '_id': fields.Str(required=True, validate=lambda x: ObjectId.is_valid(x)),
            'name': fields.Str(required=True)
        }),
        allow_none=True
    )
    is_active = fields.Bool(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ServiceCycleResponseSchema(Schema):
    """
    Schema para respuesta de ciclos de servicio
    """
    
    _id = fields.Str()
    name = fields.Str()
    description = fields.Str()
    service_type = fields.Str()
    duration_minutes = fields.Int()
    price = fields.Decimal(places=2)
    allowed_machines = fields.List(
        fields.Nested({
            '_id': fields.Str(),
            'name': fields.Str()
        })
    )
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

# Instancias de esquemas para uso en la aplicación
service_cycle_schema = ServiceCycleSchema()
service_cycle_update_schema = ServiceCycleUpdateSchema()
service_cycle_response_schema = ServiceCycleResponseSchema()
service_cycles_response_schema = ServiceCycleResponseSchema(many=True) 