#!/usr/bin/env python3
"""
Microservicio NFC - Punto de entrada principal
Maneja lectores ACR122U para sistema de lavandería
"""

from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.routes.nfc_routes import nfc_bp
from app.utils.logger import setup_logging
from app.utils.response_utils import error_response
import logging

def create_app():
    """Crear y configurar la aplicación Flask"""
    app = Flask(__name__)
    
    # Configurar CORS para desarrollo
    CORS(app)
    
    # Configurar logging
    setup_logging()
    
    # Registrar blueprints
    app.register_blueprint(nfc_bp, url_prefix='/')
    
    # Manejo de errores globales
    @app.errorhandler(404)
    def not_found(error):
        return error_response("Endpoint no encontrado", 404)
    
    @app.errorhandler(500)
    def internal_error(error):
        return error_response("Error interno del servidor", 500)
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger = logging.getLogger(__name__)
    
    try:
        port = Config.FLASK_PORT
        debug = Config.FLASK_DEBUG
        
        logger.info(f"🚀 Iniciando microservicio NFC en puerto {port}")
        logger.info(f"🔧 Modo debug: {debug}")
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug
        )
    except Exception as e:
        logger.error(f"❌ Error al iniciar el servicio: {str(e)}")
