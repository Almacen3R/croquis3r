# Observaciones del vendedor · 04/11/2026

Comprobado en local; pendiente de despliegue.

- Campo **Observaciones** debajo del área del croquis: hasta 1000 caracteres y 20 renglones. Guarda texto libre, acentos y saltos de línea.
- Forma parte del documento JSON del croquis, junto a paredes y columnas. Se conserva al guardar, crear una copia, guardar plantilla y exportar/importar el proyecto editable. Los proyectos anteriores funcionan sin observaciones. No requiere migraciones.
- PNG y PDF del dibujo incluyen el encabezado Observaciones y las notas debajo de las cotas. Se amplía la lámina y se ajustan los renglones al ancho con medición real de fuente; también se cortan palabras largas para evitar desbordes. Si está vacío, no agrega bloque ni espacio.
- La impresión directa de la página muestra las notas. Las listas PDF de materiales mantienen su contenido; esta función corresponde al dibujo.
- El texto se inserta como texto, sin interpretar HTML. El servidor valida tipo, longitud, número de renglones y caracteres de control. No altera las cantidades calculadas.

## Validación

141 pruebas Django y 43 JavaScript aprobadas. Nuevos casos cubren guardar/editar, plantillas, importación portable, compatibilidad con documentos anteriores, cantidades invariantes y rechazo de notas inválidas. El ajuste de renglones comprueba párrafos, acentos, palabras largas y anchuras medidas.

En navegador se creó una copia local llamada **Prueba local · observaciones de impresión**, se volvió a abrir y se comprobó la persistencia de las notas. La copia se conserva. Se descargó el PDF real, se renderizó con Poppler y se revisó: texto completo debajo del dibujo, sin superposiciones ni cortes. PNG y PDF usan la misma imagen generada. No se hizo impresión física.

La prueba transaccional del despliegue incluye observaciones al guardar e importar y compara el documento recuperado completo.
