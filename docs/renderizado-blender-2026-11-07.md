# Renderizado privado con Blender — 7 de noviembre de 2026

**Actualización:** desplegado en producción LAN con `520b15c9c952`, aplicación y trabajador saludables, prueba real Blender Linux y 152 pruebas Django sobre PostgreSQL aprobadas. Véase el [registro del despliegue y correcciones](despliegue-3d-2026-11-07.md). Las menciones a validación pendiente más abajo describen la preparación local anterior al despliegue.

## Uso para vendedores

Abrir un croquis → **Vista 3D** → **Imágenes de presentación** → **Generar imagen**. Se captura el dibujo actual con su pintura, piso y techo. No necesita estar guardado, aunque se recomienda guardarlo para vincular el resultado a una revisión identificable.

Estados: **En cola**, **Generando imagen**, **Lista para descargar** o **No completada**, con explicación visible en caso de fallo. Es posible cerrar el visor o continuar trabajando mientras el proceso sigue. Al regresar al mismo proyecto se consultan sus imágenes recientes. En dibujos aún sin guardar se muestran los últimos trabajos accesibles de la cuenta.

El resultado inicial es un PNG exterior de 1280 × 960 píxeles. Tiene iluminación, sombras suaves, vidrio y materiales, y utiliza la geometría del visor. No reproduce la posición de cámara actual: aplica una cámara exterior preparada. Ocultar el techo, transparentar paredes o abrir puertas en el visor son controles temporales; la imagen muestra el techo elegido y las puertas cerradas. La interfaz lo indica antes de generar.

Perfil inicial para CPU: Cycles, máximo 16 muestras, muestreo adaptativo (mínimo 4, umbral 0,1), dos hilos y sin reducción de ruido por OIDN. Prioriza completar una vista de presentación en equipos sin GPU. No se presenta como un render publicitario final; la calidad, ruido y tiempos deben evaluarse con casas representativas.

La imagen conserva una captura independiente: editar posteriormente el croquis no cambia el archivo ya generado. Se muestra la revisión guardada si coincide con lo capturado; si hay cambios pendientes se identifica como vista capturada, con fecha y una huella del documento.

## Arquitectura

- `RenderJob` almacena propietario, referencia opcional de croquis/revisión, documento validado, escena geométrica saneada, huella SHA-256, estado y tiempos.
- `RenderWorker` almacena un latido de disponibilidad. La página no acepta solicitudes si el servicio está deshabilitado o el latido tiene más de 20 segundos.
- `render_worker` es un comando Django independiente. Toma un trabajo mediante actualización condicional de estado (evita que dos procesos lo reclamen), inicia Blender y mantiene su latido durante la tarea.
- Cola en la base existente; no requiere Redis ni otro servicio de mensajería. Una imagen simultánea por trabajador y máximo dos trabajos activos por cuenta.
- Timeout de 600 segundos, finalización del proceso en fallo/timeout y detección posterior de trabajos interrumpidos. No hay reintentos automáticos que generen resultados duplicados.
- El navegador usa las mismas funciones `buildHouseScene` y `buildRoof` que el visor. El servidor limita cantidades de objetos/vértices, tamaños, coordenadas, tipos y opciones antes de almacenar la escena. La escena es una presentación aportada por el navegador, no una geometría constructiva certificada; no alimenta la cotización.
- Blender ejecuta exclusivamente `render_blender.py`, incluido en el proyecto, con `--background --factory-startup --disable-autoexec`. No acepta scripts, archivos `.blend`, rutas de salida ni recursos externos del usuario.
- El resultado se verifica como PNG de la resolución esperada antes de marcarlo listo.

Los archivos quedan en `RENDER_ROOT/<uuid-asignado-por-servidor>/`: escena JSON, log privado y PNG. El volumen no se publica como carpeta estática. Listado, vista previa y descarga requieren sesión activa y aplican la misma política de propiedad: usuario normal solo sus trabajos; superusuario puede ver todos. Los archivos se sirven con `no-store`; no se devuelven rutas internas ni logs en la API.

No se han creado tareas de eliminación, respaldo ni retención. Las imágenes consumen almacenamiento y esa política queda pendiente de acordar. No se usan servicios de IA ni se transmiten croquis o fotos a proveedores.

## Local: prueba real sin Docker

