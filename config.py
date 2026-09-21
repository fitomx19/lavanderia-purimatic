import os
import sys
from datetime import timedelta
from dotenv import load_dotenv


def get_app_config_dir():
    """
    Obtener la carpeta donde debe vivir el archivo .env con la configuración
    de esta máquina (por ejemplo, la URI de MongoDB Atlas de esta tienda).

    - Si la app corre "congelada" (empaquetada con PyInstaller como .exe),
      NO se puede escribir dentro del paquete, así que se usa la carpeta
      donde vive el .exe (para que cada tienda tenga su propio .env editable
      junto al ejecutable, sin necesidad de reinstalar ni recompilar).
    - Si corre en modo desarrollo (python run.py), se usa la raíz del proyecto.
    """
    if getattr(sys, 'frozen', False):
        # Ejecutable generado por PyInstaller: usar la carpeta del .exe
        return os.path.dirname(sys.executable)
    # Modo desarrollo normal
    return os.path.dirname(os.path.abspath(__file__))


# Cargar variables de entorno desde el .env específico de esta máquina/tienda.
# Esto permite distribuir el mismo instalador a varias tiendas y que cada una
# solo tenga que editar su propio archivo .env con su URI de MongoDB Atlas.
APP_CONFIG_DIR = get_app_config_dir()
ENV_FILE_PATH = os.path.join(APP_CONFIG_DIR, '.env')
load_dotenv(dotenv_path=ENV_FILE_PATH)

# Si el .env no existe todavía (primer arranque en una máquina nueva),
# se avisa por consola para que se note de inmediato, en vez de fallar
# silenciosamente y conectar a un localhost que no existe en esa tienda.
if not os.path.exists(ENV_FILE_PATH):
    print(
        f"⚠️  No se encontró archivo de configuración en: {ENV_FILE_PATH}\n"
        f"   Se usarán valores por defecto (MongoDB local). "
        f"Crea un archivo .env junto al ejecutable con la URI de MongoDB Atlas de esta tienda."
    )


class Config:
    """Configuración base para la aplicación Flask"""
    
    # Configuración de Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_ALGORITHM = 'HS256'
    
    # Configuración de MongoDB
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/lavanderia_db'

    # Puente NFC + ESP32 (nfc-service). En la tienda corre en localhost:5001.
    ESP32_BRIDGE_URL = os.environ.get('ESP32_BRIDGE_URL', 'http://localhost:5001').rstrip('/')
    
    # Configuración de CORS
    CORS_ORIGINS = os.environ.get(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5000,http://127.0.0.1:5000',
    ).split(',')
    
    # Configuración de la aplicación
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    MONGODB_URI = os.environ.get('MONGODB_URI_TEST') or 'mongodb://localhost:27017/lavanderia_test_db'

# Mapeo de configuraciones
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

def get_config():
    """Obtener configuración según el entorno"""
    config_name = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(config_name, DevelopmentConfig)
