"""Inventario sin configuración privada: python -m config.security_inventory [--verify]."""
import importlib.metadata
import json
import platform
import sqlite3
import ssl
import sys


def inventory():
    packages = {}
    for name in ('Django', 'asgiref', 'gunicorn', 'packaging', 'psycopg', 'psycopg-binary',
                 'pymssql', 'python-dotenv', 'sqlparse', 'typing_extensions', 'tzdata',
                 'whitenoise', 'pip', 'reportlab', 'Pillow', 'charset-normalizer'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    from psycopg import pq
    return {'python': platform.python_version(), 'openssl': ssl.OPENSSL_VERSION,
            'sqlite': sqlite3.sqlite_version, 'libpq': pq.version(), 'packages': packages}


def main():
    data = inventory()
    print(json.dumps(data, indent=2))
    if '--verify' in sys.argv:
        from packaging.version import Version
        version = Version(data['python'])
        floors = {(3, 12): '3.12.15', (3, 13): '3.13.17', (3, 14): '3.14.9', (3, 15): '3.15.1'}
        floor = floors.get(version.release[:2])
        assert floor and version >= Version(floor), 'Python requiere parche de seguridad o revisión de su serie.'
        expected = {'Django': '5.2.18', 'asgiref': '3.13.0', 'pymssql': '2.4.5', 'pip': '26.2.2',
                    'reportlab': '5.1.0', 'Pillow': '13.0.0', 'charset-normalizer': '3.5.2'}
        if sys.platform != 'win32':
            expected['gunicorn'] = '26.2.2'
        for name, version in expected.items():
            assert data['packages'][name] == version, f'Versión inesperada: {name}'


if __name__ == '__main__':
    main()
