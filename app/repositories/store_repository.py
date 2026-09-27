from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
from app.repositories.base_repository import BaseRepository
from pymongo import IndexModel, ASCENDING
import logging

logger = logging.getLogger(__name__)

class StoreRepository(BaseRepository):
    """
    Repositorio para tiendas con operaciones UPSERT
    """
    
    def __init__(self):
        super().__init__('stores')
        self.create_indexes()
    
    def _get_unique_filter(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtener filtro basado en campos únicos para tiendas
        
        Args:
            data: Datos de la tienda
            
        Returns:
            Dict: Filtro basado en nombre
        """
        filter_criteria = {}
        
        if 'nombre' in data:
            filter_criteria['nombre'] = data['nombre']
        
        return filter_criteria
    
    def find_by_nombre(self, nombre: str) -> Optional[Dict[str, Any]]:
        """
        Encontrar tienda por nombre
        
        Args:
            nombre: Nombre de la tienda
            
        Returns:
            Dict: Tienda encontrada o None
        """
        return self.find_one({'nombre': nombre, 'is_active': True})
    
    def find_active_stores(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Encontrar todas las tiendas activas
        
        Args:
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Dict: Tiendas encontradas con información de paginación
        """
        return self.find_many(
            filter_criteria={'is_active': True},
            page=page,
            per_page=per_page
        )
    
    def create_indexes(self):
        """
        Crear índices para optimizar consultas
        """
        indexes = [
            IndexModel([('nombre', ASCENDING)], unique=True),
            IndexModel([('is_active', ASCENDING)]),
            IndexModel([('created_at', ASCENDING)])
        ]
        
        self.collection.create_indexes(indexes)
        self._create_esp32_config_indexes()

    def _esp32_collection(self):
        return self.db['esp32_config']

    def _create_esp32_config_indexes(self):
        """Índice único en esp32_ids (cada ID solo en una placa) + is_active."""
        collection = self._esp32_collection()
        # Quitar índice legacy de un solo esp32_id si existe
        for index_name in ('esp32_id_1',):
            try:
                collection.drop_index(index_name)
            except Exception:
                pass
        indexes = [
            IndexModel([('esp32_ids', ASCENDING)], unique=True),
            IndexModel([('is_active', ASCENDING)]),
        ]
        try:
            collection.create_indexes(indexes)
        except Exception as e:
            logger.warning(f"No se pudieron crear índices esp32_config: {e}")

    def _serialize_esp32_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return None
        serialized = dict(doc)
        if '_id' in serialized:
            serialized['_id'] = str(serialized['_id'])

        # Normalizar modelo nuevo: esp32_ids[]
        ids = serialized.get('esp32_ids')
        if not isinstance(ids, list) or len(ids) == 0:
            legacy = serialized.get('esp32_id')
            serialized['esp32_ids'] = [str(legacy)] if legacy else []
        else:
            serialized['esp32_ids'] = [str(x).strip() for x in ids if str(x).strip()]

        if 'name' not in serialized or serialized.get('name') is None:
            serialized['name'] = ''

        return serialized

    def _find_board_by_relay_id(self, esp32_id: str, active_only: bool = False) -> Optional[Dict[str, Any]]:
        """Buscar placa que contenga el esp32_id (modelo nuevo o legacy)."""
        cfg = self._esp32_collection()
        eid = str(esp32_id)
        query_active = {'is_active': True} if active_only else {}
        doc = (
            cfg.find_one({**query_active, 'esp32_ids': eid})
            or cfg.find_one({'esp32_ids': eid})
            or cfg.find_one({**query_active, 'esp32_id': eid})
            or cfg.find_one({'esp32_id': eid})
        )
        return doc

    def _ids_conflict(self, esp32_ids: List[str], exclude_board_id: Optional[str] = None) -> Optional[str]:
        """Devuelve el primer esp32_id que ya pertenece a otra placa."""
        cfg = self._esp32_collection()
        for eid in esp32_ids:
            query = {
                '$or': [
                    {'esp32_ids': eid},
                    {'esp32_id': eid},
                ]
            }
            if exclude_board_id:
                try:
                    query['_id'] = {'$ne': ObjectId(exclude_board_id)}
                except (InvalidId, TypeError):
                    pass
            other = cfg.find_one(query)
            if other:
                return eid
        return None

    # --- ESP32 CONFIG ---
    def get_esp32_url_by_id(self, esp32_id: str) -> Optional[str]:
        """
        Obtener la URL del ESP32 desde la colección 'esp32_config'.
        Modelo nuevo:
          { esp32_ids: ["W001","W002"], esp32_url: "http://.../laundry-update", is_active: true }
        Compatible con docs legacy { esp32_id, esp32_url }.
        """
        try:
            doc = self._find_board_by_relay_id(str(esp32_id), active_only=True)
            if not doc:
                doc = self._find_board_by_relay_id(str(esp32_id), active_only=False)
            if not doc:
                return None
            return doc.get('esp32_url') or doc.get('url')
        except Exception as e:
            logger.error(f"Error obteniendo esp32_url para esp32_id={esp32_id}: {e}")
            return None

    def get_esp32_config_by_id(self, esp32_id: str) -> Optional[Dict[str, Any]]:
        """Obtener placa que contenga el esp32_id (relay) indicado."""
        try:
            doc = self._find_board_by_relay_id(str(esp32_id))
            return self._serialize_esp32_doc(doc)
        except Exception as e:
            logger.error(f"Error obteniendo esp32_config para esp32_id={esp32_id}: {e}")
            return None

    def get_esp32_config_by_board_id(self, board_id: str) -> Optional[Dict[str, Any]]:
        """Obtener placa por _id de MongoDB."""
        try:
            doc = self._esp32_collection().find_one({'_id': ObjectId(board_id)})
            return self._serialize_esp32_doc(doc)
        except (InvalidId, TypeError) as e:
            logger.error(f"board_id inválido {board_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error obteniendo esp32_config board={board_id}: {e}")
            return None

    def list_esp32_configs(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Listar placas; fusiona automáticamente docs con la misma URL."""
        try:
            self.merge_boards_by_url()
            query = {} if include_inactive else {'is_active': True}
            docs = list(self._esp32_collection().find(query))
            serialized = [self._serialize_esp32_doc(doc) for doc in docs]
            serialized.sort(key=lambda d: (d.get('name') or '', d.get('esp32_url') or ''))
            return serialized
        except Exception as e:
            logger.error(f"Error listando esp32_config: {e}")
            return []

    @staticmethod
    def _normalize_board_url(url: str) -> str:
        return (url or '').strip().rstrip('/').lower()

    def merge_boards_by_url(self) -> int:
        """
        Una URL = una placa. Fusiona documentos duplicados (legacy)
        en uno solo con todos los esp32_ids y elimina el resto.
        Returns: número de documentos eliminados.
        """
        try:
            cfg = self._esp32_collection()
            docs = list(cfg.find({}))
            by_url: Dict[str, List[Dict[str, Any]]] = {}
            for doc in docs:
                url = self._normalize_board_url(doc.get('esp32_url') or doc.get('url') or '')
                if not url:
                    continue
                by_url.setdefault(url, []).append(doc)

            removed = 0
            now = datetime.utcnow()
            for url, group in by_url.items():
                if len(group) <= 1:
                    continue
                # Preferir activa; si empatan, la más antigua
                group.sort(
                    key=lambda d: (
                        0 if d.get('is_active', True) else 1,
                        d.get('created_at') or now,
                    )
                )
                primary = group[0]
                merged_ids = []
                seen = set()
                name = primary.get('name') or ''
                is_active = False
                for d in group:
                    if d.get('is_active', True):
                        is_active = True
                    if d.get('name') and not name:
                        name = d.get('name')
                    ids = d.get('esp32_ids') if isinstance(d.get('esp32_ids'), list) else []
                    if not ids and d.get('esp32_id'):
                        ids = [str(d.get('esp32_id'))]
                    for eid in ids:
                        eid = str(eid).strip()
                        if eid and eid not in seen:
                            seen.add(eid)
                            merged_ids.append(eid)

                cfg.update_one(
                    {'_id': primary['_id']},
                    {
                        '$set': {
                            'esp32_url': primary.get('esp32_url') or primary.get('url'),
                            'esp32_ids': merged_ids,
                            'name': name or primary.get('name') or '',
                            'is_active': is_active,
                            'updated_at': now,
                        },
                        '$unset': {'esp32_id': ''},
                    },
                )
                for d in group[1:]:
                    cfg.delete_one({'_id': d['_id']})
                    removed += 1
                logger.info(
                    f"Fusionadas {len(group)} placas con URL {url} -> "
                    f"{len(merged_ids)} máquinas en {primary['_id']}"
                )
            return removed
        except Exception as e:
            logger.error(f"Error fusionando placas por URL: {e}")
            return 0

    def find_board_by_url(self, esp32_url: str) -> Optional[Dict[str, Any]]:
        url = self._normalize_board_url(esp32_url)
        if not url:
            return None
        for doc in self._esp32_collection().find({}):
            if self._normalize_board_url(doc.get('esp32_url') or doc.get('url') or '') == url:
                return self._serialize_esp32_doc(doc)
        return None

    def upsert_esp32_config(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Crear o actualizar una placa ESP32.
        Una placa = una URL + varios esp32_ids.
        Si data._id está presente, actualiza esa placa; si no, crea una nueva
        (o fusiona en la existente si la URL ya existe).
        """
        try:
            esp32_url = str(data.get('esp32_url', '')).strip()
            raw_ids = data.get('esp32_ids')
            if isinstance(raw_ids, str):
                esp32_ids = [p.strip() for p in raw_ids.split(',') if p.strip()]
            elif isinstance(raw_ids, list):
                esp32_ids = [str(x).strip() for x in raw_ids if str(x).strip()]
            else:
                esp32_ids = []
            if not esp32_ids and data.get('esp32_id'):
                esp32_ids = [str(data.get('esp32_id')).strip()]

            if not esp32_url:
                return None

            board_id = data.get('_id') or data.get('board_id')

            # Sin _id: si ya hay placa con esa URL, actualizarla (no duplicar)
            if not board_id:
                existing_by_url = self.find_board_by_url(esp32_url)
                if existing_by_url:
                    board_id = existing_by_url['_id']
                    # Unir IDs nuevos con los existentes
                    existing_ids = existing_by_url.get('esp32_ids') or []
                    merged = list(existing_ids)
                    for eid in esp32_ids:
                        if eid not in merged:
                            merged.append(eid)
                    esp32_ids = merged
                    if not data.get('name') and existing_by_url.get('name'):
                        data = dict(data)
                        data['name'] = existing_by_url.get('name')

            conflict = self._ids_conflict(esp32_ids, exclude_board_id=str(board_id) if board_id else None)
            if conflict:
                logger.error(f"esp32_id {conflict} ya está asignado a otra placa")
                return None

            now = datetime.utcnow()
            payload = {
                'name': str(data.get('name') or '').strip(),
                'esp32_url': esp32_url,
                'esp32_ids': esp32_ids,
                'is_active': bool(data.get('is_active', True)),
                'updated_at': now,
            }
            unset_legacy = {'esp32_id': ''}

            if board_id:
                try:
                    oid = ObjectId(board_id)
                except (InvalidId, TypeError):
                    return None
                self._esp32_collection().update_one(
                    {'_id': oid},
                    {'$set': payload, '$unset': unset_legacy},
                )
                return self.get_esp32_config_by_board_id(str(board_id))

            payload['created_at'] = now
            result = self._esp32_collection().insert_one(payload)
            return self.get_esp32_config_by_board_id(str(result.inserted_id))
        except Exception as e:
            logger.error(f"Error guardando esp32_config: {e}")
            return None

    def update_esp32_config_by_board_id(self, board_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualización parcial de una placa por _id."""
        existing = self.get_esp32_config_by_board_id(board_id)
        if not existing:
            return None
        merged = {
            '_id': board_id,
            'name': data.get('name', existing.get('name', '')),
            'esp32_url': data.get('esp32_url', existing.get('esp32_url')),
            'esp32_ids': data.get('esp32_ids', existing.get('esp32_ids')),
            'is_active': data.get('is_active', existing.get('is_active', True)),
        }
        return self.upsert_esp32_config(merged)

    def deactivate_esp32_config_by_board_id(self, board_id: str) -> Optional[Dict[str, Any]]:
        """Soft-delete: is_active=false."""
        return self.update_esp32_config_by_board_id(board_id, {'is_active': False})

    # --- TICKET SETTINGS (singleton) ---
    TICKET_SETTINGS_KEY = 'default'

    def _ticket_settings_collection(self):
        return self.db['ticket_settings']

    def get_ticket_settings(self, include_logo: bool = False) -> Dict[str, Any]:
        """Obtener configuración de ticket (crea defaults si no existe)."""
        try:
            from app.schemas.ticket_settings_schema import default_ticket_hours

            doc = self._ticket_settings_collection().find_one({'_id': self.TICKET_SETTINGS_KEY})
            if not doc:
                doc = {
                    '_id': self.TICKET_SETTINGS_KEY,
                    'store_name': 'Lavandería Purimatic',
                    'address': '',
                    'wifi_ssid': '',
                    'wifi_password': '',
                    'promo_mes': '',
                    'footer_thanks': 'Gracias por tu compra',
                    'printer_name': '',
                    'hours': default_ticket_hours(),
                    'logo_base64': None,
                    'logo_mime': None,
                }
            hours = doc.get('hours')
            if not hours:
                hours = default_ticket_hours()
            result = {
                'store_name': doc.get('store_name') or '',
                'address': doc.get('address') or '',
                'wifi_ssid': doc.get('wifi_ssid') or '',
                'wifi_password': doc.get('wifi_password') or '',
                'promo_mes': doc.get('promo_mes') or '',
                'footer_thanks': doc.get('footer_thanks') or 'Gracias por tu compra',
                'printer_name': doc.get('printer_name') or '',
                'hours': hours,
                'logo_mime': doc.get('logo_mime'),
                'has_logo': bool(doc.get('logo_base64')),
                'updated_at': doc.get('updated_at'),
            }
            if include_logo and doc.get('logo_base64'):
                result['logo_base64'] = doc.get('logo_base64')
            return result
        except Exception as e:
            logger.error(f"Error obteniendo ticket_settings: {e}")
            from app.schemas.ticket_settings_schema import default_ticket_hours
            return {
                'store_name': 'Lavandería Purimatic',
                'address': '',
                'wifi_ssid': '',
                'wifi_password': '',
                'promo_mes': '',
                'footer_thanks': 'Gracias por tu compra',
                'printer_name': '',
                'hours': default_ticket_hours(),
                'logo_mime': None,
                'has_logo': False,
            }

    def get_ticket_settings_for_print(self) -> Dict[str, Any]:
        """Settings completos incluyendo logo para impresión."""
        try:
            from app.schemas.ticket_settings_schema import default_ticket_hours

            doc = self._ticket_settings_collection().find_one({'_id': self.TICKET_SETTINGS_KEY}) or {}
            return {
                'store_name': doc.get('store_name') or 'Lavandería Purimatic',
                'address': doc.get('address') or '',
                'wifi_ssid': doc.get('wifi_ssid') or '',
                'wifi_password': doc.get('wifi_password') or '',
                'promo_mes': doc.get('promo_mes') or '',
                'footer_thanks': doc.get('footer_thanks') or 'Gracias por tu compra',
                'printer_name': doc.get('printer_name') or '',
                'hours': doc.get('hours') or default_ticket_hours(),
                'logo_base64': doc.get('logo_base64'),
                'logo_mime': doc.get('logo_mime'),
            }
        except Exception as e:
            logger.error(f"Error obteniendo ticket_settings para print: {e}")
            from app.schemas.ticket_settings_schema import default_ticket_hours
            return {
                'store_name': 'Lavandería Purimatic',
                'address': '',
                'wifi_ssid': '',
                'wifi_password': '',
                'promo_mes': '',
                'footer_thanks': 'Gracias por tu compra',
                'printer_name': '',
                'hours': default_ticket_hours(),
                'logo_base64': None,
                'logo_mime': None,
            }

    def upsert_ticket_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar configuración de ticket."""
        try:
            from app.schemas.ticket_settings_schema import default_ticket_hours

            now = datetime.utcnow()
            existing = self._ticket_settings_collection().find_one({'_id': self.TICKET_SETTINGS_KEY}) or {}
            hours = data.get('hours')
            if hours is None:
                hours = existing.get('hours') or default_ticket_hours()

            payload = {
                'store_name': str(data.get('store_name', existing.get('store_name', '')) or ''),
                'address': str(data.get('address', existing.get('address', '')) or ''),
                'wifi_ssid': str(data.get('wifi_ssid', existing.get('wifi_ssid', '')) or ''),
                'wifi_password': str(data.get('wifi_password', existing.get('wifi_password', '')) or ''),
                'promo_mes': str(data.get('promo_mes', existing.get('promo_mes', '')) or ''),
                'footer_thanks': str(
                    data.get('footer_thanks', existing.get('footer_thanks', 'Gracias por tu compra'))
                    or 'Gracias por tu compra'
                ),
                'printer_name': str(data.get('printer_name', existing.get('printer_name', '')) or ''),
                'hours': hours,
                'updated_at': now,
            }

            if data.get('clear_logo'):
                payload['logo_base64'] = None
                payload['logo_mime'] = None
            elif data.get('logo_base64'):
                raw = str(data['logo_base64'])
                if ',' in raw and raw.strip().lower().startswith('data:'):
                    raw = raw.split(',', 1)[1]
                payload['logo_base64'] = raw.strip()
                payload['logo_mime'] = data.get('logo_mime') or existing.get('logo_mime') or 'image/png'
            else:
                payload['logo_base64'] = existing.get('logo_base64')
                payload['logo_mime'] = existing.get('logo_mime')

            self._ticket_settings_collection().update_one(
                {'_id': self.TICKET_SETTINGS_KEY},
                {'$set': payload, '$setOnInsert': {'created_at': now}},
                upsert=True,
            )
            return self.get_ticket_settings(include_logo=False)
        except Exception as e:
            logger.error(f"Error guardando ticket_settings: {e}")
            raise

    # --- CARD BENEFITS SETTINGS (singleton) ---
    CARD_BENEFITS_KEY = 'default'

    def _card_benefits_collection(self):
        return self.db['card_benefits_settings']

    def get_card_benefits_settings(self) -> Dict[str, Any]:
        from app.schemas.card_benefits_schema import default_card_benefits_settings

        defaults = default_card_benefits_settings()
        try:
            doc = self._card_benefits_collection().find_one({'_id': self.CARD_BENEFITS_KEY})
            if not doc:
                return dict(defaults)
            packages = doc.get('reload_packages')
            if packages is None:
                packages = defaults['reload_packages']
            return {
                'reload_bonus_enabled': bool(doc.get('reload_bonus_enabled', False)),
                'reload_promo_mode': doc.get('reload_promo_mode') or defaults['reload_promo_mode'],
                'reload_packages': packages or [],
                'reload_bonus_percent': float(doc.get('reload_bonus_percent') or 0),
                'pay_discount_enabled': bool(doc.get('pay_discount_enabled', False)),
                'pay_discount_mode': doc.get('pay_discount_mode') or defaults['pay_discount_mode'],
                'pay_discount_style': doc.get('pay_discount_style') or defaults['pay_discount_style'],
                'pay_discount_percent': float(doc.get('pay_discount_percent') or 0),
                'updated_at': doc.get('updated_at'),
            }
        except Exception as e:
            logger.error(f"Error obteniendo card_benefits_settings: {e}")
            return dict(defaults)

    def upsert_card_benefits_settings(self, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        payload = {
            'reload_bonus_enabled': bool(data.get('reload_bonus_enabled', False)),
            'reload_promo_mode': data.get('reload_promo_mode') or 'paquetes_y_libre',
            'reload_packages': data.get('reload_packages') or [],
            'reload_bonus_percent': float(data.get('reload_bonus_percent') or 0),
            'pay_discount_enabled': bool(data.get('pay_discount_enabled', False)),
            'pay_discount_mode': data.get('pay_discount_mode') or 'elegir_pct_o_precio',
            'pay_discount_style': data.get('pay_discount_style') or 'porcentaje',
            'pay_discount_percent': float(data.get('pay_discount_percent') or 0),
            'updated_at': now,
        }
        self._card_benefits_collection().update_one(
            {'_id': self.CARD_BENEFITS_KEY},
            {'$set': payload, '$setOnInsert': {'created_at': now}},
            upsert=True,
        )
        return self.get_card_benefits_settings()
