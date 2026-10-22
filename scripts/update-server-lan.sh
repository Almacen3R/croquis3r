#!/bin/bash
# Actualiza exclusivamente Croquis3R desde un bundle Git verificado y sin importar datos locales.
set -euo pipefail
umask 077
stage="$(cd -- "$(dirname -- "$0")" && pwd)"
app=/opt/apps/croquis3r
data=/data/projects/croquis3r
test "$(id -u)" = 0 || { echo 'Ejecuta con sudo.' >&2; exit 1; }
test "$(hostname)" = servidor4 || { echo 'Servidor incorrecto.' >&2; exit 1; }
test "$(findmnt -n -o UUID /data)" = f47d4231-2fcd-4624-b038-3fea030a37b5 || { echo 'Montaje /data incorrecto.' >&2; exit 1; }
test -f "$app/.env.production" || { echo 'Falta la instalación existente.' >&2; exit 1; }
python3 - "$stage" <<'PY'
import hashlib,json,pathlib,sys
base=pathlib.Path(sys.argv[1])
manifest=json.loads((base/'update.json').read_text())
for name,expected in manifest['files'].items():
    assert pathlib.Path(name).name==name
    assert hashlib.sha256((base/name).read_bytes()).hexdigest()==expected, name
assert len(manifest['commit'])==40 and all(c in '0123456789abcdef' for c in manifest['commit'])
print('Paquete de actualización: SHA-256 verificado.')
PY
commit="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"])' "$stage/update.json")"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup="$data/backup-staging/update-$stamp"
install -d -m 0700 "$backup"
cd "$app"
dc() { docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml "$@"; }
dc config --quiet
test -n "$(dc ps -q db)" || { echo 'La base de Croquis3R no está iniciada.' >&2; exit 1; }
old_release="$(python3 - <<'PY'
from pathlib import Path
entries=dict(line.split('=',1) for line in Path('.env.production').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
print(entries['CROQUIS_RELEASE'])
PY
)"
old_image="croquis3r-app:$old_release"
docker image inspect "$old_image" > /dev/null
cp -p .env.production "$backup/env.production"
tar --exclude='./.git' --exclude='./.env*' --exclude='./secrets' --exclude='./backups' --exclude='./.deploy' -czf "$backup/source-before.tar.gz" .
dc exec -T db pg_dump -U croquis3r_app -d croquis3r -Fc > "$backup/database.dump"
dc exec -T db pg_restore --list < "$backup/database.dump" > "$backup/database.contents"
test -s "$backup/database.dump"
sha256sum "$backup/database.dump" > "$backup/database.sha256"
capture_business() {
  dc exec -T app python manage.py shell --command "import hashlib,json; from django.core import serializers; from catalog.models import Article; from sketches.models import Sketch,ObjectTemplate,Attention; models=(Article,Sketch,ObjectTemplate,Attention); rows=[json.loads(serializers.serialize('json',m.objects.order_by('pk'))) for m in models]; [entry['fields'].setdefault('owner',None) for group,model in zip(rows,models) if model is not Article for entry in group]; print('BUSINESS:'+json.dumps({'counts':{m._meta.label_lower:len(r) for m,r in zip(models,rows)},'sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,ensure_ascii=True).encode()).hexdigest()},sort_keys=True))" | sed -n 's/^BUSINESS://p'
}
capture_business > "$backup/business-before.json"
test -s "$backup/business-before.json"
g() { git -c safe.directory="$app" -C "$app" "$@"; }
if [ -d .git ]; then
  test -z "$(g status --porcelain --untracked-files=no)" || { echo 'Hay cambios locales versionados; detener para revisar.' >&2; exit 1; }
else
  g init -b main
fi
if g remote get-url origin > /dev/null 2>&1; then
  test "$(g remote get-url origin)" = https://github.com/Almacen3R/croquis3r.git || { echo 'Remoto Git inesperado.' >&2; exit 1; }
else
  g remote add origin https://github.com/Almacen3R/croquis3r.git
