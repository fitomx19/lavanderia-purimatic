from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
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
        validate=validate.OneOf(['lavado', 'secado', 'encargo_lavado']),
        error_messages={'required': 'El tipo de servicio es requerido'}
    )
    duration_minutes = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=180),
        error_messages={'required': 'La duración es requerida'}
    )
    price = fields.Decimal(
        places=2,
        validate=validate.Range(min=0.01, max=1000),
        allow_none=True,
        error_messages={'required': 'El precio es requerido para servicios de lavado y secado'}
    )
    price_per_kg = fields.Decimal(
        places=2,
        validate=validate.Range(min=0.01, max=100),
        allow_none=True,
        error_messages={'required': 'El precio por kilogramo es requerido para encargo de lavado'}
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
    
    @validates('price')
    def validate_price_for_service_type(self, value):
        """Validar que el precio esté presente para lavado y secado"""
        # Esta validación se ejecutará en post_load
        pass
    
    @validates('price_per_kg')
    def validate_price_per_kg_for_service_type(self, value):
        """Validar que el precio por kg esté presente para encargo_lavado"""
        # Esta validación se ejecutará en post_load
        pass
    
    @post_load
    def validate_pricing_fields(self, data, **kwargs):
        """Validar que los campos de precio sean consistentes con el tipo de servicio"""
        service_type = data.get('service_type')
        
        if service_type == 'encargo_lavado':
            if not data.get('price_per_kg'):
                raise ValidationError('El precio por kilogramo es requerido para encargo de lavado', 'price_per_kg')
            # Remover price si existe para encargo_lavado
            data.pop('price', None)
        else:  # lavado o secado
            if not data.get('price'):
                raise ValidationError('El precio es requerido para servicios de lavado y secado', 'price')
            # Remover price_per_kg si existe para otros tipos
            data.pop('price_per_kg', None)
            
        return data
    
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
        validate=validate.OneOf(['lavado', 'secado', 'encargo_lavado']),
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
    price_per_kg = fields.Decimal(
        places=2,
        validate=validate.Range(min=0.01, max=100),
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

    @post_load
    def validate_pricing_fields_update(self, data, **kwargs):
        """Validar que los campos de precio sean consistentes con el tipo de servicio en actualización"""
        service_type = data.get('service_type')
        
        if service_type == 'encargo_lavado':
            # Si se está cambiando a encargo_lavado, debe tener price_per_kg
            if 'price_per_kg' in data and not data.get('price_per_kg'):
                raise ValidationError('El precio por kilogramo es requerido para encargo de lavado', 'price_per_kg')
            # Remover price si existe
            data.pop('price', None)
        elif service_type in ['lavado', 'secado']:
            # Si se está cambiando a lavado o secado, debe tener price
            if 'price' in data and not data.get('price'):
                raise ValidationError('El precio es requerido para servicios de lavado y secado', 'price')
            # Remover price_per_kg si existe
            data.pop('price_per_kg', None)
            
        return data

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
    price_per_kg = fields.Decimal(places=2)
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