from marshmallow import Schema, fields, validate, validates, ValidationError
from typing import Dict, Any

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
        validate=validate.OneOf(['lavado', 'secado', 'combo']),
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
    machine_types_allowed = fields.List(
        fields.Str(validate=validate.OneOf(['chica', 'grande', 'secadora'])),
        required=True,
        error_messages={'required': 'Los tipos de máquina permitidos son requeridos'}
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('machine_types_allowed')
    def validate_machine_types(self, value: list) -> None:
        """
        Validar tipos de máquina permitidos
        
        Args:
            value: Lista de tipos de máquina
            
        Raises:
            ValidationError: Si la lista está vacía o no es válida
        """
        if not value or len(value) == 0:
            raise ValidationError('Debe especificar al menos un tipo de máquina')
        
        # Validar compatibilidad con tipo de servicio
        service_type = self.context.get('service_type')
        if service_type == 'lavado' and 'secadora' in value:
            raise ValidationError('El servicio de lavado no puede usar secadoras')
        elif service_type == 'secado' and ('chica' in value or 'grande' in value):
            raise ValidationError('El servicio de secado solo puede usar secadoras')

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
        validate=validate.OneOf(['lavado', 'secado', 'combo']),
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
    machine_types_allowed = fields.List(
        fields.Str(validate=validate.OneOf(['chica', 'grande', 'secadora'])),
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
    machine_types_allowed = fields.List(fields.Str())
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

# Instancias de esquemas para uso en la aplicación
service_cycle_schema = ServiceCycleSchema()
service_cycle_update_schema = ServiceCycleUpdateSchema()
service_cycle_response_schema = ServiceCycleResponseSchema()
service_cycles_response_schema = ServiceCycleResponseSchema(many=True) 