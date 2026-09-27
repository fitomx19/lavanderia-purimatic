from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


class Esp32ConfigSchema(Schema):
    """Schema para crear o actualizar una placa ESP32 (varios IDs por URL)."""

    _id = fields.Str(dump_only=True)
    name = fields.Str(missing='', validate=validate.Length(max=100), allow_none=True)
    esp32_url = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=255),
        error_messages={'required': 'esp32_url es requerida'},
    )
    # Puede ir vacío al crear la placa; las máquinas se agregan después
    esp32_ids = fields.List(
        fields.Str(validate=validate.Length(min=1, max=50)),
        missing=[],
        validate=validate.Length(max=64),
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @pre_load
    def normalize_ids(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if data.get('esp32_ids') is None:
            data['esp32_ids'] = []
        if (not data.get('esp32_ids')) and data.get('esp32_id'):
            data['esp32_ids'] = [str(data['esp32_id']).strip()]
        if isinstance(data.get('esp32_ids'), str):
            data['esp32_ids'] = [
                part.strip() for part in data['esp32_ids'].split(',') if part.strip()
            ]
        return data

    @validates('esp32_url')
    def validate_esp32_url(self, value):
        if not value.startswith('http://') and not value.startswith('https://'):
            raise ValidationError('esp32_url debe empezar con http:// o https://')

    @validates('esp32_ids')
    def validate_esp32_ids(self, value):
        if value is None:
            return
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValidationError('Hay esp32_id duplicados en la lista')


class Esp32ConfigUpdateSchema(Schema):
    """Schema para actualización parcial de una placa ESP32."""

    name = fields.Str(validate=validate.Length(max=100), allow_none=True)
    esp32_url = fields.Str(validate=validate.Length(min=8, max=255), allow_none=True)
    esp32_ids = fields.List(
        fields.Str(validate=validate.Length(min=1, max=50)),
        validate=validate.Length(max=64),
        allow_none=True,
    )
    is_active = fields.Bool(allow_none=True)

    @pre_load
    def normalize_ids(self, data, **kwargs):
        if not isinstance(data, dict):
            return data
        if isinstance(data.get('esp32_ids'), str):
            data = dict(data)
            data['esp32_ids'] = [
                part.strip() for part in data['esp32_ids'].split(',') if part.strip()
            ]
        return data

    @validates('esp32_url')
    def validate_esp32_url(self, value):
        if value is None:
            return
        if not value.startswith('http://') and not value.startswith('https://'):
            raise ValidationError('esp32_url debe empezar con http:// o https://')

    @validates('esp32_ids')
    def validate_esp32_ids(self, value):
        if value is None:
            return
        cleaned = [str(v).strip() for v in value if str(v).strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValidationError('Hay esp32_id duplicados en la lista')


class Esp32ConfigResponseSchema(Schema):
    """Schema de respuesta de una placa ESP32."""

    _id = fields.Str()
    name = fields.Str(allow_none=True)
    esp32_id = fields.Str(allow_none=True)
    esp32_ids = fields.List(fields.Str(), allow_none=True)
    esp32_url = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


esp32_config_schema = Esp32ConfigSchema()
esp32_config_update_schema = Esp32ConfigUpdateSchema()
esp32_config_response_schema = Esp32ConfigResponseSchema()
esp32_configs_response_schema = Esp32ConfigResponseSchema(many=True)
