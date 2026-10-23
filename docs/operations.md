# Operación de Croquis3R

## Estado comprobado

Actualización del 21-10-2026: Croquis3R ya funciona en el servidor LAN con PostgreSQL 18 y Docker. Ver [despliegue LAN](server-lan-deployment.md) y [registro vigente de pendientes](pendientes-ticoblock.md). El desarrollo local continúa usando SQLite; las revisiones locales de reglas y de compatibilidad HTTP aún no se desplegaron.

La descripción siguiente conserva las comprobaciones de preparación inicial.

Entorno local Windows con Python 3.13.17 y SQLite; producción preparada con Python 3.12.15 y PostgreSQL 18.6. Ver los comandos del README para preparar y ejecutar. El contenedor utiliza Gunicorn 26.2.2 y WhiteNoise; no usa el servidor de desarrollo de Django. Ver la [revisión de seguridad del 23-10-2026](seguridad-dependencias-2026-10-23.md) para distinguir lo probado de lo pendiente de aplicar en producción.

El 19 de octubre se verificó que esta estación corre en una VM QEMU con `HypervisorPresent=true`, pero sin virtualización anidada expuesta (`VirtualizationFirmwareEnabled`, SLAT y VMMonitor en `false`), y sin WSL instalado. Se pospuso Docker Desktop porque su motor Linux requiere ese soporte desde el anfitrión. Se descargó Docker Compose 5.6.0 oficial a `.tools/` (ignorado por Git), se verificó su SHA-256 y se validaron tanto la configuración local como la combinación de producción con `config --quiet`. Esto comprueba la configuración, no la construcción ni ejecución de imágenes.

## Variables

| Variable | Uso |
|---|---|
| `DJANGO_DEBUG` | `1` exclusivamente para pruebas locales; `0` exige clave propia y acceso del equipo |
| `DJANGO_SECRET_KEY` | Secreto propio; obligatorio y de al menos 32 caracteres en producción |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por comas; incluir `127.0.0.1` para el healthcheck interno |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes HTTPS autorizados separados por comas |
| `DB_ENGINE` | `sqlite` local o `postgres`; Docker fuerza `postgres` |
| `POSTGRES_DB` | Base exclusiva, por defecto `croquis3r` |
| `POSTGRES_USER` | Rol exclusivo, por defecto `croquis3r_app` |
| `POSTGRES_PASSWORD` | Secreto obligatorio para Compose; nunca versionarlo |
| `POSTGRES_HOST` | `db` dentro de Compose |
| `POSTGRES_PORT` | `5432` dentro de la red privada |
| `APP_PORT` | Puerto HTTP de prueba, `8013`, enlazado a loopback |
| `PROXY_NETWORK` | Red externa del futuro proxy, por defecto `proxy` |

## Operación local con Compose

`make` es opcional; en Windows puede usarse el comando Docker directamente.

| Objetivo | Comando |
|---|---|
| Validar configuración | `docker compose config --quiet` |
| Construir | `docker compose build` |
| Migrar | `docker compose run --rm app python manage.py migrate` |
| Cargar ejemplos | `docker compose run --rm app python manage.py seed_demo` |
| Iniciar | `docker compose up -d` |
| Estado | `docker compose ps` |
| Logs | `docker compose logs --tail=100` |
| Detener conservando datos | `docker compose down` |
| Verificar | `sh scripts/verify.sh` |

La carga de ejemplos es explícita e idempotente: no se ejecuta en cada arranque y no sobrescribe artículos que alguien editó. Las migraciones también se ejecutan explícitamente antes de iniciar la aplicación.

## Preparación posterior del servidor

`compose.production.yaml` es una base para revisión, no un despliegue completado. El uso de `!override` y `!reset` requiere Compose 2.24.4 o posterior. Se combinará con `compose.yaml` usando `--env-file .env.production`.

Antes de habilitarlo: confirmar el montaje `/data` según los documentos del servidor, crear la ruta de PostgreSQL con el UID/GID real de la imagen elegida, definir secretos fuera de Git, dominio y TLS, y configurar el proxy para alcanzar `croquis3r:8080`. El contenedor de aplicación ejecuta con UID/GID 10001. No se crean directorios en el servidor desde este prototipo.

Con `DEBUG=0`, los cookies de sesión y CSRF exigen HTTPS. El proxy y TLS deben estar listos antes de usar ese modo. Revisar `python manage.py check --deploy` en el entorno definitivo y configurar encabezados seguros/HSTS según el proxy elegido. Las imágenes base tienen etiqueta de versión mayor; sus digest concretos deben fijarse y probarse antes del despliegue. Las dependencias Python están fijadas en `requirements.lock`.

Salud: `/health/` devuelve 200 si la conexión a base responde, 503 si falla. No sustituye una prueba funcional de migraciones ni un ensayo de recuperación.

No hay credenciales de producción, conexión comercial, transferencia a Drive ni tareas programadas en esta entrega.
