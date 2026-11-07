# Presentación 3D: techo, acabados y recorrido interior

Estado: implementado en local el 7 de noviembre de 2026. Continúa el [visor inicial](visor-3d-2026-11-07.md). No se ha desplegado en producción ni se ha instalado Blender.

## Capacitación breve

1. Abrir el croquis y pulsar **Vista 3D**.
2. Expandir **Acabados y techo**. Elegir pintura (marfil, blanco, arena o verde suave), piso (cerámica, madera o concreto) y techo (sin techo, plano o dos aguas).
3. Para dos aguas, elegir la dirección de la cumbrera —la línea más alta del techo— respecto al croquis y cuánto sube sobre la parte alta de las paredes. La elevación permitida es de 0,30 a 3 m; es una propuesta visual, no una pendiente aprobada.
4. **Ocultar techo** permite revisar el interior; **Desde arriba** lo oculta automáticamente. Volver a mostrarlo desmarcando la casilla.
5. **Entrar a la casa** coloca la cámara en un recinto libre a 1,60 m del piso. Arrastrar para mirar. Usar W/A/S/D, flechas o mantener pulsados los botones de avanzar, retroceder y girar. **Reubicar dentro** vuelve a un punto interior libre; **Centrar casa** regresa al control exterior.
6. **Abrir puertas** permite pasar por sus huecos. Paredes, marcos, ventanas y columnas bloquean el recorrido. La transparencia de paredes es solo visual y no desactiva esas colisiones.
7. Volver al croquis y pulsar **Guardar croquis** para conservar los acabados. Cambiar opciones en 3D marca el documento con cambios pendientes; no guarda silenciosamente. También pueden deshacerse desde el editor.

Las preferencias se conservan en copias, plantillas y archivos portátiles exportados/importados. La posición de la cámara, transparencia, puertas abiertas y ocultación del techo son controles temporales y no se guardan.

## Alcance visual

El techo se deriva de los recintos cerrados del dibujo. No se utiliza un rectángulo envolvente que cubra espacios vacíos en plantas en L o U. En dos aguas, los polígonos del piso se triangulan y se cortan por la cumbrera antes de generar cada plano inclinado. Los cierres de los extremos se añaden en el perímetro, no sobre divisiones interiores compartidas. El plano de arranque toma la altura máxima de pared.

Es una cubierta conceptual sin aleros, canoas, estructura, láminas individuales ni uniones calculadas. Paredes de alturas distintas pueden requerir resolver sus encuentros posteriormente. Se mantiene la convención existente del área en planta respecto a recintos aislados interiores; no se detectan patios automáticamente. La escena sigue siendo de una sola planta.

Las texturas de cerámica y madera se dibujan localmente en el navegador y tienen escala repetida en metros. No se descargan imágenes externas ni se envían proyectos a IA. Son acabados de muestra, no artículos homologados ni partidas de la cotización.

La navegación interior utiliza una aproximación de persona con radio de 18 cm y espacio vertical hasta 1,75 m. El movimiento se subdivide para evitar atravesar paredes entre cuadros y desliza junto a obstáculos. No es un estudio de accesibilidad, evacuación ni normativa. No incluye escaleras, gravedad o navegación entre niveles.

## Datos y compatibilidad

Se añade `presentation3d` opcional dentro del documento JSON v1:

```json
{
  "wall_color": "ivory",
  "floor_finish": "tile",
  "roof_type": "none",
  "roof_color": "charcoal",
  "roof_rise": 0.8,
  "ridge_axis": "x"
}
```

Los documentos antiguos no se reescriben ni reciben opciones hasta que el vendedor cambia la presentación. Django valida listas cerradas de valores y el rango numérico, rechaza opciones desconocidas y conserva estos datos al guardar e importar. No hay migraciones. El cálculo de materiales usa las mismas paredes y reglas: no toma cantidades del techo ni de los acabados ilustrativos.

`presentation3d.mjs` contiene parámetros, geometría de cubierta, selección de punto interior y colisiones, comprobables sin navegador. `viewer3d.mjs` gestiona materiales, controles y cámara. Al cerrar se eliminan eventos de teclado/puntero, texturas, geometrías, materiales y renderizador; al perder el foco se detiene el movimiento.

## Verificación

- 144 pruebas Django y 58 JavaScript. Los casos nuevos cubren validación de opciones, guardado/actualización/plantillas/importación, cantidades invariables, cubiertas de plantas en L/U, dirección y elevación de cumbrera, divisiones interiores y colisiones con paredes, ventanas, puertas y columnas.
- Se creó una copia local de ejemplo llamada **Prueba local · techo y acabados 3D**, sin modificar los proyectos previos. Se probó pintura verde, piso de madera, techo terracota a dos aguas, entrada y avance interior, guardado y reapertura.

## Siguiente etapa

Preparar la escena para renderizar con Blender en un trabajador separado, con tareas en segundo plano, límites de recursos y resultados asociados a la revisión del croquis. Después: imágenes publicitarias, cámaras de recorrido y prueba de propuestas de IA con referencias. La escena actual ya permite revisar la distribución y los acabados antes de contratar servicios externos.
