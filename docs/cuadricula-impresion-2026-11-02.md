# Cuadrícula opcional e impresión limpia · 02/11/2026

Comprobado en local; pendiente de despliegue.

- Casilla **Cuadrícula** junto a Medidas: muestra/oculta únicamente el fondo. Conserva su elección en ese navegador. No modifica el ajuste a 0,50 m, las medidas, los materiales ni la revisión del proyecto.
- Todas las descargas del croquis en PNG y PDF eliminan la cuadrícula, aunque esté visible en pantalla.
- Se eliminaron los dos textos inferiores del archivo: área/marca y aclaración conceptual. El área sigue disponible en pantalla. Se conserva el nombre superior y las cotas; la lista de materiales PDF conserva su contenido.
- Se agregó estilo de impresión de la página: oculta paneles, herramientas, cuadrícula y textos externos al lienzo. Para una lámina del dibujo completo se mantiene la descarga PDF, independiente del zoom en pantalla.
- No hay migraciones ni cambios de dependencias.

## Controles de altura visibles

Se agregaron **Más alto** y **Menos alto** en la barra superior. Ajustan la altura en pasos de 80 px y se deshabilitan al alcanzar el máximo/mínimo; comparten la preferencia guardada con la franja inferior. Comprobados en navegador (465 → 545 → 465 px), sin cambiar revisión ni medidas.

## Uso de la altura existente

La franja **Arrastra para ajustar la altura** está debajo del lienzo; desplazar la página hacia abajo si no está visible. Arrastrar verticalmente; doble clic restaura la altura automática. El ejecutor de la versión `9a9e259fb0a1` confirmó en el servidor Result=success y ExecMainStatus=0 el 02/11/2026; esa funcionalidad ya está aplicada.

## Validación

42 pruebas JavaScript y 5 de PDF Django aprobadas; collectstatic y sintaxis correctos. Se comprobó en navegador ocultar la cuadrícula y recargar (ajuste a 0,50 m conservado). Se descargó un PDF real con la cuadrícula activada en pantalla, se renderizó con Poppler y se revisó: fondo blanco, sin pie inferior, título y cotas completos. Croquis de prueba conservado en revisión 3. No se realizó impresión física.
