# Identidad empresarial Almacén 3R · 02/11/2026

Implementada en local siguiendo `estilos.md` y el archivo `Logo 3R.jpg` proporcionados. Pendiente de aplicar al servidor.

## Cambios

- Hoja compartida `src/static/croquis/brand.css`: amarillo #FFE100, crema #FFFEF9 / #F4F1E9, texto #161616, bordes #DEDBD2, títulos Georgia y texto Arial/Helvetica. Botones amarillos con texto oscuro, tarjetas blancas, bordes discretos, foco visible y movimiento reducido.
- Encabezado fijo con borde inferior amarillo y logo junto al nombre Croquis3R. El mismo JPG original se usa como favicon; se distribuye dentro de los archivos estáticos, sin depender de Drive ni de una carpeta media externa. La copia conserva exactamente los bytes del archivo proporcionado.
- Componentes de marca y cabecera compartidos por acceso, editor, proyectos, calculador manual, catálogo de plantillas y detalle de plantilla. Los detalles de proyectos heredan la base de ventas.
- Acceso con composición de dos columnas y frases de marca de la guía; formulario con acento amarillo, etiquetas y campos claros.
- El editor adapta el tamaño del título y de los controles compactos a su espacio de trabajo, conservando paneles ajustables, altura, herramientas, cotas y descargas.
- Reglas móviles para encabezado, tarjetas y formulario; herramientas del editor distribuidas en tres columnas en pantallas pequeñas. Preferencia de movimiento reducido respetada.
- Se mantienen los colores semánticos dentro del SVG, el fondo blanco de las exportaciones y las reglas de impresión. No se cambian recetas, cantidades, precios, propietarios ni proyectos. Sin dependencias nuevas ni migraciones.

## Comprobaciones

139 pruebas Django aprobadas; check, collectstatic y ausencia de migraciones verificados. Inspección visual en navegador del editor, proyectos, calculador y acceso. Logo y enlace favicon comprobados; controles de altura y diálogo de descarga operativos; croquis de prueba conservado en revisión 3.

La herramienta de viewport no aplicó el ancho de 390 px al navegador integrado (continuó en 1280 px); por eso no se afirma una verificación visual móvil completa. Las reglas responsive están incluidas y pueden revisarse en un navegador móvil real.
