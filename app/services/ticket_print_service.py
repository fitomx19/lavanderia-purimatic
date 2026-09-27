"""
Impresión de tickets térmicos 80mm vía ESC/POS en Windows.
"""
from __future__ import annotations

import base64
import io
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

ESC_POS_WIDTH_DOTS = 384
LINE_WIDTH_CHARS = 42
MAX_LOGO_HEIGHT = 180

DAY_LABELS = {
    'lun': 'Lun',
    'mar': 'Mar',
    'mie': 'Mie',
    'jue': 'Jue',
    'vie': 'Vie',
    'sab': 'Sab',
    'dom': 'Dom',
}
DAY_ORDER = ('lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom')


class TicketPrintService:
    def __init__(self, store_repository=None):
        if store_repository is None:
            from app.repositories.store_repository import StoreRepository
            store_repository = StoreRepository()
        self.store_repository = store_repository

    @staticmethod
    def list_printers() -> List[str]:
        try:
            import win32print
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            printers = win32print.EnumPrinters(flags)
            return [p[2] for p in printers if p[2]]
        except Exception as e:
            logger.error(f"No se pudieron listar impresoras: {e}")
            return []

    @staticmethod
    def get_default_printer_name() -> Optional[str]:
        try:
            import win32print
            return win32print.GetDefaultPrinter()
        except Exception as e:
            logger.error(f"No se pudo obtener impresora predeterminada: {e}")
            return None

    def _resolve_printer(self, printer_name: Optional[str] = None) -> str:
        name = (printer_name or '').strip()
        if name:
            return name
        default = self.get_default_printer_name()
        if not default:
            raise RuntimeError('No hay impresora predeterminada en Windows')
        return default

    def _send_raw(self, data: bytes, printer_name: Optional[str] = None) -> str:
        import win32print

        printer = self._resolve_printer(printer_name)
        handle = win32print.OpenPrinter(printer)
        try:
            win32print.StartDocPrinter(handle, 1, ('Purimatic Ticket', None, 'RAW'))
            try:
                win32print.StartPagePrinter(handle)
                written = win32print.WritePrinter(handle, data)
                win32print.EndPagePrinter(handle)
            finally:
                win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)
        return printer

    @staticmethod
    def _encode_text(text: str) -> bytes:
        import unicodedata

        if text is None:
            text = ''
        text = unicodedata.normalize('NFC', str(text))
        # Sustituciones por si la impresora no tiene el glifo en CP850
        replacements = {
            '–': '-',
            '—': '-',
            '“': '"',
            '”': '"',
            '‘': "'",
            '’': "'",
            '…': '...',
            '€': 'EUR',
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        try:
            return text.encode('cp850', errors='replace')
        except Exception:
            return text.encode('latin-1', errors='replace')

    def _barcode_code128(self, data: str) -> bytes:
        """CODE128 ESC/POS (GS k 73) con HRI debajo."""
        text = str(data or '').strip()
        payload = ''.join(ch for ch in text if 32 <= ord(ch) < 127).encode('ascii')
        if not payload:
            return b''
        out = bytearray()
        out += b'\x1b\x61\x01'  # center
        out += b'\x1d\x68\x50'  # barcode height
        out += b'\x1d\x77\x02'  # module width
        out += b'\x1d\x48\x02'  # HRI below
        out += b'\x1d\x6b\x49'  # CODE128
        out += bytes([len(payload)])
        out += payload
        out += b'\n'
        out += self._encode_text(self._center(text) + '\n')
        out += b'\x1b\x61\x00'
        return bytes(out)

    @staticmethod
    def _center(text: str, width: int = LINE_WIDTH_CHARS) -> str:
        text = text.strip()
        if len(text) >= width:
            return text[:width]
        pad = (width - len(text)) // 2
        return (' ' * pad) + text

    @staticmethod
    def _line(left: str, right: str, width: int = LINE_WIDTH_CHARS) -> str:
        left = left[: width - 1]
        right = right[: max(0, width - len(left) - 1)]
        spaces = width - len(left) - len(right)
        return left + (' ' * max(1, spaces)) + right

    @staticmethod
    def _wrap(text: str, width: int = LINE_WIDTH_CHARS) -> List[str]:
        words = (text or '').split()
        if not words:
            return []
        lines = []
        current = ''
        for w in words:
            if len(current) + len(w) + (1 if current else 0) <= width:
                current = (current + ' ' + w).strip()
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines

    def _sep(self, char: str = '-') -> bytes:
        return self._encode_text(char * LINE_WIDTH_CHARS + '\n')

    def _section_title(self, title: str) -> bytes:
        out = bytearray()
        out += b'\x1b\x61\x01'
        out += b'\x1b\x45\x01'  # bold on
        out += self._encode_text(f'>> {title} <<\n')
        out += b'\x1b\x45\x00'
        out += b'\x1b\x61\x00'
        return bytes(out)

    @classmethod
    def _compact_hours(cls, hours: Optional[List[Dict[str, Any]]]) -> List[str]:
        if not hours:
            return []
        by_day = {h.get('day'): h for h in hours if h.get('day')}
        ordered = [by_day[d] for d in DAY_ORDER if d in by_day]
        if not ordered:
            return []

        def sig(h: Dict[str, Any]) -> Tuple:
            if h.get('closed'):
                return ('closed',)
            return ('open', h.get('open') or '', h.get('close') or '')

        groups = []
        start = 0
        while start < len(ordered):
            end = start
            s = sig(ordered[start])
            while end + 1 < len(ordered) and sig(ordered[end + 1]) == s:
                end += 1
            days = ordered[start : end + 1]
            first = DAY_LABELS.get(days[0].get('day'), days[0].get('day'))
            last = DAY_LABELS.get(days[-1].get('day'), days[-1].get('day'))
            day_span = first if start == end else f'{first}-{last}'
            if days[0].get('closed'):
                groups.append(f'{day_span}: Cerrado')
            else:
                groups.append(
                    f"{day_span} {days[0].get('open') or ''}-{days[0].get('close') or ''}"
                )
            start = end + 1
        return groups

    def _logo_raster(self, logo_base64: Optional[str]) -> Tuple[bytes, Dict[str, Any]]:
        debug: Dict[str, Any] = {
            'logo_provided': bool(logo_base64),
            'logo_ok': False,
            'error': None,
            'width': 0,
            'height': 0,
            'raster_bytes': 0,
            'black_pixels': 0,
            'black_ratio': 0.0,
            'decoded_bytes': 0,
            'method': 'GS_v_0',
            'inverted': False,
        }
        if not logo_base64:
            debug['error'] = 'No hay logo guardado. Sube un PNG/JPEG y guarda antes de probar.'
            return b'', debug
        try:
            from PIL import Image, ImageOps, ImageEnhance

            raw = logo_base64
            if ',' in raw and raw.strip().lower().startswith('data:'):
                raw = raw.split(',', 1)[1]
            raw = ''.join(raw.split())
            img_bytes = base64.b64decode(raw)
            debug['decoded_bytes'] = len(img_bytes)
            img = Image.open(io.BytesIO(img_bytes))
            debug['source_mode'] = img.mode
            debug['source_size'] = f'{img.width}x{img.height}'

            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGBA', img.size, (255, 255, 255, 255))
                img = Image.alpha_composite(background, img.convert('RGBA')).convert('RGB')
            else:
                img = img.convert('RGB')

            max_w = ESC_POS_WIDTH_DOTS
            if img.width != max_w:
                ratio = max_w / float(img.width)
                img = img.resize((max_w, max(1, int(img.height * ratio))), Image.LANCZOS)
            if img.height > MAX_LOGO_HEIGHT:
                ratio = MAX_LOGO_HEIGHT / float(img.height)
                img = img.resize((max(8, int(img.width * ratio)), MAX_LOGO_HEIGHT), Image.LANCZOS)

            width = img.width - (img.width % 8)
            if width < 8:
                debug['error'] = 'Logo demasiado estrecho tras alinear a 8 px'
                return b'', debug
            if width != img.width:
                img = img.crop((0, 0, width, img.height))

            gray = ImageOps.grayscale(img)
            gray = ImageEnhance.Contrast(gray).enhance(2.2)
            bw = gray.point(lambda x: 0 if x < 140 else 255, mode='1')

            width_bytes = width // 8
            height = bw.height
            pixels = bw.load()
            black = 0
            total = width * height
            data = bytearray()
            for y in range(height):
                for x_byte in range(width_bytes):
                    byte_val = 0
                    for bit in range(8):
                        x = x_byte * 8 + bit
                        if pixels[x, y] == 0:
                            byte_val |= 0x80 >> bit
                            black += 1
                    data.append(byte_val)

            ratio = black / float(total) if total else 0
            if ratio < 0.03:
                debug['inverted'] = True
                data = bytearray((~b) & 0xFF for b in data)
                black = total - black
                ratio = black / float(total) if total else 0

            header = bytearray()
            header += b'\x1d\x76\x30\x00'
            header += bytes([width_bytes & 0xFF, (width_bytes >> 8) & 0xFF])
            header += bytes([height & 0xFF, (height >> 8) & 0xFF])
            raster = bytes(header) + bytes(data) + b'\n'

            debug.update({
                'logo_ok': True,
                'width': width,
                'height': height,
                'raster_bytes': len(raster),
                'black_pixels': black,
                'black_ratio': round(ratio, 4),
            })
            return raster, debug
        except Exception as e:
            debug['error'] = str(e)
            logger.warning(f"No se pudo convertir logo a ESC/POS: {e}", exc_info=True)
            return b'', debug

    def build_ticket_bytes(
        self,
        settings: Dict[str, Any],
        sale: Dict[str, Any],
        card_balances: Optional[List[Dict[str, Any]]] = None,
        include_logo_debug_line: bool = False,
    ) -> Tuple[bytes, Dict[str, Any]]:
        out = bytearray()
        out += b'\x1b\x40'
        # PC850 (Western Europe) — coincide con encode cp850 para acentos
        out += b'\x1b\x74\x02'

        logo, logo_debug = self._logo_raster(settings.get('logo_base64'))
        if logo_debug.get('logo_ok'):
            logger.info(
                f"Ticket logo OK {logo_debug.get('width')}x{logo_debug.get('height')} "
                f"black_ratio={logo_debug.get('black_ratio')}"
            )
        elif logo_debug.get('error'):
            logger.warning(f"Ticket logo: {logo_debug.get('error')}")

        if logo:
            out += b'\x1b\x61\x01'
            out += logo
            out += b'\n'

        # Header
        out += b'\x1b\x61\x01'
        store_name = (settings.get('store_name') or 'Lavandería Purimatic').strip()
        out += b'\x1b\x21\x30'
        out += self._encode_text(store_name[:20] + '\n')
        out += b'\x1b\x21\x00'

        address = (settings.get('address') or '').strip()
        if address:
            for line in self._wrap(address, LINE_WIDTH_CHARS):
                out += self._encode_text(line + '\n')

        out += self._sep('=')
        out += b'\x1b\x61\x00'

        folio = (sale.get('folio') or '').strip()
        if not folio:
            sale_id = str(sale.get('_id') or '')
            folio = sale_id[-8:] if sale_id else 'N/A'
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        out += b'\x1b\x45\x01'
        out += self._encode_text(self._line('FOLIO', folio) + '\n')
        out += b'\x1b\x45\x00'
        out += self._encode_text(self._line('Fecha', now) + '\n')

        employee_name = (sale.get('employee_name') or '').strip()
        if employee_name:
            out += self._encode_text(self._line('Te atendió', employee_name[:22]) + '\n')

        client_name = (sale.get('client_name') or '').strip()
        if client_name:
            out += self._encode_text(self._line('Cliente', client_name[:22]) + '\n')
        client_phone = (sale.get('client_phone') or '').strip()
        if client_phone:
            out += self._encode_text(self._line('Tel', client_phone[:22]) + '\n')

        out += self._sep('-')
        out += self._section_title('DETALLE')

        items = sale.get('items') or {}
        products = items.get('products') or []
        services = items.get('services') or []
        reload_info = items.get('reload') or {}
        is_reload = (sale.get('sale_type') == 'recarga') or bool(reload_info)

        if is_reload:
            pay_amt = float(
                reload_info.get('pay_amount')
                or sale.get('pay_amount')
                or sale.get('total_amount')
                or 0
            )
            credit_amt = float(
                reload_info.get('credit_amount') or sale.get('credit_amount') or pay_amt
            )
            bonus_amt = float(
                reload_info.get('bonus_amount')
                or sale.get('bonus_amount')
                or max(0.0, credit_amt - pay_amt)
            )
            card_num = reload_info.get('card_number') or ''
            out += self._encode_text(self._line('Recarga tarjeta', '') + '\n')
            if card_num:
                out += self._encode_text(self._line('Tarjeta', str(card_num)[-8:]) + '\n')
            out += self._encode_text(self._line('Pagó', f'${pay_amt:.2f}') + '\n')
            out += self._encode_text(self._line('Acreditó', f'${credit_amt:.2f}') + '\n')
            if bonus_amt > 0.009:
                out += b'\x1b\x45\x01'
                out += self._encode_text(self._line('Bono', f'${bonus_amt:.2f}') + '\n')
                out += b'\x1b\x45\x00'
        elif not products and not services:
            out += b'\x1b\x61\x01'
            out += self._encode_text('(sin artículos)\n')
            out += b'\x1b\x61\x00'

        for p in products:
            # Solo nombre legible para el cliente (nunca product_id / _id)
            name = str(p.get('nombre') or p.get('name') or 'Producto').strip()
            if not name or len(name) == 24 and all(c in '0123456789abcdef' for c in name.lower()):
                name = 'Producto'
            qty = p.get('quantity', 1)
            sub = float(p.get('subtotal') or 0)
            out += self._encode_text(self._line(f'{qty}x {name}', f'${sub:.2f}') + '\n')

        for s in services:
            # Solo nombre del ciclo/servicio; sin machine_id / esp32 / ObjectId
            name = str(
                s.get('cycle_name')
                or s.get('service_name')
                or s.get('nombre')
                or s.get('name')
                or 'Servicio'
            ).strip()
            if not name or name == str(s.get('service_cycle_id') or '') or name == str(s.get('machine_id') or ''):
                name = 'Servicio'
            weight = s.get('weight_kg')
            if weight is not None:
                try:
                    w = float(weight)
                    if w > 0:
                        name = f'{name} ({w:g} kg)'
                except (TypeError, ValueError):
                    pass
            price = float(s.get('price') or s.get('subtotal') or 0)
            price_orig = s.get('price_original')
            out += self._encode_text(self._line(name, f'${price:.2f}') + '\n')
            if price_orig is not None and float(price_orig) > price + 0.009:
                out += self._encode_text(
                    self._line('  Precio normal', f'${float(price_orig):.2f}') + '\n'
                )

        out += self._sep('=')
        discount_amount = float(sale.get('discount_amount') or 0)
        if discount_amount > 0.009:
            sub_before = float(
                sale.get('subtotal_before_discount')
                or (float(sale.get('total_amount') or 0) + discount_amount)
            )
            out += self._encode_text(self._line('Subtotal', f'${sub_before:.2f}') + '\n')
            out += b'\x1b\x45\x01'
            out += self._encode_text(
                self._line('Ahorro con tarjeta', f'-${discount_amount:.2f}') + '\n'
            )
            out += b'\x1b\x45\x00'

        total = float(sale.get('total_amount') or 0)
        out += b'\x1b\x21\x20'
        out += self._encode_text(self._line('TOTAL', f'${total:.2f}') + '\n')
        out += b'\x1b\x21\x00'

        payments = sale.get('payment_methods') or []
        if payments:
            out += self._encode_text('Pagos:\n')
            labels = {
                'efectivo': 'Efectivo',
                'tarjeta_recargable': 'Tarjeta',
                'tarjeta_credito': 'T. crédito',
                'tarjeta': 'Tarjeta',
                'transferencia': 'Transferencia',
            }
            for pm in payments:
                ptype = pm.get('payment_type') or ''
                amount = float(pm.get('amount') or 0)
                label = labels.get(ptype, ptype)
                out += self._encode_text(self._line(f'  {label}', f'${amount:.2f}') + '\n')

        if card_balances:
            out += self._sep('-')
            for bal in card_balances:
                remaining = bal.get('balance_after')
                if remaining is None:
                    remaining = bal.get('new_balance')
                if remaining is not None:
                    out += b'\x1b\x45\x01'
                    out += self._encode_text(
                        self._line('Saldo tarjeta', f'${float(remaining):.2f}') + '\n'
                    )
                    out += b'\x1b\x45\x00'

        hour_lines = self._compact_hours(settings.get('hours'))
        if hour_lines:
            out += self._sep('=')
            out += self._section_title('HORARIO')
            for hl in hour_lines:
                out += b'\x1b\x61\x01'
                out += self._encode_text(hl + '\n')
            out += b'\x1b\x61\x00'

        ssid = (settings.get('wifi_ssid') or '').strip()
        wifi = (settings.get('wifi_password') or '').strip()
        if ssid or wifi:
            out += self._sep('=')
            out += self._section_title('WIFI')
            out += b'\x1b\x61\x01'
            if ssid:
                out += self._encode_text(f'Red: {ssid}\n')
            if wifi:
                out += b'\x1b\x21\x10'
                out += self._encode_text(f'Clave: {wifi}\n')
                out += b'\x1b\x21\x00'
            out += b'\x1b\x61\x00'

        promo = (settings.get('promo_mes') or '').strip()
        if promo:
            out += self._sep('-')
            out += self._section_title('PROMO')
            out += b'\x1b\x61\x01'
            for line in self._wrap(promo):
                out += self._encode_text(line + '\n')
            out += b'\x1b\x61\x00'

        notes = (sale.get('notes') or '').strip()
        print_notes = sale.get('print_notes')
        if notes and print_notes is not False:
            out += self._sep('-')
            out += self._section_title('NOTAS')
            out += b'\x1b\x61\x00'
            for line in self._wrap(notes):
                out += self._encode_text(line + '\n')

        thanks = (settings.get('footer_thanks') or 'Gracias por tu compra').strip()
        out += self._sep('=')
        out += b'\x1b\x61\x01'
        out += b'\x1b\x21\x10'
        for line in self._wrap(thanks):
            out += self._encode_text(line + '\n')
        out += b'\x1b\x21\x00'
        out += b'\x1b\x61\x00'

        # Código de barras del folio
        out += self._sep('-')
        out += self._barcode_code128(folio)

        # Espacio final amplio antes del corte
        out += self._encode_text('\n\n\n\n\n\n')
        out += b'\x1d\x56\x00'
        return bytes(out), logo_debug

    def print_sale_ticket(
        self,
        sale: Dict[str, Any],
        card_balances: Optional[List[Dict[str, Any]]] = None,
        debug: bool = False,
    ) -> Dict[str, Any]:
        try:
            settings = self.store_repository.get_ticket_settings_for_print()
            payload, logo_debug = self.build_ticket_bytes(
                settings,
                sale,
                card_balances,
                include_logo_debug_line=False,
            )
            printer_used = self._send_raw(payload, settings.get('printer_name'))
            logger.info(
                f"Ticket impreso en '{printer_used}' ({len(payload)} bytes) "
                f"folio={sale.get('folio')} logo_ok={logo_debug.get('logo_ok')}"
            )
            return {
                'success': True,
                'message': 'Ticket impreso',
                'printer_used': printer_used,
            }
        except Exception as e:
            logger.error(f"Error imprimiendo ticket: {e}")
            return {
                'success': False,
                'message': f'No se pudo imprimir el ticket: {e}',
            }

    def print_test_ticket(self) -> Dict[str, Any]:
        sample_sale = {
            '_id': 'TEST',
            'folio': '202609-0042',
            'total_amount': 185.0,
            'employee_name': 'María López',
            'items': {
                'products': [
                    {'nombre': 'Jabón líquido', 'quantity': 2, 'subtotal': 40.0},
                    {'nombre': 'Suavizante', 'quantity': 1, 'subtotal': 25.0},
                    {'nombre': 'Bolsa ropa', 'quantity': 1, 'subtotal': 10.0},
                ],
                'services': [
                    {
                        'cycle_name': 'Lavado rápido',
                        'price': 45.0,
                    },
                    {
                        'cycle_name': 'Secado estándar',
                        'price': 65.0,
                    },
                ],
            },
            'payment_methods': [
                {'payment_type': 'efectivo', 'amount': 100.0},
                {'payment_type': 'tarjeta_recargable', 'amount': 85.0},
            ],
        }
        return self.print_sale_ticket(
            sample_sale,
            card_balances=[{'balance_after': 120.5}],
            debug=False,
        )

    def print_encargo_ticket(
        self,
        encargo: Dict[str, Any],
        employee_name: Optional[str] = None,
        print_notes: bool = True,
    ) -> Dict[str, Any]:
        """Ticket de cliente para encargo (detalle + pagos + barcode)."""
        products = []
        weight = float(encargo.get('weight_kg') or 0)
        ppk = float(encargo.get('price_per_kg') or 0)
        ppk_orig = encargo.get('price_per_kg_original')
        if weight > 0:
            products.append({
                'nombre': f'Lavado por kg ({weight:g} kg)',
                'quantity': 1,
                'subtotal': round(weight * ppk, 2),
            })
        servicios = encargo.get('servicios') or encargo.get('extras') or []
        for ex in servicios:
            qty = int(ex.get('qty') or 1)
            price = float(ex.get('price') or 0)
            size = (ex.get('size') or '').strip()
            # Solo nombre comercial; nunca el id interno del catálogo
            name = (ex.get('name') or '').strip() or 'Servicio'
            if name == str(ex.get('id') or ''):
                name = 'Servicio'
            label = f'{name}' + (f' {size}' if size else '')
            products.append({
                'nombre': label,
                'quantity': qty,
                'subtotal': round(price * qty, 2),
            })
        client = (encargo.get('client_name') or '').strip()
        phone = (encargo.get('client_phone') or '').strip()
        notes = (encargo.get('notes') or '').strip() if print_notes else ''
        sale_like = {
            '_id': encargo.get('_id'),
            'folio': encargo.get('folio'),
            'total_amount': encargo.get('total_amount'),
            'subtotal_before_discount': encargo.get('subtotal_before_discount'),
            'discount_amount': encargo.get('discount_amount'),
            'discount_reason': encargo.get('discount_reason'),
            'employee_name': employee_name,
            'items': {'products': products, 'services': []},
            'payment_methods': encargo.get('payment_methods') or [],
            'client_name': client,
            'client_phone': phone,
            'notes': notes,
            'print_notes': bool(print_notes),
            'price_per_kg_original': ppk_orig,
        }
        return self.print_sale_ticket(sale_like)

    def print_encargo_bag_label(self, encargo: Dict[str, Any]) -> Dict[str, Any]:
        """Etiqueta interna de bolsa: folio en una línea + nombre."""
        try:
            settings = self.store_repository.get_ticket_settings_for_print()
            folio = (encargo.get('folio') or '').strip() or 'SIN-FOLIO'
            name = (encargo.get('client_name') or '').strip() or 'Cliente'
            phone = (encargo.get('client_phone') or '').strip()
            now = datetime.now().strftime('%d/%m/%Y %H:%M')

            # ~32 chars útiles a ancho doble en 80mm; folio típico E-YYYYMM-NNNN = 13
            folio_line = folio if len(folio) <= 20 else folio[:20]

            out = bytearray()
            out += b'\x1b\x40'  # init
            out += b'\x1b\x74\x02'  # CP850
            out += b'\x1b\x61\x01'  # center
            # Doble alto+ancho (cabe en una línea a 80mm)
            out += b'\x1d\x21\x11'
            out += self._encode_text(folio_line + '\n')
            # Nombre normal / semi-doble
            out += b'\x1d\x21\x00'
            out += b'\x1b\x21\x10'
            out += self._encode_text(name[:28] + '\n')
            out += b'\x1b\x21\x00'
            if phone:
                out += self._encode_text(phone + '\n')
            out += self._encode_text(now + '\n')
            out += self._encode_text('COPIA TIENDA\n')
            out += self._encode_text('\n\n\n\n')
            out += b'\x1d\x56\x00'  # cut

            printer_used = self._send_raw(bytes(out), settings.get('printer_name'))
            return {
                'success': True,
                'message': 'Etiqueta de bolsa impresa',
                'printer_used': printer_used,
            }
        except Exception as e:
            logger.error(f"Error imprimiendo etiqueta bolsa: {e}")
            return {'success': False, 'message': str(e)}
