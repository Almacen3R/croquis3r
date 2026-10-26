# Preferencia de paños y puertas ajustables — 26-10-2026

Fuente: nueva indicación del usuario basada en el criterio de un cotizador de 3R. Esta actualización sustituye la restricción anterior que rechazaba puertas de 0,50 y 1 m.

## Uso del croquis

El selector **Largo sugerido de paños de pared** está junto a las herramientas de dibujo. Permite 2, 1,50, 1 y 0,50 m. El valor inicial del croquis sin preferencia guardada es 1,50 m por preferencia de 3R; los croquis con una elección explícita conservan esa elección.

Cambiarlo recalcula la propuesta y sus materiales. Divide únicamente los tramos de pared libres, usando primero la medida elegida y luego medidas menores. Por ejemplo, 4 m con preferencia de 1,50 m se distribuyen como 1,50 + 1,50 + 1 m. No acorta la casa, no modifica el área, no mueve columnas dibujadas y no divide ni cambia automáticamente las puertas o ventanas.

Las puertas se colocan haciendo clic sobre una pared o usando la pared seleccionada. Se propone inicialmente hasta 2 m, ajustándose al espacio libre si es menor. Se permiten módulos de 0,50, 1, 1,50 y 2 m; se conserva además el módulo Amplia de 3 m previamente confirmado para no invalidar proyectos. Las medidas de 1,50 m se identifican por su largo, sin asumir automáticamente que son puertas de baño.

Se quitaron los selectores de puerta tanto de la barra de dibujo como del inspector. Las bolitas cambian el largo, el cuerpo mueve la puerta y los botones de rotación/inversión controlan su apertura. El inspector permite escribir directamente el largo. El módulo no representa necesariamente la medida libre del vano ni un SKU comercial confirmado.

## Cálculo y compatibilidad

El croquis y el calculador manual aceptan las mismas medidas de puerta. Se reactiva `panel_19` de 1 m, se agrega `panel_103` de 0,50 m y se conserva `panel_101` de 1,50 m. El formulario ya no bloquea las atenciones antiguas por contener puertas de 1 m. Los resultados históricos almacenados no se reescriben al abrirlos.

Los módulos de puerta aportan longitud y cero bloques de cerramiento, según el tratamiento de vano del modulador. Se mantiene el cálculo de viga por pared continua en croquis y por paño independiente en el manual. Marcos, rellenos y refuerzos siguen fuera de esa receta. El módulo de 0,50 m se incorpora por la indicación de este chat; no se presenta como una fila original del Excel. Versión de reglas: `ticoblock-manual-2026-10-26-v5`.

La homologación de precios no se inventa para las nuevas medidas: si falta el SKU correspondiente aparece pendiente. Siguen pendientes peso, mortero y acero de la familia de 10 cm.

## Verificación local

127 pruebas Django y 34 JavaScript aprobadas. Se verifican las cinco medidas admitidas, rechazo de largos ajenos a la lista, creación y ajuste por extremos, guardado y reapertura, recetas coherentes entre manual y croquis, conservación de resultados históricos y preferencia explícita de 2 m.

En navegador se cambió la preferencia de 2 a 1,50 m y se comprobó el desglose: los tramos libres son de 1,50 m o menos y la puerta de 2 m permanece completa. Se cambió la puerta a 0,50 m, se rotó, se guardó y se reabrió. El área se conservó en 12 m². Solo se actualizó el croquis identificado como prueba local; no se eliminaron datos.

Esta verificación es local. La actualización de producción requiere su propio paquete aprobado, porque el ejecutor del servidor fija el commit y los hashes de cada versión.
