# Importaciones de schemas existentes
from .user_client_schema import (
    user_client_schema,
    user_client_update_schema,
    user_client_balance_schema,
    user_client_response_schema,
    users_client_response_schema
)

from .user_employee_schema import (
    user_employee_schema,
    user_employee_update_schema,
    user_employee_response_schema,
    users_employee_response_schema
)

from .product_schema import (
    product_schema,
    product_update_schema,
    product_response_schema,
    products_response_schema
)

from .washer_schema import (
    washer_schema,
    washer_update_schema,
    washer_response_schema,
    washers_response_schema
)

from .dryer_schema import (
    dryer_schema,
    dryer_update_schema,
    dryer_response_schema,
    dryers_response_schema
)

# Importaciones de schemas nuevos (Segunda Fase)
from .card_schema import (
    card_schema,
    card_update_schema,
    card_balance_schema,
    card_transfer_schema,
    card_response_schema,
    cards_response_schema
)

from .service_cycle_schema import (
    service_cycle_schema,
    service_cycle_update_schema,
    service_cycle_response_schema,
    service_cycles_response_schema
)

from .sale_schema import (
    sale_schema,
    sale_update_schema,
    sale_response_schema,
    sales_response_schema
)

__all__ = [
    # Schemas existentes
    'user_client_schema',
    'user_client_update_schema',
    'user_client_balance_schema',
    'user_client_response_schema',
    'users_client_response_schema',
    'user_employee_schema',
    'user_employee_update_schema',
    'user_employee_response_schema',
    'users_employee_response_schema',
    'product_schema',
    'product_update_schema',
    'product_response_schema',
    'products_response_schema',
    'washer_schema',
    'washer_update_schema',
    'washer_response_schema',
    'washers_response_schema',
    'dryer_schema',
    'dryer_update_schema',
    'dryer_response_schema',
    'dryers_response_schema',
    
    # Schemas nuevos (Segunda Fase)
    'card_schema',
    'card_update_schema',
    'card_balance_schema',
    'card_transfer_schema',
    'card_response_schema',
    'cards_response_schema',
    'service_cycle_schema',
    'service_cycle_update_schema',
    'service_cycle_response_schema',
    'service_cycles_response_schema',
    'sale_schema',
    'sale_update_schema',
    'sale_response_schema',
    'sales_response_schema'
]
