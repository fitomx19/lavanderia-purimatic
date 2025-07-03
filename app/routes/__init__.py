# Importaciones de rutas existentes
from .auth_routes import auth_bp
from .client_routes import client_bp
from .employee_routes import employee_bp
from .product_routes import product_bp
from .washer_routes import washer_bp
from .dryer_routes import dryer_bp

# Importaciones de rutas nuevas (Segunda Fase)
from .card_routes import card_bp
from .service_cycle_routes import service_cycle_bp
from .sale_routes import sale_bp

__all__ = [
    # Rutas existentes
    'auth_bp',
    'client_bp', 
    'employee_bp',
    'product_bp',
    'washer_bp',
    'dryer_bp',
    
    # Rutas nuevas (Segunda Fase)
    'card_bp',
    'service_cycle_bp',
    'sale_bp'
]
