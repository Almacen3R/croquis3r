# Git y actualización de Croquis3R

Repositorio: <https://github.com/Almacen3R/croquis3r>. Rama principal: `main`.

Se versionan código, migraciones, pruebas, recursos de las plantillas, documentación del proyecto y scripts. No se versionan SQLite, PostgreSQL, secretos, volcados, credenciales, entornos virtuales, paquetes temporales ni las referencias privadas de conexión/inventario del servidor.

## Actualizar el servidor existente

No volver a ejecutar los scripts de primera instalación. El script `scripts/update-server-lan.sh` actualiza exclusivamente el proyecto `croquis3r` en `/opt/apps/croquis3r` y conserva la base de producción. Recibe un directorio privado de preparación con:

- `croquis3r.bundle`: bundle Git completo de `main`, correspondiente al commit ya publicado en GitHub;
- `update-server-lan.sh`: copia exacta del script versionado;
- `update.json`: commit y SHA-256 de los dos archivos.

La transferencia por SSH evita guardar una credencial personal de GitHub en el servidor. El checkout conserva `origin` apuntando al repositorio oficial, aunque el objeto Git se recibe desde el bundle.

El script comprueba el servidor y `/data`, respalda el código/configuración y crea un volcado PostgreSQL previo, verificando su lectura con `pg_restore --list`. Registra conteos y una huella de los artículos, croquis, plantillas y atenciones. Después recibe el commit, construye una imagen etiquetada con su hash, comprueba migraciones y ejecuta las pruebas Django sobre una base de prueba independiente.

Si las comprobaciones pasan, recrea únicamente `app` con `--no-deps`, manteniendo PostgreSQL y las demás aplicaciones. Verifica salud, acceso autenticado, el asistente por metros y que la huella de los registros comerciales siga igual. Conserva usuario y contraseña actuales; no vuelve a importar los datos locales ni crea otro administrador.

Ante un error posterior al cambio de código, conserva el respaldo y trata de recuperar la imagen anterior. No restaura automáticamente ni sobrescribe la base de producción. Si el script informa un fallo, revisar el diagnóstico antes de repetir.

La cuenta SSH requiere autenticación interactiva de `sudo`. La ejecución se realiza mediante el script preparado para ese commit; no se amplían permisos ni se reutilizan autorizaciones de otra aplicación. Los respaldos previos al despliegue son locales, sin sustituir la política externa de copias que sigue pendiente.
