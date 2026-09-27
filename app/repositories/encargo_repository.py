from typing import Dict, Any, Optional, List
from datetime import datetime
import re
from bson import ObjectId
from bson.errors import InvalidId
from pymongo import IndexModel, ASCENDING, DESCENDING, ReturnDocument
from app.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class EncargoRepository(BaseRepository):
    def __init__(self):
        super().__init__('encargos')
        self.create_indexes()

    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if '_id' in data:
            oid = data['_id']
            if isinstance(oid, str):
                oid = ObjectId(oid)
            return {'_id': oid}
        if 'folio' in data:
            return {'folio': data['folio']}
        return {}

    def create_indexes(self):
        indexes = [
            IndexModel([('folio', ASCENDING)], unique=True),
            IndexModel([('status', ASCENDING)]),
            IndexModel([('created_at', DESCENDING)]),
            IndexModel([('client_phone', ASCENDING)]),
            IndexModel([('client_name', ASCENDING)]),
        ]
        try:
            self.collection.create_indexes(indexes)
        except Exception as e:
            logger.warning(f"Índices encargos: {e}")

    def next_folio(self) -> str:
        period = datetime.utcnow().strftime('%Y%m')
        key = f'E-{period}'
        counters = self.db['sale_counters']
        result = counters.find_one_and_update(
            {'_id': key},
            {'$inc': {'seq': 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        seq = int((result or {}).get('seq') or 1)
        return f'E-{period}-{seq:04d}'

    def _serialize(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        out = dict(doc)
        if '_id' in out:
            out['_id'] = str(out['_id'])
        return out

    def create_encargo(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        payload = {
            **data,
            'folio': data.get('folio') or self.next_folio(),
            'status': 'recibida',
            'created_at': now,
            'updated_at': now,
            'recibida_at': now,
            'status_history': [
                {'status': 'recibida', 'at': now, 'employee_id': data.get('employee_id')},
            ],
        }
        result = self.collection.insert_one(payload)
        return self.find_by_id(str(result.inserted_id))

    def find_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc = self.collection.find_one({'_id': ObjectId(document_id)})
            return self._serialize(doc)
        except (InvalidId, TypeError):
            return None

    def find_by_folio(self, folio: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({'folio': str(folio).strip()})
        return self._serialize(doc)

    def list_encargos(
        self,
        status: Optional[str] = None,
        folio: Optional[str] = None,
        q: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {}
        if status:
            query['status'] = status
        term = (q or folio or '').strip()
        if term:
            if folio and not q:
                query['folio'] = str(folio).strip()
            else:
                escaped = re.escape(term)
                query['$or'] = [
                    {'folio': {'$regex': escaped, '$options': 'i'}},
                    {'client_name': {'$regex': escaped, '$options': 'i'}},
                ]
        return self.find_many(
            filter_criteria=query,
            page=page,
            per_page=per_page,
            sort_by='created_at',
            sort_order=-1,
        )

    def update_status(
        self,
        encargo_id: str,
        status: str,
        employee_id: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow()
        field_map = {
            'recibida': 'recibida_at',
            'en_lavado': 'en_lavado_at',
            'terminada': 'terminada_at',
            'entregada': 'entregada_at',
        }
        set_fields: Dict[str, Any] = {
            'status': status,
            'updated_at': now,
            field_map.get(status, 'updated_at'): now,
        }
        if extra_fields:
            set_fields.update(extra_fields)
        ops: Dict[str, Any] = {
            '$set': set_fields,
            '$push': {
                'status_history': {
                    'status': status,
                    'at': now,
                    'employee_id': employee_id,
                }
            },
        }
        self.collection.update_one({'_id': ObjectId(encargo_id)}, ops)
        return self.find_by_id(encargo_id)

    # --- settings singleton ---
    SETTINGS_KEY = 'default'

    def _settings_collection(self):
        return self.db['encargo_settings']

    def _flatten_legacy_extras(self, extras: list) -> list:
        flat = []
        for ex in extras or []:
            if not isinstance(ex, dict):
                continue
            if ex.get('sizes'):
                for sz in ex['sizes']:
                    flat.append({
                        'id': f"{ex.get('id', 's')}-{sz.get('size', '')}",
                        'name': ex.get('name') or 'Servicio',
                        'size': sz.get('size') or '',
                        'price': float(sz.get('price') or 0),
                    })
            else:
                flat.append({
                    'id': ex.get('id') or ex.get('name') or 's',
                    'name': ex.get('name') or 'Servicio',
                    'size': ex.get('size') or '',
                    'price': float(ex.get('price') or 0),
                })
        return flat

    def get_settings(self) -> Dict[str, Any]:
        from app.schemas.encargo_schema import default_encargo_settings

        defaults = default_encargo_settings()
        doc = self._settings_collection().find_one({'_id': self.SETTINGS_KEY})
        if not doc:
            return defaults
        servicios = doc.get('servicios')
        if not servicios and doc.get('extras'):
            servicios = self._flatten_legacy_extras(doc.get('extras'))
        if not servicios:
            servicios = defaults['servicios']
        price_tarjeta = doc.get('price_per_kg_tarjeta')
        return {
            'price_per_kg': float(doc.get('price_per_kg') or 25),
            'price_per_kg_tarjeta': float(price_tarjeta) if price_tarjeta is not None else None,
            'servicios': servicios,
            'print_bag_label': bool(doc.get('print_bag_label', True)),
            'print_notes': bool(doc.get('print_notes', True)),
            # compat lectura vieja
            'extras': servicios,
        }

    def upsert_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        servicios = data.get('servicios')
        if servicios is None:
            servicios = self._flatten_legacy_extras(data.get('extras') or [])
        price_tarjeta = data.get('price_per_kg_tarjeta')
        payload = {
            'price_per_kg': float(data.get('price_per_kg') or 25),
            'price_per_kg_tarjeta': float(price_tarjeta) if price_tarjeta not in (None, '') else None,
            'servicios': servicios or [],
            'print_bag_label': bool(data.get('print_bag_label', True)),
            'print_notes': bool(data.get('print_notes', True)),
            'updated_at': now,
        }
        self._settings_collection().update_one(
            {'_id': self.SETTINGS_KEY},
            {'$set': payload, '$setOnInsert': {'created_at': now}},
            upsert=True,
        )
        return self.get_settings()
