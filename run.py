import os
import sys
import threading
import webbrowser
import time


def _build_app():
    from app import create_app
    from config import get_config
    return create_app(get_config())


def _open_browser(port):
    def _go():
        time.sleep(1.5)
        webbrowser.open(f'http://127.0.0.1:{port}')
    threading.Thread(target=_go, daemon=True).start()


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

    if frozen:
        _open_browser(port)

    run_kwargs = {
        'debug': False if frozen else app.config['DEBUG'],
        'host': host,
        'port': port,
        'use_reloader': False,
    }
    # Solo el servidor Werkzeug entiende este flag. Con gevent/eventlet lo rechaza.
    if getattr(socketio, 'async_mode', 'threading') == 'threading':
        run_kwargs['allow_unsafe_werkzeug'] = True

    socketio.run(app, **run_kwargs)


if __name__ == '__main__':
    main()
else:
    # Importación para depuración / WSGI: asume que el .env ya existe
    app = _build_app()
