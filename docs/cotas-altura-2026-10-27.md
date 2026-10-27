# Cotas legibles y altura del lienzo · 27/10/2026

Implementado y validado localmente; pendiente de aplicar al servidor.

- Cotas parciales: texto de 0,13 a 0,17 unidades SVG; totales: de 0,16 a 0,20. Arial en negrita (700), color oscuro y halo blanco para separar texto de la cuadrícula.
- Líneas de cotas de 0,012 a 0,022; marcas de extremos de 0,014 a 0,026. Líneas auxiliares más oscuras y gruesas. Medidas de abertura seleccionada también reforzadas.
- Se conserva el estilo en las descargas PDF/PNG. La cuadrícula exportada tiene opacidad 0,35 para priorizar dibujo y medidas en papel; la cuadrícula de pantalla conserva su contraste.
- Debajo del lienzo hay una franja arrastrable para ajustar altura (320–1600 px). El ancho sigue dependiendo de los paneles laterales.
- Se recuerda la altura en el navegador, no en el proyecto. Doble clic restablece la altura automática de la pantalla. También permite Tab, flechas arriba/abajo (40 px), Inicio/Fin. Los atajos Ctrl/Alt/Meta no modifican tamaños.
- No cambia geometría, cantidades, área, revisiones ni archivos de proyecto. Sin migraciones ni nuevas dependencias.

## Comprobaciones

42 pruebas JavaScript y 5 pruebas de exportación PDF Django aprobadas, sintaxis de módulos y collectstatic correctos. En navegador: arrastre de 425 a 465 px, teclado hasta 505 px y persistencia al recargar; límite 1600, doble clic para restablecer y Ctrl+Inicio sin modificar altura. El croquis de prueba se conserva en revisión 3.

Se descargó un PDF real desde el editor, se renderizó con Poppler y se revisó la página completa: cotas parciales y totales legibles, sin cortes, cuadrícula tenue. No se hizo una prueba física de impresora.

## Estado de la versión anterior

El paquete `caaeb9e3056f` (paneles laterales y listas PDF con/sin precios) terminó correctamente en producción el 27/10/2026. Estado del ejecutor: Result=success, ExecMainStatus=0. Pasaron 139 pruebas en PostgreSQL, comprobación de ambos PDF, 11 artículos homologados, guardado e importación con CSRF. Aplicación y PostgreSQL saludables; preservados 12 croquis, 3 atenciones, 1 plantilla de objeto y 4 artículos internos. Respaldo previo: `/data/projects/croquis3r/backup-staging/update-20261027T162056Z`.
