from marshmallow import Schema, fields, validate, pre_load


ENCARGO_STATUSES = ('recibida', 'en_lavado', 'terminada', 'entregada')


class EncargoServicioItemSchema(Schema):
    """Línea de servicio en un encargo (precio editable)."""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    size = fields.Str(missing='', allow_none=True, validate=validate.Length(max=50))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    qty = fields.Int(missing=1, validate=validate.Range(min=1, max=50))


class EncargoPaymentSchema(Schema):
    payment_type = fields.Str(
        required=True,
        validate=validate.OneOf(['efectivo', 'tarjeta_credito', 'tarjeta_recargable']),
    )
    amount = fields.Float(required=True, validate=validate.Range(min=0.01))
    nfc_uid = fields.Str(allow_none=True)
    card_id = fields.Str(allow_none=True)


class EncargoCreateSchema(Schema):
    client_id = fields.Str(allow_none=True)
    client_name = fields.Str(missing='', allow_none=True, validate=validate.Length(max=120))
    client_phone = fields.Str(missing='', allow_none=True, validate=validate.Length(max=40))
    weight_kg = fields.Float(required=True, validate=validate.Range(min=0.1, max=200))
    price_per_kg = fields.Float(allow_none=True, validate=validate.Range(min=0))
    servicios = fields.List(fields.Nested(EncargoServicioItemSchema), missing=[])
    extras = fields.List(fields.Nested(EncargoServicioItemSchema), missing=[])  # compat
    payment_methods = fields.List(
        fields.Nested(EncargoPaymentSchema),
        required=True,
        validate=validate.Length(min=1),
    )
    notes = fields.Str(missing='', allow_none=True, validate=validate.Length(max=500))
    employee_id = fields.Str(allow_none=True)

    @pre_load
    def merge_servicios(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if not data.get('servicios') and data.get('extras'):
            data['servicios'] = data['extras']
        return data


class EncargoStatusSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(ENCARGO_STATUSES))
    machine_id = fields.Str(allow_none=True)
    service_cycle_id = fields.Str(allow_none=True)


class EncargoServicioCatalogSchema(Schema):
    """Fila del catálogo admin (plana)."""

    id = fields.Str(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    size = fields.Str(missing='', allow_none=True, validate=validate.Length(max=50))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    price_tarjeta = fields.Float(allow_none=True, validate=validate.Range(min=0))


class EncargoSettingsSchema(Schema):
    price_per_kg = fields.Float(missing=25.0, validate=validate.Range(min=0))
    price_per_kg_tarjeta = fields.Float(allow_none=True, validate=validate.Range(min=0))
    servicios = fields.List(fields.Nested(EncargoServicioCatalogSchema), missing=[])
    extras = fields.List(fields.Dict(), missing=[])  # ignorable / migrado
    print_bag_label = fields.Bool(missing=True)
    print_notes = fields.Bool(missing=True)

    @pre_load
    def normalize_servicios(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if not data.get('servicios') and data.get('extras'):
            # Migrar nested viejo → plano
            flat = []
            for ex in data['extras']:
                if isinstance(ex, dict) and ex.get('sizes'):
                    for sz in ex['sizes']:
                        flat.append({
                            'id': f"{ex.get('id', 's')}-{sz.get('size', '')}",
                            'name': ex.get('name') or 'Servicio',
                            'size': sz.get('size') or '',
                            'price': float(sz.get('price') or 0),
                        })
                elif isinstance(ex, dict):
                    flat.append({
                        'id': ex.get('id') or ex.get('name') or 's',
                        'name': ex.get('name') or 'Servicio',
                        'size': ex.get('size') or '',
                        'price': float(ex.get('price') or 0),
                    })
            data['servicios'] = flat
        return data


class EncargoResponseSchema(Schema):
    _id = fields.Str()
    folio = fields.Str()
    client_id = fields.Str(allow_none=True)
    client_name = fields.Str(allow_none=True)
    client_phone = fields.Str(allow_none=True)
    weight_kg = fields.Float()
    price_per_kg = fields.Float()
    price_per_kg_original = fields.Float(allow_none=True)
    servicios = fields.List(fields.Dict(), allow_none=True)
    extras = fields.List(fields.Dict(), allow_none=True)
    total_amount = fields.Float()
    subtotal_before_discount = fields.Float(allow_none=True)
    discount_amount = fields.Float(allow_none=True)
    discount_reason = fields.Str(allow_none=True)
    payment_methods = fields.List(fields.Dict())
    status = fields.Str()
    notes = fields.Str(allow_none=True)
    employee_id = fields.Str(allow_none=True)
    machine_id = fields.Str(allow_none=True)
    machine_name = fields.Str(allow_none=True)
    service_cycle_id = fields.Str(allow_none=True)
    wash_started_at = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    status_history = fields.List(fields.Dict(), allow_none=True)
    recibida_at = fields.DateTime(allow_none=True)
    en_lavado_at = fields.DateTime(allow_none=True)
    terminada_at = fields.DateTime(allow_none=True)
    entregada_at = fields.DateTime(allow_none=True)


encargo_create_schema = EncargoCreateSchema()
encargo_status_schema = EncargoStatusSchema()
encargo_settings_schema = EncargoSettingsSchema()
encargo_response_schema = EncargoResponseSchema()
encargos_response_schema = EncargoResponseSchema(many=True)


def default_encargo_settings():
    return {
        'price_per_kg': 25.0,
        'price_per_kg_tarjeta': None,
        'print_bag_label': True,
        'print_notes': True,
        'servicios': [
            {'id': 'colcha-chica', 'name': 'Colcha', 'size': 'chica', 'price': 40.0, 'price_tarjeta': None},
            {'id': 'colcha-mediana', 'name': 'Colcha', 'size': 'mediana', 'price': 60.0, 'price_tarjeta': None},
            {'id': 'colcha-grande', 'name': 'Colcha', 'size': 'grande', 'price': 80.0, 'price_tarjeta': None},
            {'id': 'edredon-ind', 'name': 'Edredón', 'size': 'individual', 'price': 50.0, 'price_tarjeta': None},
            {'id': 'edredon-mat', 'name': 'Edredón', 'size': 'matrimonial', 'price': 70.0, 'price_tarjeta': None},
            {'id': 'edredon-king', 'name': 'Edredón', 'size': 'king', 'price': 90.0, 'price_tarjeta': None},
        ],
    }
