"""
Asistente de primer arranque para cada máquina/tienda.

Cada tienda tiene su propio clúster de MongoDB Atlas. Este asistente
pide la URI, la prueba de verdad (ping) y guarda un .env junto al
ejecutable. No requiere Python instalado cuando corre empaquetado:
tkinter viaja dentro del .exe de PyInstaller.
"""

import os
import sys
import secrets
from urllib.parse import urlparse, urlunparse


def get_config_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_env_path():
    return os.path.join(get_config_dir(), '.env')


def ensure_store_configuration():
    """
    Si ya hay .env con URI de Atlas, no molesta.
    Si falta (primer arranque o --setup), abre el asistente.
    Devuelve True si la app puede continuar.
    """
    force_setup = '--setup' in sys.argv
    env_path = get_env_path()

    if force_setup:
        return run_wizard(env_path)

    if os.path.exists(env_path):
        # En la tienda (.exe) un .env con localhost no sirve: reabrir asistente.
        # En desarrollo, respetar el .env aunque sea Mongo local.
        if getattr(sys, 'frozen', False) and not _env_has_atlas_uri(env_path):
            return run_wizard(env_path)
        return True

    return run_wizard(env_path)


def _env_has_atlas_uri(env_path):
    try:
        with open(env_path, 'r', encoding='utf-8') as handle:
            content = handle.read()
    except OSError:
        return False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith('#') or '=' not in stripped:
            continue
        key, value = stripped.split('=', 1)
        if key.strip() != 'MONGODB_URI':
            continue
        uri = value.strip().strip('"').strip("'")
        return uri.startswith('mongodb+srv://') or (
            uri.startswith('mongodb://') and 'localhost' not in uri
        )
    return False


def normalize_atlas_uri(raw_uri, db_name):
    """Asegura esquema Atlas y que la URI lleve nombre de base de datos."""
    uri = (raw_uri or '').strip().strip('"').strip("'")
    if not uri:
        raise ValueError('Pega la URI de MongoDB Atlas de esta tienda.')

    if not (uri.startswith('mongodb+srv://') or uri.startswith('mongodb://')):
        raise ValueError(
            'La URI debe empezar con mongodb+srv:// (Atlas) o mongodb://.'
        )

    parsed = urlparse(uri)
    if not parsed.hostname:
        raise ValueError('La URI no tiene host. Cópiala completa desde Atlas > Connect.')

    current_db = (parsed.path or '').lstrip('/').split('?')[0]
    target_db = (db_name or current_db or 'lavanderia_purimatic').strip()
    if not target_db:
        target_db = 'lavanderia_purimatic'

    query = parsed.query
    if 'retryWrites' not in query:
        extra = 'retryWrites=true&w=majority'
        query = f'{query}&{extra}' if query else extra

    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc,
        f'/{target_db}',
        '',
        query,
        '',
    ))
    return normalized, target_db


def test_mongodb_connection(uri):
    """Prueba real contra Atlas. Devuelve (ok, mensaje_en_español)."""
    from pymongo import MongoClient
    from pymongo.errors import (
        ConfigurationError,
        ConnectionFailure,
        OperationFailure,
        ServerSelectionTimeoutError,
    )

    client = None
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=8000,
            connectTimeoutMS=8000,
        )
        client.admin.command('ping')
        return True, 'Conexión correcta con MongoDB Atlas.'
    except ConfigurationError as exc:
        return False, (
            'La URI está mal formada. Cópiala otra vez desde Atlas > Connect > Drivers.\n'
            'Si la contraseña tiene caracteres especiales (@ : / # ?), hay que codificarla.\n'
            f'Detalle: {exc}'
        )
    except OperationFailure as exc:
        return False, (
            'Atlas rechazó usuario o contraseña. Revisa Database Access.\n'
            f'Detalle: {exc}'
        )
    except ServerSelectionTimeoutError as exc:
        return False, (
            'No se pudo contactar el clúster. Revisa:\n'
            '  1) Internet de esta máquina\n'
            '  2) Atlas > Network Access: agrega la IP de esta tienda o 0.0.0.0/0\n'
            '  3) Que el clúster no esté pausado\n'
            f'Detalle: {exc}'
        )
    except ConnectionFailure as exc:
        return False, f'Fallo de conexión con Atlas.\nDetalle: {exc}'
    except Exception as exc:
        return False, f'No se pudo probar la URI.\nDetalle: {exc}'
    finally:
        if client is not None:
            client.close()


def write_env_file(env_path, uri, db_name):
    os.makedirs(os.path.dirname(env_path) or '.', exist_ok=True)

    existing = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or '=' not in stripped:
                    continue
                key, value = stripped.split('=', 1)
                existing[key.strip()] = value.strip().strip('"')

    secret_key = existing.get('SECRET_KEY') or secrets.token_hex(32)
    jwt_key = existing.get('JWT_SECRET_KEY') or secrets.token_hex(32)

    content = (
        '# Configuración de esta tienda. No compartir.\n'
        '# Generado por el asistente de Purimatic.\n'
        'FLASK_ENV=production\n'
        f'MONGODB_URI="{uri}"\n'
        f'MONGODB_DB_NAME={db_name}\n'
        f'SECRET_KEY={secret_key}\n'
        f'JWT_SECRET_KEY={jwt_key}\n'
        'JWT_ACCESS_TOKEN_EXPIRES=86400\n'
        'CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173\n'
        'HOST=0.0.0.0\n'
        'PORT=5000\n'
    )
    with open(env_path, 'w', encoding='utf-8') as handle:
        handle.write(content)

    os.environ['MONGODB_URI'] = uri
    os.environ['MONGODB_DB_NAME'] = db_name
    os.environ['SECRET_KEY'] = secret_key
    os.environ['JWT_SECRET_KEY'] = jwt_key
    os.environ['FLASK_ENV'] = 'production'