Se usa Blender **4.5.15 LTS**, portable para Windows en `.tools/blender-4.5.15-windows-x64`. `scripts/install-blender.py` verifica SHA-256 antes de extraer; no modifica la instalación global ni las asociaciones de archivos.

Configurar en el entorno local o `.env`:

```text
RENDER_ENABLED=1
BLENDER_BINARY=C:/ruta/al/proyecto/.tools/blender-4.5.15-windows-x64/blender.exe
```

Aplicar migraciones y ejecutar en procesos separados:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8013 --noreload
.\.venv\Scripts\python.exe manage.py render_worker
```

El trabajador debe permanecer ejecutándose para admitir solicitudes. La interfaz indica su indisponibilidad si se detiene. No se inicia Blender dentro de una petición HTTP.

`scripts/configure-local-render.py` habilita la instalación portable en el `.env` local preservando las demás opciones y sin imprimir sus valores. Se ejecutó para esta prueba. La aplicación y el trabajador se dejaron en procesos separados; después de reiniciar el equipo hay que volver a iniciarlos.

## Contenedor preparado para el servidor

`compose.render.yaml` es un complemento opcional de la configuración existente. `Dockerfile.render` reutiliza la imagen de la aplicación mediante un contexto de construcción `service:app` e instala el paquete oficial Linux x64 de Blender 4.5.15 con SHA-256 fijado. Requiere Compose con soporte de `additional_contexts` y BuildKit.

El trabajador tiene 2 CPU, 2 GiB de memoria, máximo 128 procesos, raíz de solo lectura, `/tmp` temporal, sin capacidades adicionales, sin nuevos privilegios, sin puertos publicados y solo la red interna de base. Comparte únicamente el volumen de imágenes con la aplicación. No recibe credenciales ni acceso de red a la base comercial.

Ejemplo de futura habilitación LAN, después de construir y revisar en el servidor:

```bash
# RENDER_ENABLED=1 en el archivo de entorno del despliegue.
docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml -f compose.render.yaml --profile renders build app render-worker
docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml -f compose.render.yaml --profile renders run --rm app python manage.py migrate --noinput
docker compose --env-file .env.production -f compose.yaml -f compose.server-lan.yaml -f compose.render.yaml --profile renders up -d
```

No reemplaza los procedimientos de actualización o respaldo existentes. En esta estación no hay motor Docker disponible: se validó la composición y se probó Blender nativo, pero la construcción y ejecución de la imagen Linux siguen pendientes. No se desplegó este módulo en producción.

## Fuentes y versión

Paquetes oficiales: [directorio Blender 4.5 LTS](https://download.blender.org/release/Blender4.5/), [sumas SHA-256 de 4.5.15](https://download.blender.org/release/Blender4.5/blender-4.5.15.sha256). Se verificó además `blender --version`: 4.5.15 LTS, compilación del 22 de octubre de 2026. Se conserva la distribución y licencia del paquete oficial en la instalación.

## Pendiente de etapas posteriores

Seleccionar vistas interiores de render, añadir aleros y detalles visuales revisables, probar materiales y mobiliario, medir tiempos con casas grandes y recursos reales del servidor. Después se puede añadir un video con cámaras de recorrido y, de forma separada, una prueba de acabados con IA. Este módulo inicial genera imágenes; aún no genera video.

## Comprobaciones

152 pruebas Django y 58 pruebas JavaScript aprobadas. Ocho pruebas nuevas cubren captura y cuota por cuenta, servicio ausente, privacidad, descarga con sesión, validación de escena, reclamación única del trabajo, PNG verificado y finalización del proceso por timeout.

La primera prueba real con 32 muestras y reducción de ruido llegó al límite de diez minutos; se conservó como tarea fallida con mensaje visible. Se ajustó el perfil a la configuración de CPU descrita arriba y se solicitó otra imagen desde la interfaz. El fallo no modificó el croquis ni su revisión.

La segunda prueba terminó y produjo un PNG válido de 1280 × 960. Blender registró **2 minutos y 36 segundos** de render y guardado en esta estación; no es una promesa de tiempo para otros proyectos o para el servidor. Se revisó visualmente: conserva el volumen, la puerta, el techo y los colores de la casa de ejemplo. El perfil ligero deja ruido visible y aún requiere mejorar acabados/detalles para publicidad final. La interfaz mostró «Lista para descargar», la miniatura y el enlace; se probó la descarga con sesión y sin errores en consola. Se comprobó también que cerrar y abrir el visor no detiene la tarea.
