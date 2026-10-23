#!/bin/bash
# Instalación administrativa explícita. Autoriza SOLO el paquete 897308d80fbf.
# No permite comandos libres, Docker general ni elegir otro script/commit.
set -euo pipefail
umask 077
test "$(id -u)" = 0 || { echo 'Ejecutar con sudo desde una terminal del administrador.' >&2; exit 1; }
test "$(hostname)" = servidor4 || { echo 'Servidor incorrecto.' >&2; exit 1; }
test "$#" = 0 || { echo 'Este instalador no admite argumentos.' >&2; exit 1; }
python3 - <<'PY'
import configparser, hashlib, json, os, pathlib, stat, subprocess

commit='897308d80fbfe191da5590fd37983de567a16494'
source=pathlib.Path('/home/administrador/croquis3r-update-897308d80fbf')
dest=pathlib.Path('/usr/local/lib/croquis3r-approved/897308d80fbf')
app=pathlib.Path('/opt/apps/croquis3r')
unit='croquis3r-update-897308d80fbf.service'
expected={'croquis3r.bundle':'88b646f5e166905a36d640b2e61235c9a63283555ad4249c26307d93f99835ad',
          'update-server-lan.sh':'86ef92c0c2af7a9e3f61101b65a3f0a56eda0b5f2106265ec5ad4cbaaba24c1d'}
payload={name:(source/name).read_bytes() for name in expected}
for name,data in payload.items():
    assert hashlib.sha256(data).hexdigest()==expected[name], 'Paquete distinto del revisado: '+name
manifest=json.loads((source/'update.json').read_text())
assert manifest['commit']==commit and manifest['files']==expected

# El ejecutor no debe leer configuración Git ni Compose modificable por SSH
# mientras trabaja como root. No cambia propietarios del volumen PostgreSQL.
assert app.is_dir() and not app.is_symlink()
for parent in (app.parent,app.parent.parent):
    info=parent.stat()
    assert info.st_uid==0 and not info.st_mode & 0o022, 'Padre de aplicación modificable'
for root,dirs,files in os.walk(app,followlinks=False):
    for path in [pathlib.Path(root),*(pathlib.Path(root)/n for n in dirs+files)]:
        assert not path.is_symlink(), 'Revisar enlace antes de autorizar: '+str(path)
        os.chown(path,0,0,follow_symlinks=False)
        path.chmod(stat.S_IMODE(path.stat().st_mode) & ~0o022)

gitdir=app/'.git'
assert gitdir.is_dir() and not gitdir.is_symlink()
cfg=configparser.RawConfigParser(strict=True)
cfg.read(gitdir/'config')
allowed={
 'core':{'repositoryformatversion':{'0'},'filemode':{'true','false'},'bare':{'false'},
         'logallrefupdates':{'true'},'ignorecase':{'true','false'},'symlinks':{'true','false'}},
 'remote "origin"':{'url':{'https://github.com/Almacen3R/croquis3r.git'},
                     'fetch':{'+refs/heads/*:refs/remotes/origin/*'}},
 'branch "main"':{'remote':{'origin'},'merge':{'refs/heads/main'}},
}
assert not cfg.defaults(), 'Configuración Git inesperada'
for section in cfg.sections():
    assert section in allowed, 'Revisar sección Git: '+section
    for key,value in cfg.items(section):
        assert key in allowed[section] and value in allowed[section][key], 'Revisar opción Git: '+key
for name in ('objects/info/alternates','info/grafts','commondir','refs/replace'):
    assert not (gitdir/name).exists(), 'Referencia Git no admitida: '+name

def private_dir(path):
    path.mkdir(parents=True,exist_ok=True)
    assert not path.is_symlink() and path.stat().st_uid==0
    path.chmod(0o700)

private_dir(dest.parent)
private_dir(dest)

def write_once(path,data,mode):
    if path.exists():
        assert not path.is_symlink() and path.stat().st_uid==0 and path.read_bytes()==data, 'Archivo existente distinto: '+str(path)
    else:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
        with os.fdopen(fd,'wb') as out:out.write(data)
    path.chmod(mode)

# Ejecutor fijo: Git sin hooks, fsmonitor ni configuración global; código root.
script=payload['update-server-lan.sh'].decode()
old='g() { git -c safe.directory="$app" -C "$app" "$@"; }'
new='g() { env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_NO_REPLACE_OBJECTS=1 git -c core.hooksPath=/dev/null -c core.fsmonitor=false -c safe.directory="$app" -C "$app" "$@"; }'
assert script.count(old)==1
script=script.replace(old,new)
assert script.count('chown -R administrador:administrador "$app"')==1
script=script.replace('chown -R administrador:administrador "$app"','chown -R root:root "$app"')
payload['update-server-lan.sh']=script.encode()
for name,data in payload.items():write_once(dest/name,data,0o600)
approved={'commit':commit,'files':{n:hashlib.sha256(d).hexdigest() for n,d in payload.items()}}
write_once(dest/'update.json',(json.dumps(approved,indent=2)+'\n').encode(),0o600)
subprocess.run(['/bin/bash','-n',str(dest/'update-server-lan.sh')],check=True)

unit_body=f'''[Unit]
Description=Actualizacion aprobada de Croquis3R 897308d80fbf
After=docker.service network-online.target
Wants=network-online.target
Requires=docker.service

[Service]
Type=oneshot
User=root
Group=root
UMask=0077
WorkingDirectory={dest}
ExecStart=/bin/bash {dest}/update-server-lan.sh
ExecStartPost=/usr/bin/touch {dest}/completed
TimeoutStartSec=45min
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal
SyslogIdentifier=croquis3r-update
'''
write_once(pathlib.Path('/etc/systemd/system')/unit,unit_body.encode(),0o644)
runner=f'''#!/bin/bash
set -euo pipefail
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
test "$#" = 1 || exit 64
case "$1" in
 start)
   if test -f {dest}/completed; then echo 'La actualizacion aprobada ya termino.'; exit 0; fi
   /usr/bin/systemctl start --no-block {unit}
   echo 'Actualizacion iniciada en segundo plano; consultar status o logs.'
   ;;
 status) /usr/bin/systemctl show {unit} --property=ActiveState,SubState,Result,ExecMainStatus ;;
 logs) /usr/bin/journalctl -u {unit} -n 120 --no-pager ;;
 *) echo 'Solo se admite start, status o logs.' >&2; exit 64 ;;
esac
'''
write_once(pathlib.Path('/usr/local/sbin/croquis3r-update'),runner.encode(),0o755)
sudoers=b'''# Solo la actualizacion previamente aprobada de Croquis3R; sin argumentos libres.
administrador ALL=(root) NOPASSWD: /usr/local/sbin/croquis3r-update start, /usr/local/sbin/croquis3r-update status, /usr/local/sbin/croquis3r-update logs
'''
candidate=dest/'sudoers.candidate'
write_once(candidate,sudoers,0o440)
subprocess.run(['/usr/sbin/visudo','-cf',str(candidate)],check=True)
write_once(pathlib.Path('/etc/sudoers.d/croquis3r-approved-update'),sudoers,0o440)
subprocess.run(['/usr/sbin/visudo','-cf','/etc/sudoers'],check=True)
subprocess.run(['/usr/bin/systemctl','daemon-reload'],check=True)
print('Autorizacion instalada para Croquis3R, exclusivamente paquete 897308d80fbf.')
print('El codigo instalado queda protegido por root; no se alteran datos PostgreSQL ni secretos.')
print('Todavia no se inicio la actualizacion. El operador puede ejecutar start y consultar status/logs.')
PY
