from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


DAY_KEYS = ('lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom')


class TicketHoursDaySchema(Schema):
    day = fields.Str(required=True, validate=validate.OneOf(DAY_KEYS))
    open = fields.Str(missing='07:00', allow_none=True)
    close = fields.Str(missing='22:00', allow_none=True)
    closed = fields.Bool(missing=False)


class TicketSettingsSchema(Schema):
    """Configuración de ticket térmico 80mm."""

    store_name = fields.Str(missing='', validate=validate.Length(max=120), allow_none=True)
    address = fields.Str(missing='', validate=validate.Length(max=250), allow_none=True)
    wifi_ssid = fields.Str(missing='', validate=validate.Length(max=120), allow_none=True)
    wifi_password = fields.Str(missing='', validate=validate.Length(max=120), allow_none=True)
    promo_mes = fields.Str(missing='', validate=validate.Length(max=500), allow_none=True)
    footer_thanks = fields.Str(missing='Gracias por tu compra', validate=validate.Length(max=200), allow_none=True)
    printer_name = fields.Str(missing='', validate=validate.Length(max=200), allow_none=True)
    hours = fields.List(fields.Nested(TicketHoursDaySchema), allow_none=True)
    logo_base64 = fields.Str(allow_none=True)
    logo_mime = fields.Str(allow_none=True, validate=validate.Length(max=64))
    clear_logo = fields.Bool(missing=False)

    @validates('logo_mime')
    def validate_logo_mime(self, value):
        if not value:
            return
        allowed = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
        if value.lower() not in allowed:
            raise ValidationError('logo_mime debe ser image/png, image/jpeg o image/webp')


class TicketSettingsResponseSchema(Schema):
    store_name = fields.Str(allow_none=True)
    address = fields.Str(allow_none=True)
    wifi_ssid = fields.Str(allow_none=True)
    wifi_password = fields.Str(allow_none=True)
    promo_mes = fields.Str(allow_none=True)
    footer_thanks = fields.Str(allow_none=True)
    printer_name = fields.Str(allow_none=True)
    hours = fields.List(fields.Nested(TicketHoursDaySchema), allow_none=True)
    logo_mime = fields.Str(allow_none=True)
    has_logo = fields.Bool()
    logo_base64 = fields.Str(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


ticket_settings_schema = TicketSettingsSchema()
ticket_settings_response_schema = TicketSettingsResponseSchema()


def default_ticket_hours():
    """Horario por defecto Lun-Vie 07:00-22:00, Sab-Dom 08:00-15:00."""
    hours = []
    for day in DAY_KEYS:
        if day in ('sab', 'dom'):
            hours.append({'day': day, 'open': '08:00', 'close': '15:00', 'closed': False})
        else:
            hours.append({'day': day, 'open': '07:00', 'close': '22:00', 'closed': False})
    return hours
