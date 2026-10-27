# Descargas, importación y Proyectos — 26-10-2026

Actualización del 27-10-2026: el botón de la lámina pasa a **Descargar**, con elección [PDF o PNG](descarga-pdf-png-2026-10-27.md). El archivo de proyecto editable y su importación mantienen el mismo formato.

## Diseño implementado

Se separan dos archivos con propósitos distintos:

- **Imagen PNG:** para compartir o imprimir el dibujo. Se genera en el navegador desde el SVG nativo, sin dependencias nuevas ni enviar el dibujo a terceros. Usa el contorno completo de paredes, aberturas, columnas y cotas visibles, independientemente del zoom. Omite selección y arrastre temporal, agrega nombre, área y nota de croquis conceptual. Fondo blanco y cuadrícula; lado mayor de hasta 2400 píxeles. No contiene controles ni datos editables del proyecto.
- **Proyecto `.croquis3r.json`:** permite respaldar el dibujo actual, incluso antes de guardarlo en el servidor, y subirlo para continuar. Incluye geometría en metros, orientación de puertas, columnas, configuración aplicada y referencias SKU de los artículos asignados. No incorpora propietarios, IDs de registros, credenciales, precios ni resultados históricos. No conserva el historial de deshacer ni el zoom.

El SVG es la representación visual. El documento geométrico que ya utiliza el editor es la fuente adecuada para continuar editando: una imagen, aunque sea SVG, no sustituye ese documento. Por eso se utiliza un formato JSON versionado y validado en vez de intentar reconstruir objetos desde una imagen.

## Flujo del vendedor

1. En el editor, **Descargar imagen PNG** genera la lámina del dibujo; **Descargar proyecto** guarda el archivo editable. Si hay configuración pendiente, se pide aplicarla antes de descargar el proyecto.
2. En **Proyectos → Subir proyecto**, elegir el `.croquis3r.json` y pulsar **Subir y abrir copia**.
3. El servidor valida el archivo y crea un croquis independiente del usuario que lo sube. No reemplaza el original ni restaura una autoría indicada en el archivo.
4. El editor abre esa copia para seguir trabajando y guardando revisiones. Materiales y precios se recalculan con las reglas y consultas vigentes; esta función no restaura una cotización histórica.

La importación admite un archivo JSON de hasta 1 MB, formato `croquis3r-project` versión 1 y unidades en metros. Aplica las mismas reglas de geometría, puertas y artículos que el guardado normal. Rechaza archivos corruptos, versiones incompatibles y referencias desconocidas sin dejar registros parciales. Las asignaciones se trasladan por SKU, porque los IDs del catálogo pueden variar entre instalaciones. El exportador impide descargar un archivo que supere el límite de importación.

## Una sola lista de proyectos

Se mantiene la URL `/atenciones/` para conservar enlaces, pero su nombre visible ahora es **Proyectos**. La lista se muestra primero; las opciones para empezar un trabajo nuevo quedan después.

Croquis, plantillas personales de croquis, cálculos por paños y listas ajustadas de plantillas comparten búsqueda, orden por fecha de actualización y paginación de 25 registros. La columna Tipo indica cómo se abre cada uno. No se fusionan ni modifican los modelos o datos existentes. Se conservan los permisos: cada usuario ve los suyos; los administradores ven todos, incluidos los antiguos sin propietario.

El acceso **Subir proyecto** está en la cabecera y en el editor. Los errores de importación aparecen al inicio de la página para que no queden escondidos debajo de la lista.

## Comprobaciones

132 pruebas Django y 38 JavaScript aprobadas en local; sin migraciones pendientes. Cubren privacidad, búsqueda y paginación combinadas, importación con CSRF, propiedad del usuario actual, rechazo sin escrituras parciales, traslado por SKU y conservación de geometría/configuración.

En el navegador se descargaron un PNG y un proyecto reales. Se inspeccionó visualmente la imagen completa. Se subió el archivo descargado, se abrió como otro croquis, se modificó la apertura de una puerta y se guardó como revisión 2. Se comprobó que el original y la copia seguían accesibles en Proyectos. La copia está identificada como prueba local; no se eliminaron registros.

El actualizador de producción incluye una prueba transaccional de importación y guardado con CSRF, revertida para no dejar proyectos de prueba. La publicación en producción requiere aprobar el paquete correspondiente; la prueba local no confirma por sí sola un despliegue.

## Despliegue confirmado

El usuario ejecutó el instalador y lanzó el paquete `ced0fe4e7935`. Terminó el 26-10-2026 a las 12:35:10 de Costa Rica, con `Result=success`, `ExecMainStatus=0` y ambos contenedores saludables. El estado `active (exited)` conserva el resultado de la tarea terminada.

Se aprobaron las 132 pruebas Django sobre una base PostgreSQL de prueba y la comprobación transaccional de guardado/importación con CSRF sobre la aplicación desplegada. Se verificaron los 11 artículos homologados mediante SELECT. No hubo migraciones pendientes. Las huellas antes y después confirmaron que se conservaron 10 croquis, 3 atenciones, 1 plantilla de objeto y 4 artículos internos.

Desde la PC, la salud por LAN respondió correctamente y el módulo servido `project-files.mjs` coincidió byte a byte con la versión publicada. El PNG y la edición posterior a importar se comprobaron en navegador local; esta comprobación de producción confirma además la API y la distribución del mismo módulo.

Respaldo previo: `/data/projects/croquis3r/backup-staging/update-20261026T183445Z`. Esta versión incluye también las mejoras anteriores de preferencia visible de paños y puertas ajustables.
