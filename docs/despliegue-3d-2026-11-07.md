# Despliegue de 3D y Blender — 7 de noviembre de 2026

Solicitado por el responsable para compartir los avances con sus compañeros. Incluye visor, techo/acabados, recorrido interior, cola privada e imágenes Blender; no importa datos locales ni cambia cuentas o contraseñas.

## Preflight observado

- Servidor `servidor4`, 16 procesadores lógicos, 91 GiB de memoria total y unos 80 GiB disponibles; `/data` con aproximadamente 1,8 TiB libres.
- Docker Compose 5.6.0; PostgreSQL Croquis3R 18.6 y aplicación `git-0de706a3d92d` saludables.
- La cuenta SSH puede consultar contenedores y ejecutar paquetes anteriores previamente autorizados. El nuevo paquete necesita autenticación administrativa propia; no se reutilizan autorizaciones de otro commit ni de otra aplicación.

## Procedimiento preparado

1. Respaldo previo de código, entorno y PostgreSQL, comprobación de lectura del volcado y huella de artículos, croquis, plantillas y atenciones.
2. Verificación del bundle Git y construcción de imágenes etiquetadas por commit para aplicación y trabajador. No cambia tráfico durante la construcción.
3. Render real en el contenedor Linux, sin red, sin credenciales ni base productiva, con el mismo límite de 2 CPU/2 GiB. Valida un PNG de 1280 × 960 antes de continuar. Conserva log y muestra en el respaldo del despliegue.
4. Inventario de dependencias, pruebas Django en una base de prueba y plan de migraciones restringido a las aditivas de propietarios y cola de render.
5. Aplicación de migraciones, recreación de la aplicación y arranque del trabajador. Se activa `RENDER_ENABLED=1` y un volumen privado compartido para imágenes; el trabajador no publica puertos ni recibe la configuración SQL comercial.
6. Comprobación de salud, disponibilidad del trabajador, flujos autenticados existentes y conservación de la huella de datos.

Se mantienen las reglas de reversión del actualizador: recuperar configuración/imagen/código previos ante fallo, conservar respaldo y no restaurar ni sobrescribir automáticamente la base. Si falla después de iniciar el nuevo trabajador, se detiene ese servicio del proyecto. Las tablas nuevas son aditivas y compatibles con la versión anterior.

El instalador de autorización fija un commit y hashes concretos y permite únicamente iniciar esa actualización o leer su estado y registro. Se ejecuta mediante una unidad de systemd, de modo que la sesión SSH no espera una construcción larga ni depende de que la terminal permanezca abierta.

## Estado

Preparado para empaquetar y transferir. El despliegue no se considera aplicado hasta verificar el resultado de la unidad y los servicios después de la autenticación administrativa.
