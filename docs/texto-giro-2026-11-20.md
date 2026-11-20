# Texto en renglones y giro del croquis — 20 de noviembre de 2026

## Uso

- Enter y Shift+Enter agregan otro renglón en el texto de una anotación o flecha. Para aplicar: botón Aplicar anotación o Ctrl+Enter (Command+Enter en Mac). Se conserva el foco automático al crear texto.
- Las líneas SVG usan posiciones verticales explícitas: conservan los renglones vacíos, incluidos saltos CRLF, tanto en el dibujo como en sus descargas PNG/PDF.
- El botón **Girar 90°**, junto a los controles de zoom y Centrar, gira todo el proyecto a la izquierda. El responsable confirmó 90°, en lugar de 45°, para trasladar la parte de arriba al lateral izquierdo.
- Giran paredes, columnas, ubicaciones de puertas/ventanas y anotaciones. El texto queda legible horizontalmente; el eje de cumbrera del techo también cambia. Los largos, alturas, artículos, cantidades y observaciones se conservan.
- El giro usa el origen de coordenadas, conserva la cuadrícula y centra la vista después. Se valida antes de aplicar y se rechaza si cambia el dibujo durante la solicitud. No gira con una configuración pendiente. Deshacer/Rehacer incluye el giro; Guardar lo conserva en el proyecto, plantillas y archivos portátiles.

Sin migraciones ni dependencias nuevas. No se modifica automáticamente ningún croquis de producción.

## Verificación

155 pruebas Django y 69 pruebas JavaScript aprobadas (224). Casos nuevos: atajos, composición de teclado, líneas vacías, cuatro giros exactos, apertura de puerta, columnas, anotaciones, área, largos y techo. En una copia privada del ejemplo se comparó el cálculo real de Django para las cuatro orientaciones: las mismas 8 partidas, 39 paños y metros. La copia se usó únicamente en memoria/archivos privados locales, sin guardar cambios en el proyecto remoto.

Estado: implementado y comprobado mediante pruebas; pendiente de aplicar a producción y de prueba visual del usuario.
