#!/bin/bash
# Reanuda exclusivamente la instalación que falló antes de crear PostgreSQL.
set -euo pipefail
umask 077
stage="$(cd -- "$(dirname -- "$0")" && pwd)"
app=/opt/apps/croquis3r
data=/data/projects/croquis3r
test "$(id -u)" = 0 || { echo 'Ejecuta con sudo.' >&2; exit 1; }
test "$(hostname)" = servidor4 || { echo 'Servidor incorrecto.' >&2; exit 1; }
test "$(findmnt -n -o UUID /data)" = f47d4231-2fcd-4624-b038-3fea030a37b5 || { echo 'Montaje incorrecto.' >&2; exit 1; }
test -f "$app/.env.production" || { echo 'Falta la configuración inicial; detener.' >&2; exit 1; }
cd "$app"
dc() { docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml "$@"; }
dc config --quiet
if [ -n "$(dc ps -aq)" ]; then echo 'Ya existen contenedores Croquis3R; detener para revisar.' >&2; exit 1; fi
if ss -H -ltn | awk '{print $4}' | grep -Eq '(^|:)8013$'; then echo 'Puerto 8013 ocupado.' >&2; exit 1; fi
python3 - "$stage" "$data" <<'PY'
import hashlib, json, pathlib, sys
stage, data = map(pathlib.Path, sys.argv[1:])
manifest = json.loads((stage/'release.json').read_text())
assert manifest['release'] == '20261021'
fixture = stage/'initial-data.json'
assert hashlib.sha256(fixture.read_bytes()).hexdigest() == manifest['files'][fixture.name]['sha256']
pg = data/'postgres'
assert not pg.exists() or (pg.is_dir() and not any(pg.iterdir())), 'PostgreSQL ya tiene archivos: detener.'
assert not (data/'persistent/initial-admin-password').exists(), 'Ya se creó el acceso inicial: detener.'
print('Instalación parcial verificada; se conservan configuración y datos de origen.')
PY
numeric_owner() {
  # Ubuntu 26.04 usa uutils install: evitar resolución NSS para UID/GID de contenedor.
  python3 - "$1" "$2" "$3" <<'PY'
import os, sys
os.chown(sys.argv[1], int(sys.argv[2].strip()), int(sys.argv[3].strip()))
PY
}
pg_uid="$(docker run --rm --network none --entrypoint id postgres:18-bookworm -u postgres)"
pg_gid="$(docker run --rm --network none --entrypoint id postgres:18-bookworm -g postgres)"
install -d -m 0700 "$data/postgres"
numeric_owner "$data/postgres" "$pg_uid" "$pg_gid"
dc build app
dc up -d --wait db
dc run --rm -T app python manage.py migrate --noinput
install -m 0400 "$stage/initial-data.json" "$data/persistent/initial-data.json"
numeric_owner "$data/persistent/initial-data.json" 10001 10001
dc run --rm -T -v "$data/persistent/initial-data.json:/restore/initial-data.json:ro" app python manage.py loaddata /restore/initial-data.json
dc run --rm -T -v "$data/persistent/initial-data.json:/restore/initial-data.json:ro" app python manage.py shell <<'PY'
import json
from django.apps import apps
records = json.load(open('/restore/initial-data.json'))
counts = {}
for row in records:
    model = apps.get_model(row['model'])
    actual = model.objects.get(pk=row['pk'])
    for name in ('document', 'specification', 'inputs', 'result', 'revision', 'name', 'project', 'customer', 'notes'):
        if name in row['fields']:
            assert getattr(actual, name) == row['fields'][name], (row['model'], row['pk'], name)
    counts[row['model']] = counts.get(row['model'], 0) + 1
for label, count in counts.items():
    assert apps.get_model(label).objects.count() == count, label
print('Importación comprobada:', counts)
PY
# Contraseña inicial recuperable únicamente desde la cuenta administradora del servidor.
install -d -m 0700 -o administrador -g administrador /home/administrador/.config/croquis3r
python3 - <<'PY'
from pathlib import Path
import secrets
password = secrets.token_urlsafe(24)
Path('/data/projects/croquis3r/persistent/initial-admin-password').write_text(password)
Path('/home/administrador/.config/croquis3r/acceso-inicial.txt').write_text(
    'URL: http://192.168.0.214:8013/\nUsuario: croquis_admin\nContraseña: ' + password + '\n')
PY
numeric_owner "$data/persistent/initial-admin-password" 10001 10001
chmod 0400 "$data/persistent/initial-admin-password"
chown administrador:administrador /home/administrador/.config/croquis3r/acceso-inicial.txt
chmod 0600 /home/administrador/.config/croquis3r/acceso-inicial.txt
dc run --rm -T -v "$data/persistent/initial-admin-password:/run/initial-admin-password:ro" app python manage.py shell <<'PY'
from pathlib import Path
from django.contrib.auth import get_user_model
get_user_model().objects.create_superuser('croquis_admin', '', Path('/run/initial-admin-password').read_text())
print('Cuenta inicial creada; contraseña en archivo privado del administrador.')
PY
dc up -d --wait app
curl --fail --silent http://192.168.0.214:8013/health/
dc exec -T app python manage.py check --deploy --fail-level ERROR
dc exec -T app python manage.py shell <<'PY'
from django.test import Client
from django.contrib.auth import get_user_model
client = Client(HTTP_HOST='192.168.0.214:8013')
assert client.get('/').status_code == 302
client.force_login(get_user_model().objects.get(username='croquis_admin'))
for url in ('/', '/calculador-casas/', '/atenciones/', '/api/sketches/'):
    response = client.get(url)
    assert response.status_code == 200, (url, response.status_code)
print('Acceso del equipo, editor, calculador y datos: comprobados.')
PY
dc ps
docker image inspect croquis3r-app:20261021 postgres:18-bookworm --format '{{.Id}} {{json .RepoDigests}}' > "$data/persistent/deployed-images.txt"
install -m 0600 "$stage/release.json" "$data/persistent/release.json"
echo 'Croquis3R disponible en http://192.168.0.214:8013/'
echo 'Acceso inicial: /home/administrador/.config/croquis3r/acceso-inicial.txt (archivo privado).'
echo 'Piloto LAN HTTP. Respaldos externos y conexión con artículos comerciales siguen pendientes.'
