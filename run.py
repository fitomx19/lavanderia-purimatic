from app import create_app
from config import get_config

# Crear la aplicación Flask
app = create_app(get_config())

if __name__ == '__main__':
    app.run(
        debug=app.config['DEBUG'],
        host='0.0.0.0',
        port=5000
    )
