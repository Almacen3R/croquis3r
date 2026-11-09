# Anotaciones del croquis — 7 de noviembre de 2026

Implementación local, sin cambios nuevos en 3D ni despliegue productivo.

## Uso

1. Pulsar **Anotaciones**, encima del lienzo.
2. **Texto**: tocar el plano para colocar una nota. Escribir en el panel derecho y pulsar **Enter** o **Aplicar anotación**. **Shift + Enter** agrega otro renglón. El mismo atajo sirve para el texto opcional de una flecha.
3. **Flecha**: tocar el inicio y luego el punto que se desea señalar. Puede añadirse un texto opcional junto al inicio. No está restringida a ángulos rectos ni módulos de medio metro.
4. **Mover y editar**: seleccionar una nota o flecha. Arrastrar el cuerpo para trasladarla; las bolitas de una flecha ajustan su inicio o punta. Elegir color negro/azul/rojo y tamaño del texto en el panel. Las posiciones exactas están en una sección opcional.
5. Duplicar o eliminar con los botones existentes; Deshacer/Rehacer también incluye anotaciones. Escape cancela una flecha incompleta.
6. **Guardar croquis** conserva las anotaciones con el proyecto. También se guardan en plantillas y en el archivo portátil. Las descargas PNG/PDF del croquis incluyen textos y flechas, sin controles de selección.

Máximo 100 anotaciones por proyecto, 300 caracteres y 8 renglones por anotación. Una flecha sin texto es válida; una nota de texto no puede quedar vacía. Las coordenadas se guardan en metros con tres decimales, con límites de ±100 m y flechas de al menos 0,10 m.

## Modelo y cálculos

Colección `annotations` opcional dentro del documento JSON v1, separada de las piezas de construcción. Objetos `kind: text` con `x,y`, u objetos `kind: arrow` con `x1,y1,x2,y2`; ambos tienen `id,text,color,font_size`. Django valida y conserva esta colección al guardar/importar. Los identificadores deben ser únicos también frente a paredes, aberturas y columnas. No requiere migraciones de base de datos.

El editor integra las anotaciones en selección, inspector, lista de objetos, arrastre, duplicación e historial. Se pintan mediante SVG nativo dentro del grupo exportable `scene`, con texto seguro mediante `textContent`, flechas vectoriales y letra Arial gruesa con halo blanco. El centrado y la exportación incluyen su extensión para evitar cortes. La punta no depende de marcadores SVG externos.

Las anotaciones no tienen asignaciones de artículos, no dividen paños y no intervienen en área, columnas, materiales, precios o modelo 3D. Se mantienen los permisos del croquis propietario y no se crea un almacenamiento público separado.

## Comprobaciones

Pruebas nuevas de validación/límites/IDs, guardado de plantilla e importación, cantidades invariables, archivo portátil, independencia del modelo 3D y movimiento de anotaciones/extremos. Verificación en navegador con el proyecto local **Prueba local · anotaciones de vendedor**: texto de varios renglones, color, flecha con rótulo, modificación, guardado y reapertura. Se prueban también las descargas del plano.

Resultado: **155 pruebas Django y 60 JavaScript aprobadas**. El navegador confirmó descargas PNG y PDF completadas, arrastre de texto y punta de flecha, y duplicar/eliminar/deshacer/rehacer (conteos de anotaciones 3 → 2 → 3 → 2). Se guardó el ejemplo local en revisión 4. Sin errores ni advertencias de consola. No se cambiaron los proyectos de producción.

El campo de texto aplica con Enter mediante el formulario; Shift + Enter inserta un renglón. Al colocar una anotación se evita que la acción predeterminada del lienzo recupere el foco y se enfoca/selecciona el texto después de soltar el puntero. Se verificó con entrada de teclado sin seleccionar el campo derecho: clic en Texto, clic en lienzo, escritura directa y Enter; el SVG mostró el texto aplicado. Para cargar estas correcciones en una pestaña antigua, guardar el dibujo y recargar la página.
