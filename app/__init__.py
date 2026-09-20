import os
import time
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    ServerSelectionTimeoutError,
    ConfigurationError,
    OperationFailure,
)
import logging
from flask_socketio import SocketIO # Importar SocketIO
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Instancia global de MongoDB
mongo_client = None
db = None
socketio = None # Añadir una instancia global para SocketIO
scheduler = None # Añadir una instancia global para el scheduler

def create_app(config_class):
    """
    Factory pattern para crear la aplicación Flask
    
    Args:
        config_class: Clase de configuración a usar
        
    Returns:
        app: Instancia de la aplicación Flask configurada
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configurar logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    
    # Inicializar extensiones
    init_extensions(app) # Esto ahora inicializará SocketIO
    
    # Inicializar base de datos
    init_database(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Configurar manejo de errores
    configure_error_handlers(app)
    
    # Inicializar scheduler de monitoreo
    init_scheduler(app)
    
    return app

def init_extensions(app):
    """Inicializar extensiones de Flask y SocketIO"""
    global socketio # Acceder a la variable global
    
    # Configurar JWT
    jwt = JWTManager(app)
    
    # Configurar CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Inicializar Flask-SocketIO
    socketio = SocketIO(app, cors_allowed_origins=app.config['CORS_ORIGINS'])
    
    # Configurar JWT callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        # Aquí podrías implementar una lista de tokens revocados
        return False
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from app.utils.response_utils import error_response
        return error_response('Token ha expirado', 401)
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        from app.utils.response_utils import error_response
        return error_response('Token inválido', 401)
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from app.utils.response_utils import error_response
        return error_response('Token de autorización requerido', 401)

def init_database(app, max_retries=3, retry_delay_seconds=3):
    """
    Inicializar conexión a MongoDB (Atlas, distinto por tienda).

    Reintenta varias veces antes de rendirse, porque en las máquinas de las
    tiendas es común que el internet tarde unos segundos en estar listo justo
    cuando arranca la aplicación. Si todos los intentos fallan, se muestra un
    mensaje claro indicando qué revisar según el tipo exacto de error.
    """
    global mongo_client, db

    mongo_uri = app.config['MONGODB_URI']
    last_error = None

    for intento in range(1, max_retries + 1):
        try:
            mongo_client = MongoClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            # Probar la conexión de verdad (MongoClient() es "perezoso")
            mongo_client.admin.command('ping')

            # Atlas a veces llega sin nombre de base en la URI
            # (mongodb+srv://...mongodb.net/?retryWrites=true). En ese caso
            # el split tradicional deja el nombre vacío y la app "conecta"
            # a una BD que no es la de la tienda.
            from urllib.parse import urlparse
            parsed = urlparse(mongo_uri)
            db_name = (parsed.path or '').lstrip('/').split('?')[0]
            if not db_name:
                db_name = os.environ.get('MONGODB_DB_NAME', 'lavanderia_purimatic')
            db = mongo_client[db_name]

            app.logger.info(f"Conectado exitosamente a MongoDB: {db_name}")
            return

        except ConfigurationError as e:
            # URI mal formada, típicamente el SRV de Atlas mal copiado
            # o falta dnspython. Reintentar no ayuda aquí.
            app.logger.error(
                "❌ Error de configuración en MONGODB_URI. Revisa que la URI "
                "de MongoDB Atlas esté completa y bien copiada (mongodb+srv://usuario:password@cluster.mongodb.net/basedatos). "
                f"Detalle: {e}"
            )
            raise

        except OperationFailure as e:
            # Conectó al cluster pero las credenciales/permisos fallan.
            app.logger.error(
                "❌ MongoDB Atlas rechazó las credenciales. Revisa el usuario y "
                "contraseña de la URI, y que ese usuario tenga permisos sobre la base de datos. "
                f"Detalle: {e}"
            )
            raise

        except ServerSelectionTimeoutError as e:
            last_error = e
            app.logger.warning(
                f"⚠️ Intento {intento}/{max_retries}: no se pudo contactar a MongoDB Atlas "
                "(revisa: conexión a internet de esta máquina, y en Atlas > Network Access "
                "que la IP de esta tienda esté permitida, ej. 0.0.0.0/0 para cualquier IP). "
                f"Detalle: {e}"
            )

        except ConnectionFailure as e:
            last_error = e
            app.logger.warning(
                f"⚠️ Intento {intento}/{max_retries}: fallo de conexión a MongoDB. Detalle: {e}"
            )

        if intento < max_retries:
            time.sleep(retry_delay_seconds)

    app.logger.error(
        "❌ No se pudo conectar a MongoDB Atlas después de varios intentos. "
        "Checklist para esta tienda:\n"
        "  1) ¿Hay conexión a internet en esta máquina?\n"
        "  2) ¿La URI en el archivo .env (junto al ejecutable) es la correcta de esta tienda?\n"
        "  3) En MongoDB Atlas > Network Access, ¿está permitida la IP de esta tienda?\n"
        "  4) ¿El usuario/contraseña de la URI siguen siendo válidos?\n"
        f"Último error: {last_error}"
    )
    raise last_error

def register_blueprints(app):
    """Registrar blueprints de la aplicación"""
    
    # Importar blueprints existentes
    from app.routes.auth_routes import auth_bp
    from app.routes.employee_routes import employee_bp
    from app.routes.client_routes import client_bp
    from app.routes.product_routes import product_bp
    from app.routes.washer_routes import washer_bp
    from app.routes.dryer_routes import dryer_bp
    
    # Importar blueprints nuevos (Segunda Fase)
    from app.routes.card_routes import card_bp
    from app.routes.service_cycle_routes import service_cycle_bp
    from app.routes.sale_routes import sale_bp
    
    # Registrar blueprints existentes
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(employee_bp, url_prefix='/employees')
    app.register_blueprint(client_bp, url_prefix='/clients')
    app.register_blueprint(product_bp, url_prefix='/products')
    app.register_blueprint(washer_bp, url_prefix='/washers')
    app.register_blueprint(dryer_bp, url_prefix='/dryers')
    
    # Registrar blueprints nuevos (Segunda Fase)
    app.register_blueprint(card_bp, url_prefix='/api')
    app.register_blueprint(service_cycle_bp, url_prefix='/api')
    app.register_blueprint(sale_bp, url_prefix='/api')

def configure_error_handlers(app):
    """Configurar manejadores de errores"""
    
    from app.utils.response_utils import error_response
    
    @app.errorhandler(404)
    def not_found(error):
        return error_response('Recurso no encontrado', 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Error interno del servidor: {error}')
        return error_response('Error interno del servidor', 500)
    
    @app.errorhandler(400)
    def bad_request(error):
        return error_response('Solicitud incorrecta', 400)
    
    @app.errorhandler(403)
    def forbidden(error):
        return error_response('Acceso prohibido', 403)

def get_db():
    """Obtener instancia de la base de datos"""
    global db
    if db is None:
        raise RuntimeError("Base de datos no inicializada")
    return db

def init_scheduler(app):
    """Inicializar scheduler para monitoreo automático de máquinas"""
    global scheduler
    
    try:
        if not scheduler:
            scheduler = BackgroundScheduler()
            
            # Importar aquí para evitar imports circulares
            from app.services.machine_monitor import machine_monitor
            
            # Programar verificación cada 30 segundos
            scheduler.add_job(
                func=machine_monitor.check_and_notify_completed_services,
                trigger="interval",
                seconds=30,
                id='machine_monitor',
                name='Monitor de máquinas y servicios',
                replace_existing=True
            )
            
            # Iniciar scheduler
            scheduler.start()
            app.logger.info("✅ Scheduler de monitoreo iniciado - verificando cada 30 segundos")
            
            # Asegurar que el scheduler se cierre correctamente al terminar la aplicación
            atexit.register(lambda: scheduler.shutdown() if scheduler else None)
            
    except Exception as e:
        app.logger.error(f"❌ Error al inicializar scheduler: {e}")