fi
g bundle verify "$stage/croquis3r.bundle"
bundle_commit="$(g bundle list-heads "$stage/croquis3r.bundle" refs/heads/main | awk '{print $1}')"
test "$bundle_commit" = "$commit" || { echo 'El commit del bundle no coincide.' >&2; exit 1; }
g fetch "$stage/croquis3r.bundle" refs/heads/main
new_release="git-${commit:0:12}"
switched=0
code_updated=0
old_commit="$(g rev-parse --verify HEAD 2>/dev/null || true)"
on_failure() {
  status=$?
  trap - ERR
  echo "Actualización interrumpida. Respaldo conservado en $backup" >&2
  cp -p "$backup/env.production" .env.production
  if [ "$switched" = 1 ]; then
    echo "Intentando recuperar la imagen anterior: $old_image" >&2
    dc up -d --no-deps --wait --wait-timeout 120 app || true
  fi
  if [ "$code_updated" = 1 ]; then
    if [ -n "$old_commit" ]; then g checkout -f -B main "$old_commit" || true;
    else tar -xzf "$backup/source-before.tar.gz" -C "$app" || true; fi
  fi
  echo 'No se restauró ni sobrescribió la base de datos. Revisar el diagnóstico antes de reintentar.' >&2
  exit "$status"
}
trap on_failure ERR
# El contenido previo está respaldado; .env.production y datos no están versionados.
code_updated=1
g checkout -f -B main "$commit"
g update-ref refs/remotes/origin/main "$commit"
g branch --set-upstream-to=origin/main main
chown -R administrador:administrador "$app"
python3 - "$new_release" <<'PY'
from pathlib import Path
import sys
path=Path('.env.production')
rows=path.read_text().splitlines()
assert sum(row.startswith('CROQUIS_RELEASE=') for row in rows)==1
path.write_text('\n'.join('CROQUIS_RELEASE='+sys.argv[1] if row.startswith('CROQUIS_RELEASE=') else row for row in rows)+'\n')
path.chmod(0o600)
PY
dc config --quiet
dc build app
dc run --rm --no-deps -T app python manage.py check
# Solo se autoriza aquí la migración aditiva de propietarios: campos nulos,
# sin asignar autorías históricas, borrar filas ni cambiar documentos/resultados.
dc run --rm --no-deps -T app python manage.py shell --command "from django.db import connection; from django.db.migrations.executor import MigrationExecutor; executor=MigrationExecutor(connection); plan=executor.migration_plan(executor.loader.graph.leaf_nodes()); assert all(not backwards and (migration.app_label,migration.name)==('sketches','0003_record_owners') for migration,backwards in plan), 'Migraciones inesperadas; revisar antes de continuar.'; print('Plan de migraciones permitido:',[(m.app_label,m.name) for m,_ in plan])"
# Las pruebas usan una base de prueba PostgreSQL independiente de croquis3r.
dc run --rm --no-deps -T app python manage.py test sketches catalog
# Evitar escrituras de la imagen anterior durante la migración y comprobación.
# El rollback conserva esta extensión nullable compatible con la imagen anterior.
switched=1
dc stop app
dc run --rm --no-deps -T app python manage.py migrate --noinput
dc up -d --no-deps --wait --wait-timeout 120 app
curl --fail --silent http://192.168.0.214:8013/health/
dc exec -T app python manage.py shell <<'PY'
from django.test import Client
from django.contrib.auth import get_user_model
c=Client(HTTP_HOST='192.168.0.214:8013')
assert c.get('/').status_code==302
user=get_user_model().objects.filter(is_superuser=True,is_active=True).first()
assert user is not None, 'Falta una cuenta del equipo.'
c.force_login(user)
for url in ('/','/calculador-casas/','/atenciones/','/api/sketches/'):
    assert c.get(url).status_code==200,url
response=c.post('/api/suggest-panels/',data='{"meters":"7.5"}',content_type='application/json')
assert response.status_code==200
assert response.json()['panels']==4
assert c.get('/salir/').status_code==405
assert c.post('/salir/').status_code==302
assert c.get('/api/sketches/').status_code==403
print('Editor, calculador, atenciones, distribución y cierre de sesión: OK.')
PY
capture_business > "$backup/business-after.json"
python3 - "$backup" <<'PY'
import json,pathlib,sys
path=pathlib.Path(sys.argv[1])
before=json.loads((path/'business-before.json').read_text())
after=json.loads((path/'business-after.json').read_text())
assert before==after,'Los registros comerciales cambiaron durante el despliegue; revisar sin restaurar automáticamente.'
print('Registros conservados:',after['counts'])
PY
docker image inspect "croquis3r-app:$new_release" --format '{{.Id}}' > "$backup/deployed-image.txt"
printf '%s\n' "$commit" > "$backup/deployed-commit.txt"
dc ps
trap - ERR
echo "Actualización terminada: $commit"
echo 'Croquis3R: http://192.168.0.214:8013/ · conservar usuario y contraseña actuales.'
echo "Respaldo previo: $backup"
