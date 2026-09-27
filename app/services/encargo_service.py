from typing import Dict, Any, Optional
from datetime import datetime
from app.repositories.encargo_repository import EncargoRepository
from app.repositories.card_repository import CardRepository
from app.schemas.encargo_schema import (
    encargo_create_schema,
    encargo_status_schema,
    encargo_settings_schema,
    encargo_response_schema,
    encargos_response_schema,
)
from marshmallow import ValidationError
import logging

logger = logging.getLogger(__name__)

STATUS_FLOW = {
    'recibida': 'en_lavado',
    'en_lavado': 'terminada',
    'terminada': 'entregada',
}


def _normalize_encargo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    d = dict(doc)
    if not isinstance(d.get('_id'), str) and d.get('_id') is not None:
        d['_id'] = str(d['_id'])
    servicios = d.get('servicios')
    if not servicios and d.get('extras'):
        servicios = d['extras']
    d['servicios'] = servicios or []
    d['extras'] = d['servicios']  # compat
    return d


class EncargoService:
    def __init__(self):
        self.repo = EncargoRepository()
        self.card_repository = CardRepository()

    def get_settings(self) -> Dict[str, Any]:
        return {'success': True, 'data': self.repo.get_settings()}

    def update_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            validated = encargo_settings_schema.load(data)
            # No persistir campo extras legacy
            validated.pop('extras', None)
            saved = self.repo.upsert_settings(validated)
            return {'success': True, 'data': saved, 'message': 'Configuración de encargos guardada'}
        except ValidationError as e:
            return {'success': False, 'message': 'Datos inválidos', 'errors': e.messages}

    def list_encargos(
        self,
        status: Optional[str] = None,
        folio: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        result = self.repo.list_encargos(
            status=status, folio=folio, q=q, page=page, per_page=per_page
        )
        serialized = [_normalize_encargo_doc(d) for d in result.get('documents', [])]
        return {
            'success': True,
            'data': {
                'encargos': encargos_response_schema.dump(serialized),
                'pagination': {
                    'page': result['page'],
                    'per_page': result['per_page'],
                    'total': result['total'],
                    'total_pages': result['total_pages'],
                },
            },
        }

    def _print_encargo_docs(self, encargo: Dict[str, Any], employee_id: str) -> Dict[str, Any]:
        from app.services.ticket_print_service import TicketPrintService
        from app.repositories.user_employee_repository import UserEmployeeRepository

        emp_name = None
        emp = UserEmployeeRepository().find_by_id(employee_id) if employee_id else None
        if emp:
            emp_name = emp.get('nombre') or emp.get('name') or emp.get('username')

        settings = self.repo.get_settings()
        print_notes = bool(settings.get('print_notes', True))

        printer = TicketPrintService()
        ticket_result = printer.print_encargo_ticket(
            encargo, emp_name, print_notes=print_notes
        )
        bag_printed = False
        bag_message = None
        if settings.get('print_bag_label', True):
            bag_result = printer.print_encargo_bag_label(encargo)
            bag_printed = bool(bag_result.get('success'))
            bag_message = bag_result.get('message')
        return {
            'ticket_printed': bool(ticket_result.get('success')),
            'ticket_message': ticket_result.get('message'),
            'bag_printed': bag_printed,
            'bag_message': bag_message,
        }

    def create_encargo(self, data: Dict[str, Any], employee_id: str) -> Dict[str, Any]:
        try:
            from app.repositories.store_repository import StoreRepository
            from app.schemas.card_benefits_schema import effective_pay_discount_style

            validated = encargo_create_schema.load(data)
            settings = self.repo.get_settings()
            price_per_kg_base = validated.get('price_per_kg')
            if price_per_kg_base is None:
                price_per_kg_base = float(settings.get('price_per_kg') or 25)
            else:
                price_per_kg_base = float(price_per_kg_base)

            weight = float(validated['weight_kg'])
            servicios = list(validated.get('servicios') or validated.get('extras') or [])
            payments = validated.get('payment_methods') or []

            benefits = StoreRepository().get_card_benefits_settings()
            style = effective_pay_discount_style(benefits)
            apply_discount = bool(style) and any(
                (pm or {}).get('payment_type') == 'tarjeta_recargable' for pm in payments
            )
            percent = float(benefits.get('pay_discount_percent') or 0)

            # Precios originales (sin descuento)
            kg_total_original = round(weight * price_per_kg_base, 2)
            servicios_enriched = []
            servicios_total_original = 0.0
            for e in servicios:
                price_orig = float(e.get('price') or 0)
                qty = int(e.get('qty') or 1)
                servicios_total_original += price_orig * qty
                servicios_enriched.append({
                    **e,
                    'price_original': price_orig,
                    'price': price_orig,
                    'qty': qty,
                    'savings': 0.0,
                })

            subtotal_before = round(kg_total_original + servicios_total_original, 2)
            price_per_kg = price_per_kg_base
            discount_amount = 0.0
            discount_reason = None

            if apply_discount and style == 'porcentaje' and percent > 0:
                factor = 1 - percent / 100.0
                price_per_kg = round(price_per_kg_base * factor, 4)
                for row in servicios_enriched:
                    final = round(float(row['price_original']) * factor, 2)
                    row['price'] = final
                    row['savings'] = round(float(row['price_original']) - final, 2)
            elif apply_discount and style == 'precio_ciclo':
                tarjeta_ppk = settings.get('price_per_kg_tarjeta')
                if tarjeta_ppk is not None:
                    price_per_kg = float(tarjeta_ppk)
                catalog = {str(s.get('id')): s for s in (settings.get('servicios') or [])}
                for row in servicios_enriched:
                    # Match by name+size in catalog if possible
                    matched = None
                    for s in settings.get('servicios') or []:
                        if (
                            (s.get('name') or '').strip().lower() == (row.get('name') or '').strip().lower()
                            and (s.get('size') or '') == (row.get('size') or '')
                        ):
                            matched = s
                            break
                    if matched and matched.get('price_tarjeta') is not None:
                        final = float(matched['price_tarjeta'])
                        row['price'] = final
                        row['savings'] = round(float(row['price_original']) - final, 2)

            kg_total = round(weight * float(price_per_kg), 2)
            servicios_total = sum(
                float(e.get('price') or 0) * int(e.get('qty') or 1) for e in servicios_enriched
            )
            total = round(kg_total + servicios_total, 2)
            discount_amount = round(max(0.0, subtotal_before - total), 2)
            if discount_amount > 0:
                discount_reason = 'tarjeta_recargable'

            paid = round(sum(float(p.get('amount') or 0) for p in payments), 2)
            if abs(paid - total) > 0.05:
                return {
                    'success': False,
                    'message': f'El pago (${paid:.2f}) no coincide con el total (${total:.2f})',
                }

            for pm in payments:
                if pm.get('payment_type') != 'tarjeta_recargable':
                    continue
                amount = float(pm['amount'])
                nfc_uid = pm.get('nfc_uid')
                card_id = pm.get('card_id')
                if nfc_uid:
                    result = self.card_repository.process_nfc_payment(
                        nfc_uid, amount, employee_id=employee_id, sale_id=None
                    )
                    if not result.get('success'):
                        return {
                            'success': False,
                            'message': result.get('message') or 'Error cobrando tarjeta NFC',
                        }
                elif card_id:
                    updated = self.card_repository.update_balance(
                        card_id, amount, 'subtract', employee_id, 'pago_venta'
                    )
                    if not updated:
                        return {'success': False, 'message': f'Error cobrando tarjeta {card_id}'}
                else:
                    return {
                        'success': False,
                        'message': 'NFC o card_id requerido para tarjeta recargable',
                    }

            payload = {
                'client_id': validated.get('client_id') or None,
                'client_name': (validated.get('client_name') or '').strip(),
                'client_phone': (validated.get('client_phone') or '').strip(),
                'weight_kg': weight,
                'price_per_kg': float(price_per_kg),
                'price_per_kg_original': float(price_per_kg_base),
                'servicios': servicios_enriched,
                'extras': servicios_enriched,
                'total_amount': total,
                'subtotal_before_discount': subtotal_before,
                'discount_amount': discount_amount,
                'discount_reason': discount_reason,
                'payment_methods': payments,
                'notes': (validated.get('notes') or '').strip(),
                'employee_id': employee_id,
            }
            encargo = self.repo.create_encargo(payload)
            if not encargo:
                return {'success': False, 'message': 'No se pudo crear el encargo'}
            encargo = _normalize_encargo_doc(encargo)

            print_info = {'ticket_printed': False, 'ticket_message': None}
            try:
                print_info = self._print_encargo_docs(encargo, employee_id)
            except Exception as pe:
                print_info['ticket_message'] = str(pe)
                logger.error(f"Error imprimiendo ticket encargo: {pe}")

            return {
                'success': True,
                'message': 'Encargo recibido y cobrado',
                'data': encargo_response_schema.dump(encargo),
                **print_info,
            }
        except ValidationError as e:
            return {'success': False, 'message': 'Datos inválidos', 'errors': e.messages}
        except Exception as e:
            logger.error(f"Error creando encargo: {e}")
            return {'success': False, 'message': 'Error interno al crear encargo'}

    def reprint(self, encargo_id: str, employee_id: str) -> Dict[str, Any]:
        doc = self.repo.find_by_id(encargo_id)
        if not doc:
            doc = self.repo.find_by_folio(encargo_id)
        if not doc:
            return {'success': False, 'message': 'Encargo no encontrado'}
        encargo = _normalize_encargo_doc(doc)
        try:
            print_info = self._print_encargo_docs(encargo, employee_id)
            return {
                'success': True,
                'message': 'Reimpresión enviada',
                'data': encargo_response_schema.dump(encargo),
                **print_info,
            }
        except Exception as e:
            logger.error(f"Error reimprimiendo encargo: {e}")
            return {'success': False, 'message': str(e)}

    def _activate_wash(
        self,
        encargo_id: str,
        machine_id: str,
        service_cycle_id: str,
    ) -> Dict[str, Any]:
        from app.services.sale_service import SaleService
        from app.repositories.service_cycle_repository import ServiceCycleRepository

        cycle_repo = ServiceCycleRepository()
        cycle = cycle_repo.find_by_id(service_cycle_id)
        if not cycle:
            return {'success': False, 'message': 'Ciclo de servicio no encontrado'}

        duration = int(cycle.get('duration_minutes') or 0)
        if duration <= 0:
            return {'success': False, 'message': 'El ciclo no tiene duración válida'}

        sale_svc = SaleService()
        machine = sale_svc._get_machine_by_id(machine_id)
        if not machine:
            return {'success': False, 'message': 'Máquina no encontrada'}
        estado = (machine.get('estado') or 'disponible').lower()
        if estado not in ('disponible', 'available'):
            return {
                'success': False,
                'message': f'La máquina no está disponible (estado: {estado})',
            }

        machine_name = (
            machine.get('nombre')
            or machine.get('name')
            or f"#{machine.get('numero', '')}"
        ).strip()

        # Asegurar tipo para mark/activate
        is_washer = bool(sale_svc.washer_repository.find_by_id(machine_id))
        machine_tipo = 'lavadora' if is_washer else 'secadora'
        try:
            if is_washer:
                sale_svc.washer_repository.upsert({'_id': machine_id, 'tipo': 'lavadora'})
            else:
                sale_svc.dryer_repository.upsert({'_id': machine_id, 'tipo': 'secadora'})
        except Exception:
            pass

        sale_svc._mark_machine_occupied_on_sale_creation(
            machine_id, encargo_id, 0, service_cycle_id
        )
        try:
            update_data = {
                'estado': 'ocupada',
                'tipo': machine_tipo,
                'current_service': {
                    'sale_id': encargo_id,
                    'service_index': 0,
                    'service_cycle_id': service_cycle_id,
                    'encargo_id': encargo_id,
                },
            }
            if is_washer:
                sale_svc.washer_repository.upsert({'_id': machine_id, **update_data})
            else:
                sale_svc.dryer_repository.upsert({'_id': machine_id, **update_data})
        except Exception as mark_err:
            logger.warning(f"Re-mark machine: {mark_err}")

        ok, started_at, _end = sale_svc._activate_machine_service(
            machine_id, encargo_id, 0, service_cycle_id, duration
        )
        if not ok:
            err = getattr(sale_svc, '_esp32_last_error', None) or 'No se pudo encender la máquina'
            try:
                revert = {'estado': 'disponible', 'current_service': None}
                if is_washer:
                    sale_svc.washer_repository.upsert({'_id': machine_id, **revert})
                else:
                    sale_svc.dryer_repository.upsert({'_id': machine_id, **revert})
            except Exception as rev_err:
                logger.error(f"Error revirtiendo máquina tras fallo ESP32: {rev_err}")
            return {'success': False, 'message': err}

        return {
            'success': True,
            'extra_fields': {
                'machine_id': machine_id,
                'machine_name': machine_name,
                'service_cycle_id': service_cycle_id,
                'wash_started_at': started_at or datetime.utcnow(),
            },
        }

    def update_status(
        self,
        encargo_id: str,
        data: Dict[str, Any],
        employee_id: str,
    ) -> Dict[str, Any]:
        try:
            if isinstance(data, str):
                data = {'status': data}
            validated = encargo_status_schema.load(data or {})
            new_status = validated['status']
            existing = self.repo.find_by_id(encargo_id)
            if not existing:
                return {'success': False, 'message': 'Encargo no encontrado'}
            current = existing.get('status')
            expected = STATUS_FLOW.get(current)
            if new_status != expected and new_status != current:
                if expected and new_status != expected:
                    return {
                        'success': False,
                        'message': f'Desde "{current}" solo puedes pasar a "{expected}"',
                    }

            extra_fields = None
            if new_status == 'en_lavado' and current != 'en_lavado':
                machine_id = (validated.get('machine_id') or '').strip()
                cycle_id = (validated.get('service_cycle_id') or '').strip()
                if not machine_id or not cycle_id:
                    return {
                        'success': False,
                        'message': 'Para pasar a en lavado elige máquina y ciclo de lavado',
                    }
                act = self._activate_wash(encargo_id, machine_id, cycle_id)
                if not act.get('success'):
                    return act
                extra_fields = act.get('extra_fields')

            updated = self.repo.update_status(
                encargo_id, new_status, employee_id, extra_fields=extra_fields
            )
            return {
                'success': True,
                'message': f'Estado actualizado a {new_status}',
                'data': encargo_response_schema.dump(_normalize_encargo_doc(updated)),
            }
        except ValidationError as e:
            return {'success': False, 'message': 'Estado inválido', 'errors': e.messages}
        except Exception as e:
            logger.error(f"Error actualizando estado encargo: {e}")
            return {'success': False, 'message': 'Error interno'}

    def get_encargo(self, encargo_id: str) -> Dict[str, Any]:
        doc = self.repo.find_by_id(encargo_id)
        if not doc:
            doc = self.repo.find_by_folio(encargo_id)
        if not doc:
            return {'success': False, 'message': 'Encargo no encontrado'}
        return {'success': True, 'data': encargo_response_schema.dump(_normalize_encargo_doc(doc))}
