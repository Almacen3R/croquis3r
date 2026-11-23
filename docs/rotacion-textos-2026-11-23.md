# Giro de textos — 23 de noviembre de 2026

Al seleccionar una anotación, el panel derecho ofrece Girar texto 90° a la izquierda. Cada pulsación recorre 0, 270, 180, 90 y vuelve a 0 grados SVG. El giro se aplica al texto completo, con todos sus renglones, desde su punto de colocación. En flechas gira solamente el rótulo; inicio, punta y sentido de la flecha se conservan.

El botón aplica también los cambios pendientes de texto, color y tamaño del formulario, conserva el foco para repetir el giro con teclado y permite Deshacer/Rehacer. Se deshabilita mientras se valida para evitar pulsaciones dobles simultáneas.

La propiedad opcional text_rotation admite únicamente enteros 0/90/180/270. Documentos anteriores sin esa propiedad se muestran como antes. Se conserva en croquis, plantillas, duplicados y archivos portátiles. El grupo SVG del texto incluye la zona de selección y arrastre, por lo que ambos giran juntos y el centrado/exportación consideran su extensión real. PNG y PDF conservan esa transformación vectorial antes de rasterizar el croquis.

No cambia paredes, materiales ni 3D. Sin migraciones ni dependencias nuevas. El giro general del croquis mantiene la orientación elegida para cada texto; el nuevo botón permite ajustar cada rótulo por separado.

Pruebas de ángulos admitidos y rechazados, materiales invariantes, guardado/plantilla/importación, transformaciones SVG, texto de varios renglones, zona de selección y conservación al mover/descargar el proyecto. Desplegado y verificado en producción LAN con la versión `1a0571ae709a`.

Verificación: 166 pruebas Django y 88 JavaScript aprobadas (254). La aplicación también evita sobrescribir cambios hechos durante la validación del formulario.

Producción: actualización terminada con estado success y código 0. Se ejecutaron las 166 pruebas Django sobre PostgreSQL y el render de prueba Blender Linux produjo un PNG de 1280 × 960. Se conservaron 4 artículos, 5 atenciones, 1 plantilla de objetos y 21 croquis. Respaldo previo: `/data/projects/croquis3r/backup-staging/update-20261123T140532Z`.

La comprobación HTTP autenticada confirmó los archivos editor.js y annotations.mjs idénticos por SHA-256 al código probado, giro 270 aceptado y 45 rechazado por la API, y salud OK. No se guardaron proyectos de prueba.
