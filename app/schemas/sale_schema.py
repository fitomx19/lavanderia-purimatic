from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from typing import Dict, Any

class ProductItemSchema(Schema):
    """
    Schema para items de productos en la venta
    """
    
    product_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID del producto es requerido'}
    )
    quantity = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=100),
        error_messages={'required': 'La cantidad es requerida'}
    )
    unit_price = fields.Float(
        validate=validate.Range(min=0.01, max=1000),
        allow_none=True,
        missing=None
    )
    subtotal = fields.Float(
        validate=validate.Range(min=0.01, max=10000),
        allow_none=True,
        missing=None
    )

class ServiceItemSchema(Schema):
    """
    Schema para items de servicios en la venta
    """
    
    service_cycle_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID del ciclo de servicio es requerido'}
    )
    machine_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID de la máquina es requerido'}
    )
    machine_type = fields.Str(
        validate=validate.OneOf(['washer', 'dryer']),
        allow_none=True
    )
    duration = fields.Int(
        validate=validate.Range(min=1, max=180),
        allow_none=True
    )
    price = fields.Float(
        validate=validate.Range(min=0.01, max=1000),
        allow_none=True,
        missing=None
    )
    weight_kg = fields.Float(allow_none=True, missing=None) # Añadir weight_kg aquí
    status = fields.Str(
        validate=validate.OneOf(['pending', 'active', 'completed']),
        missing='pending'
    )
    started_at = fields.String(allow_none=True)
    completed_at = fields.String(allow_none=True)
    estimated_end_at = fields.String(allow_none=True)

class PaymentMethodSchema(Schema):
    """
    Schema para métodos de pago
    """
    
    payment_type = fields.Str(
        required=True,
        validate=validate.OneOf(['efectivo', 'tarjeta_credito', 'tarjeta_recargable']),
        error_messages={'required': 'El tipo de pago es requerido'}
    )
    amount = fields.Float(
        required=True,
        validate=validate.Range(min=0.01, max=10000),
        error_messages={'required': 'El monto es requerido'}
    )
    card_id = fields.Str(allow_none=True)
    reference = fields.Str(allow_none=True)
    
    @validates('card_id')
    def validate_card_id(self, value: str) -> None:
        """
        Validar que se proporcione card_id para tarjeta recargable
        """
        payment_type = self.context.get('payment_type')
        if payment_type == 'tarjeta_recargable' and not value:
            raise ValidationError('El ID de la tarjeta es requerido para pagos con tarjeta recargable')

class SaleItemsSchema(Schema):
    """
    Schema para items de la venta - estructura simplificada
    """
    
    # Aceptar una lista simple de items
    products = fields.List(
        fields.Nested(ProductItemSchema),
        missing=[]
    )
    services = fields.List(
        fields.Nested(ServiceItemSchema),
        missing=[]
    )

class SaleSchema(Schema):
    """
    Schema para validación de ventas
    """
    
    _id = fields.Str(dump_only=True)
    client_id = fields.Str(allow_none=True)
    employee_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID del empleado es requerido'}
    )
    store_id = fields.Str(
        required=True,
        error_messages={'required': 'El ID de la tienda es requerido'}
    )
    total_amount = fields.Float(
        validate=validate.Range(min=0.01, max=10000),
        allow_none=True,
        missing=None
    )
    payment_methods = fields.List(
        fields.Nested(PaymentMethodSchema),
        required=True,
        validate=validate.Length(min=1),
        error_messages={'required': 'Debe especificar al menos un método de pago'}
    )
    
    # Cambiar a una lista simple de items
    items = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=1),
        error_messages={'required': 'Debe incluir al menos un item'}
    )
    
    status = fields.Str(
        validate=validate.OneOf(['pending', 'completed', 'cancelled']),
        missing='pending'
    )
    created_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(allow_none=True)
    
    @post_load
    def process_items(self, data, **kwargs):
        """
        Procesar items y organizarlos en productos y servicios
        """
        items = data.get('items', [])
        processed_items = {
            'products': [],
            'services': []
        }
        
        for item in items:
            if 'product_id' in item:
                # Es un producto
                processed_items['products'].append({
                    'product_id': item['product_id'],
                    'quantity': item.get('quantity', 1),
                    'unit_price': item.get('unit_price'),
                    'subtotal': item.get('subtotal')
                })
            elif 'service_cycle_id' in item:
                # Es un servicio
                processed_items['services'].append({
                    'service_cycle_id': item['service_cycle_id'],
                    'machine_id': item['machine_id'],
                    'machine_type': item.get('machine_type'),
                    'duration': item.get('duration'),
                    'price': item.get('price'),
                    'weight_kg': item.get('weight_kg'), # Añadir weight_kg aquí
                    'status': item.get('status', 'pending'),
                    'started_at': item.get('started_at'),
                    'estimated_end_at': item.get('estimated_end_at')
                })
        
        # Reemplazar items con la estructura procesada
        data['items'] = processed_items
        return data
    
    @validates('items')
    def validate_items(self, value: list) -> None:
        """
        Validar que haya al menos un item válido
        """
        if not value:
            raise ValidationError('Debe incluir al menos un item')
        
        valid_items = 0
        for item in value:
            if 'product_id' in item or 'service_cycle_id' in item:
                valid_items += 1
        
        if valid_items == 0:
            raise ValidationError('Debe incluir al menos un producto o servicio válido')

class SaleUpdateSchema(Schema):
    """
    Schema para actualización de ventas
    """
    
    _id = fields.Str(dump_only=True)
    status = fields.Str(
        validate=validate.OneOf(['pending', 'completed', 'cancelled']),
        allow_none=True
    )
    completed_at = fields.DateTime(allow_none=True)
    items = fields.Nested(SaleItemsSchema, allow_none=True)

class SaleResponseSchema(Schema):
    """
    Schema para respuesta de ventas
    """
    
    _id = fields.Str()
    client_id = fields.Str()
    employee_id = fields.Str()
    store_id = fields.Str()
    total_amount = fields.Float()
    payment_methods = fields.List(fields.Nested(PaymentMethodSchema))
    items = fields.Nested(SaleItemsSchema)
    status = fields.Str()
    created_at = fields.DateTime()
    completed_at = fields.DateTime()
    finalized_at = fields.DateTime(allow_none=True) # Añadir finalized_at al esquema de respuesta

# Instancias de esquemas para uso en la aplicación
sale_schema = SaleSchema()
sale_update_schema = SaleUpdateSchema()
sale_response_schema = SaleResponseSchema()
sales_response_schema = SaleResponseSchema(many=True) 