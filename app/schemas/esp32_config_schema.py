from marshmallow import Schema, fields, validate, validates, ValidationError


class Esp32ConfigSchema(Schema):
    """Schema para crear o actualizar una placa ESP32."""

    _id = fields.Str(dump_only=True)
    esp32_id = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50),
        error_messages={'required': 'esp32_id es requerido'},
    )
    esp32_url = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=255),
        error_messages={'required': 'esp32_url es requerida'},
    )
    is_active = fields.Bool(missing=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('esp32_url')
    def validate_esp32_url(self, value):
        if not value.startswith('http://') and not value.startswith('https://'):
            raise ValidationError('esp32_url debe empezar con http:// o https://')


class Esp32ConfigUpdateSchema(Schema):
    """Schema para actualización parcial de una placa ESP32."""

    esp32_url = fields.Str(validate=validate.Length(min=8, max=255), allow_none=True)
    is_active = fields.Bool(allow_none=True)

    @validates('esp32_url')
    def validate_esp32_url(self, value):
        if value is None:
            return
        if not value.startswith('http://') and not value.startswith('https://'):
            raise ValidationError('esp32_url debe empezar con http:// o https://')


class Esp32ConfigResponseSchema(Schema):
    """Schema de respuesta de una placa ESP32."""

    _id = fields.Str()
    esp32_id = fields.Str()
    esp32_url = fields.Str()
    is_active = fields.Bool()
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


esp32_config_schema = Esp32ConfigSchema()
esp32_config_update_schema = Esp32ConfigUpdateSchema()
esp32_config_response_schema = Esp32ConfigResponseSchema()
esp32_configs_response_schema = Esp32ConfigResponseSchema(many=True)
