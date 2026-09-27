from marshmallow import Schema, fields, validate, validates_schema, ValidationError


RELOAD_PROMO_MODES = ('paquetes', 'paquetes_y_libre', 'porcentaje_y_libre')
PAY_DISCOUNT_MODES = ('elegir_pct_o_precio', 'solo_precio_ciclo', 'solo_porcentaje')
PAY_DISCOUNT_STYLES = ('porcentaje', 'precio_ciclo')


class ReloadPackageSchema(Schema):
    pay_amount = fields.Float(required=True, validate=validate.Range(min=0.01, max=10000))
    credit_amount = fields.Float(required=True, validate=validate.Range(min=0.01, max=10000))
    label = fields.Str(missing='', allow_none=True, validate=validate.Length(max=80))


class CardBenefitsSettingsSchema(Schema):
    reload_bonus_enabled = fields.Bool(missing=False)
    reload_promo_mode = fields.Str(
        missing='paquetes_y_libre',
        validate=validate.OneOf(RELOAD_PROMO_MODES),
    )
    reload_packages = fields.List(fields.Nested(ReloadPackageSchema), missing=[])
    reload_bonus_percent = fields.Float(missing=0.0, validate=validate.Range(min=0, max=500))

    pay_discount_enabled = fields.Bool(missing=False)
    pay_discount_mode = fields.Str(
        missing='elegir_pct_o_precio',
        validate=validate.OneOf(PAY_DISCOUNT_MODES),
    )
    pay_discount_style = fields.Str(
        missing='porcentaje',
        validate=validate.OneOf(PAY_DISCOUNT_STYLES),
    )
    pay_discount_percent = fields.Float(missing=0.0, validate=validate.Range(min=0, max=100))

    @validates_schema
    def validate_packages(self, data, **kwargs):
        packages = data.get('reload_packages') or []
        for pkg in packages:
            pay = float(pkg.get('pay_amount') or 0)
            credit = float(pkg.get('credit_amount') or 0)
            if credit < pay:
                raise ValidationError(
                    'El saldo acreditado no puede ser menor al monto pagado',
                    'reload_packages',
                )


class CardBenefitsResponseSchema(Schema):
    reload_bonus_enabled = fields.Bool()
    reload_promo_mode = fields.Str()
    reload_packages = fields.List(fields.Dict())
    reload_bonus_percent = fields.Float()
    pay_discount_enabled = fields.Bool()
    pay_discount_mode = fields.Str()
    pay_discount_style = fields.Str()
    pay_discount_percent = fields.Float()
    updated_at = fields.DateTime(allow_none=True)


class ReloadSaleSchema(Schema):
    """Payload para venta de recarga de tarjeta."""

    card_id = fields.Str(required=True)
    client_id = fields.Str(allow_none=True)
    store_id = fields.Str(required=True)
    employee_id = fields.Str(allow_none=True)
    pay_amount = fields.Float(required=True, validate=validate.Range(min=0.01, max=10000))
    credit_amount = fields.Float(allow_none=True, validate=validate.Range(min=0.01, max=10000))
    package_index = fields.Int(allow_none=True, validate=validate.Range(min=0, max=100))
    payment_methods = fields.List(
        fields.Dict(),
        required=True,
        validate=validate.Length(min=1),
    )
    notes = fields.Str(allow_none=True, validate=validate.Length(max=300))


card_benefits_settings_schema = CardBenefitsSettingsSchema()
card_benefits_response_schema = CardBenefitsResponseSchema()
reload_sale_schema = ReloadSaleSchema()


def default_card_benefits_settings():
    return {
        'reload_bonus_enabled': False,
        'reload_promo_mode': 'paquetes_y_libre',
        'reload_packages': [
            {'pay_amount': 500.0, 'credit_amount': 700.0, 'label': 'Promo $500'},
            {'pay_amount': 1000.0, 'credit_amount': 1400.0, 'label': 'Promo $1000'},
        ],
        'reload_bonus_percent': 0.0,
        'pay_discount_enabled': False,
        'pay_discount_mode': 'elegir_pct_o_precio',
        'pay_discount_style': 'porcentaje',
        'pay_discount_percent': 0.0,
    }


def effective_pay_discount_style(settings: dict):
    """Devuelve 'porcentaje', 'precio_ciclo' o None si el descuento al pagar está apagado."""
    if not settings or not settings.get('pay_discount_enabled'):
        return None
    mode = settings.get('pay_discount_mode') or 'elegir_pct_o_precio'
    if mode == 'solo_porcentaje':
        return 'porcentaje'
    if mode == 'solo_precio_ciclo':
        return 'precio_ciclo'
    style = settings.get('pay_discount_style') or 'porcentaje'
    return style if style in PAY_DISCOUNT_STYLES else 'porcentaje'


def compute_reload_credit(settings: dict, pay_amount: float, package_index=None):
    """
    Calcula saldo a acreditar según config.
    Retorna (credit_amount, bonus_amount, source).
    """
    pay = round(float(pay_amount), 2)
    if not settings or not settings.get('reload_bonus_enabled'):
        return pay, 0.0, 'sin_bono'

    mode = settings.get('reload_promo_mode') or 'paquetes_y_libre'
    packages = settings.get('reload_packages') or []

    if package_index is not None:
        try:
            idx = int(package_index)
            if 0 <= idx < len(packages):
                pkg = packages[idx]
                credit = round(float(pkg.get('credit_amount') or pay), 2)
                return credit, round(credit - pay, 2), 'paquete'
        except (TypeError, ValueError):
            pass

    if mode in ('paquetes', 'paquetes_y_libre'):
        for pkg in packages:
            if abs(float(pkg.get('pay_amount') or 0) - pay) < 0.01:
                credit = round(float(pkg.get('credit_amount') or pay), 2)
                return credit, round(credit - pay, 2), 'paquete'

    if mode == 'porcentaje_y_libre':
        pct = float(settings.get('reload_bonus_percent') or 0)
        credit = round(pay * (1 + pct / 100.0), 2)
        return credit, round(credit - pay, 2), 'porcentaje'

    if mode == 'paquetes':
        # Sin paquete coincidente en modo solo-paquetes
        return pay, 0.0, 'sin_bono'

    return pay, 0.0, 'libre'