def encode_password_hint(uri):
    """Ayuda visual: si hay un segundo @ en userinfo, la contraseña no está codificada."""
    if '://' not in uri:
        return ''
    rest = uri.split('://', 1)[1]
    host_part = rest.split('/', 1)[0]
    if host_part.count('@') > 1:
        return (
            'La contraseña parece contener @. En Atlas hay que usar la versión '
            'codificada (%40 en lugar de @).'
        )
    return ''


def run_wizard(env_path):
    try:
        import tkinter as tk
        from tkinter import messagebox
    except ImportError:
        print(
            'No se pudo abrir el asistente gráfico. Crea a mano el archivo:\n'
            f'  {env_path}\n'
            'con la línea MONGODB_URI="mongodb+srv://..." de esta tienda.'
        )
        return False

    result = {'ok': False}

    root = tk.Tk()
    root.title('Purimatic — Configurar esta tienda')
    root.geometry('760x520')
    root.resizable(False, False)

    pad = {'padx': 16, 'pady': 6}

    tk.Label(
        root,
        text='Configuración de MongoDB Atlas para esta tienda',
        font=('Segoe UI', 14, 'bold'),
    ).pack(anchor='w', **pad)

    tk.Label(
        root,
        text=(
            'Cada tienda usa su propia cuenta/clúster de Atlas.\n'
            'Pega la URI de Connect > Drivers. En Network Access permite la IP de esta máquina '
            'o 0.0.0.0/0.'
        ),
        justify='left',
        wraplength=720,
    ).pack(anchor='w', padx=16)

    tk.Label(root, text='URI de MongoDB Atlas', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=16, pady=(12, 0))
    uri_var = tk.StringVar()
    uri_entry = tk.Entry(root, textvariable=uri_var, width=98)
    uri_entry.pack(anchor='w', padx=16)
    uri_entry.focus_set()

    tk.Label(root, text='Nombre de la base de datos', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=16, pady=(12, 0))
    db_var = tk.StringVar(value='lavanderia_purimatic')
    tk.Entry(root, textvariable=db_var, width=40).pack(anchor='w', padx=16)

    status_var = tk.StringVar(value=f'El archivo se guardará en:\n{env_path}')
    status = tk.Label(root, textvariable=status_var, justify='left', wraplength=720, fg='#333333')
    status.pack(anchor='w', padx=16, pady=12)

    buttons = tk.Frame(root)
    buttons.pack(fill='x', padx=16, pady=8)

    def set_busy(busy):
        state = 'disabled' if busy else 'normal'
        test_btn.config(state=state)
        save_btn.config(state=state)
        root.update_idletasks()

    def do_test(save_if_ok=False):
        raw = uri_var.get()
        hint = encode_password_hint(raw)
        try:
            uri, db_name = normalize_atlas_uri(raw, db_var.get())
        except ValueError as exc:
            status_var.set(str(exc))
            messagebox.showerror('URI inválida', str(exc))
            return False

        if hint:
            status_var.set(hint)

        set_busy(True)
        status_var.set('Probando conexión con Atlas (unos segundos)...')
        root.update()
        ok, message = test_mongodb_connection(uri)
        set_busy(False)

        if not ok:
            status_var.set(message)
            messagebox.showerror('No se pudo conectar', message)
            return False

        db_var.set(db_name)
        status_var.set(message + f'\nBase de datos: {db_name}')
        if save_if_ok:
            write_env_file(env_path, uri, db_name)
            result['ok'] = True
            messagebox.showinfo(
                'Listo',
                f'Configuración guardada.\n\n{env_path}\n\nLa API arrancará en http://localhost:5000',
            )
            root.destroy()
        else:
            messagebox.showinfo('Conexión correcta', message)
        return True

    test_btn = tk.Button(buttons, text='Probar conexión', width=20, command=lambda: do_test(False))
    test_btn.pack(side='left', padx=(0, 8))

    save_btn = tk.Button(
        buttons,
        text='Guardar y continuar',
        width=22,
        command=lambda: do_test(True),
    )
    save_btn.pack(side='left', padx=8)

    def cancel():
        if os.path.exists(env_path) and _env_has_atlas_uri(env_path):
            result['ok'] = True
            root.destroy()
            return
        if messagebox.askyesno('Salir', 'Sin URI de Atlas la aplicación no puede arrancar. ¿Salir?'):
            result['ok'] = False
            root.destroy()

    tk.Button(buttons, text='Cancelar', width=12, command=cancel).pack(side='right')
    root.protocol('WM_DELETE_WINDOW', cancel)
    root.mainloop()
    return result['ok']


__all__ = ['ensure_store_configuration', 'normalize_atlas_uri', 'test_mongodb_connection']
