# Giro sin cambio de zoom y centrado — 21 de noviembre de 2026

El giro llamaba a fit, que recalculaba la escala al intercambiar ancho y alto. Además, fit construía la vista desde la esquina mínima y añadía un tamaño mínimo de 6 x 5 m; cuando el dibujo era estrecho, ese mínimo dejaba el centro desplazado. No consideraba siempre las cotas o las aberturas al encuadrar.

Ahora el giro conserva las dos dimensiones del viewBox y solo lo traslada al centro del contenido renderizado. Recalcular materiales no vuelve a ajustar la escala. El botón Centrar encuadra todo el contenido usando su centro real y la proporción actual del lienzo. Se incluyen escena, cotas y marcadores; se excluye la cuadrícula de fondo.

Cuando llegan las cotas completas de la estimación, se refina el centrado una vez con la misma política de la acción inicial. Usar zoom o tocar el lienzo cancela ese refinamiento pendiente para no desplazar una vista que el vendedor ya está manipulando. Cargar otro proyecto invalida la estimación anterior antes de calcular sus límites.

El giro no modifica su transformación geométrica, materiales, datos guardados ni exportaciones. El botón Centrar sigue siendo un encuadre completo: puede ajustar escala para mostrar todo. Girar conserva la escala elegida; si el contenido ya no cabe en la altura del lienzo, Centrar permite encuadrarlo completo.

Pruebas: centrado exacto de paredes de 13 m en ambas orientaciones, tramos pequeños, coordenadas negativas, monitores anchos/verticales, cotas y anotaciones separadas, cuatro giros consecutivos sin acumular zoom y conservación del factor real de escala SVG. Pendiente de desplegar y comprobar en producción.

Verificación previa: 165 pruebas Django y 86 JavaScript aprobadas (251), sintaxis del editor correcta. Sin migraciones.
