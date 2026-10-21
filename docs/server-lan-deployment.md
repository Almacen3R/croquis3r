# Primer despliegue LAN de Croquis3R

Preparación y primer despliegue del 21 de octubre de 2026. **Servidor LAN instalado y saludable.** PostgreSQL está en uso; ver el [registro vigente](pendientes-ticoblock.md). Las secciones de ejecución y reanudación documentan el procedimiento histórico; no repetir la instalación inicial sobre las rutas existentes.

## Base y datos

La aplicación local usa SQLite (`db.sqlite3`). En el servidor se usará PostgreSQL 18 exclusivo del proyecto. Los documentos JSON, sus revisiones, plantillas y atenciones se conservan mediante una exportación Django desde una instantánea consistente de SQLite. La base original permanece intacta.

La instantánea preparada contiene 4 croquis, 1 plantilla de pared, 3 atenciones y 4 artículos locales. Incluye los ejemplos que ya existían; no conecta con la base comercial. No importa contraseñas ni sesiones locales. La exportación se restauró en una base local aislada y se compararon los documentos y resultados.

## Instalación propuesta

- Código: `/opt/apps/croquis3r`.
- PostgreSQL: `/data/projects/croquis3r/postgres`, montaje PostgreSQL 18 en `/var/lib/postgresql`.
- Red de base privada; sin publicar 5432.
- Aplicación Gunicorn con usuario 10001, `DEBUG=0` y acceso del equipo autenticado.
- HTTP interno: `http://192.168.0.214:8013`, enlazado únicamente a esa IP LAN.
- Compose: `compose.yaml` + `compose.server-lan.yaml`, nombre de proyecto `croquis3r`.
- El modo LAN configura cookies para HTTP explícitamente. Al migrar a HTTPS se debe usar el archivo de producción para proxy y restaurar cookies seguras.
- Esta exposición directa LAN es una excepción temporal al proxy común: permite probar el proyecto sin cambiar la configuración ni los contenedores de otras aplicaciones. No instala DNS ni TLS.
- Secretos generados exclusivamente en el servidor, archivo `.env.production` con permisos 0600.
- Usuario inicial: `croquis_admin`; acceso inicial en `/home/administrador/.config/croquis3r/acceso-inicial.txt`, privado para el administrador. Cambiar la contraseña inicial desde Django Admin.

El script de instalación comprueba hostname, UUID y serie del disco de datos, disponibilidad del puerto y ausencia de rutas del proyecto. Si ya existen `/opt/apps/croquis3r` o `/data/projects/croquis3r`, se detiene sin sobrescribirlas. No detiene ni reinicia aplicaciones ajenas. No usa `down -v`, no modifica sudoers ni configura respaldos externos.

## Preparación local

```powershell
.venv/Scripts/python.exe scripts/prepare-server-release.py
```

Salida privada y excluida de Git/Docker: `.deploy/croquis3r-20261021/`. Incluye código empaquetado, datos iniciales, script y manifiesto SHA-256. Las comprobaciones de Compose y del script no sustituyen probar la construcción real con Docker/PostgreSQL.

## Ejecución administrativa pendiente

La cuenta SSH `administrador` puede consultar el estado de Docker con sudo sin contraseña, pero no construir/iniciar contenedores ni crear las rutas nuevas. No se reutiliza el permiso `rrhh-run`, que pertenece a otra aplicación.

Una vez subido y verificado el paquete en `/home/administrador/croquis3r-deploy-20261021`, ejecutar desde PowerShell:

```powershell
ssh -t -F "$env:USERPROFILE\.ssh\config_inventariotec" inventariotec-produccion "sudo bash /home/administrador/croquis3r-deploy-20261021/deploy-server-lan.sh"
```

Este comando pide la contraseña de sudo directamente en la terminal. No debe pegarse la contraseña en el chat. El script crea el proyecto, construye la imagen, migra PostgreSQL, carga y comprueba los datos, crea la cuenta inicial y arranca los dos servicios. Finalmente comprueba salud HTTP y acceso autenticado al editor, calculador, atenciones y API.

Si falla después de crear directorios, no repetirlo ni eliminar datos para continuar: revisar primero el registro y el estado de `croquis3r`. El script se detiene precisamente para evitar sobrescribir una instalación parcial.

## Verificación posterior

```bash
cd /opt/apps/croquis3r
sudo docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml ps
curl --fail http://192.168.0.214:8013/health/
```

Tras la instalación deben verificarse desde otra computadora de la LAN el inicio de sesión, apertura de los croquis importados, cálculo y guardar/reabrir un croquis nuevo. La ejecución real, el acceso LAN y la migración PostgreSQL se considerarán pendientes hasta observar esos resultados.

Respaldos programados, Drive, remoto Git y conexión al catálogo comercial siguen fuera de esta primera instalación. El archivo de datos iniciales bajo `persistent/` es una copia de importación, no una política de respaldos.


## Reanudación tras fallo de permisos — 21 de octubre de 2026

La primera ejecución verificó los archivos, creó las rutas y la configuración, y descargó PostgreSQL. Se detuvo en `install -o 999`, antes de construir la aplicación o iniciar PostgreSQL. El servidor usa `install (uutils coreutils) 0.8.0`, que rechazó ese UID sin cuenta local. No es un problema de SSH ni requiere crear usuarios de contenedor en Ubuntu.

Los scripts corregidos asignan UID/GID numéricos mediante `os.chown`, evitando resolverlos como nombres de cuentas. Se conservó el paquete original y se agregó `resume-server-lan.sh` al directorio privado de preparación. La reanudación comprueba que todavía no existen contenedores Croquis3R y que PostgreSQL no contiene archivos; conserva los secretos generados y no borra directorios. Si esos supuestos cambian, se detiene.

```powershell
ssh -t -F "$env:USERPROFILE\.ssh\config_inventariotec" inventariotec-produccion "sudo bash /home/administrador/croquis3r-deploy-20261021/resume-server-lan.sh"
```

Se verificaron en el servidor la integridad del script de reanudación, sintaxis Bash y configuración Compose instalada. Construcción, migración y disponibilidad siguen pendientes de esa ejecución administrativa.
