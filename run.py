import os
import sys


def _build_app():
    from app import create_app
    from config import get_config
    return create_app(get_config())


def main():
    from setup_wizard import ensure_store_configuration

    if not ensure_store_configuration():
        print('No se guardó la URI de MongoDB Atlas. La aplicación no arrancará.')
        raise SystemExit(1)

    app = _build_app()
    from app import socketio

    frozen = getattr(sys, 'frozen', False)
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f'Purimatic listo en http://127.0.0.1:{port}')
    print('Para reconfigurar Atlas de esta tienda, cierra y vuelve a abrir con --setup')

    socketio.run(
        app,
        debug=False if frozen else app.config['DEBUG'],
        host=host,
        port=port,
        allow_unsafe_werkzeug=True,
        use_reloader=False,
    )


if __name__ == '__main__':
    main()
else:
    # Importación para depuración / WSGI: asume que el .env ya existe
    app = _build_app()
