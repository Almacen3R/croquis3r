# Zoom, cuadrícula y columnas independientes — 26-10-2026

## Caso reportado y reproducido

Los botones Acercar/Alejar ya cambiaban el zoom al probarlos en el navegador, pero no existía zoom con la rueda. Se agregan gestos de rueda y trackpad sobre el plano, manteniendo el punto bajo el cursor, además de botones con texto visible y límites de ampliación. El zoom solo cambia la vista, no las medidas del proyecto.

Se incorpora **Mover vista** y arrastre del fondo con Seleccionar. El botón central del ratón también desplaza la vista. Centrar incluye tanto paredes como columnas independientes. Esc vuelve a Seleccionar. No se agrega una implementación de pellizco táctil con dos dedos en esta entrega.

La cuadrícula mantiene cuadros de 0,50 m y usa un trazo más contrastado, `#7d9084`, de un píxel constante en pantalla. Se retiran A—01, Vista en planta, la leyenda del cuadro y la referencia N de las esquinas. Las instrucciones se muestran fuera del plano con texto más legible; las cotas del dibujo se conservan.

## Columnas fuera de paredes

Se reprodujo una columna C en `(2, 2)` con una pared en `y=0`: el resultado anterior era `incomplete`, lista vacía y mensaje «La columna está fuera de las paredes». Era una validación que bloqueaba el cálculo completo, no un fallo de PostgreSQL ni del guardado.

Ahora se admiten columnas independientes, dentro del contorno o fuera de él. Se cuentan una vez en su producto C/E y se incluye su precio cuando está homologado. No agregan paredes, no dividen paños ni modifican las cantidades de bloques de los muros. Se muestra cuántas son independientes y una nota de revisión de ubicación/función.

Las columnas sobre una pared siguen dividiendo sus paños. Se mantienen los rechazos de columnas duplicadas, medidas inválidas, posiciones no modulares sobre una pared y columnas que atraviesan un vano. Las columnas independientes no reemplazan las columnas pendientes en límites de paños. Se conservan los controles de segundo piso y los datos pendientes de peso, mortero y acero de 10 cm.

Se puede iniciar un dibujo solo con columnas; sin paredes no se inventan metros ni bloques. El cálculo usa la familia configurada. La imagen PNG también admite ese dibujo y Centrar incluye sus posiciones.

## Verificación local

134 pruebas Django y 40 JavaScript aprobadas; sin migraciones pendientes. Los casos nuevos verifican conteo independiente C/E, conservación de materiales y segmentos de pared, dibujo de solo columnas, restricciones de familia/segundo piso y zoom proporcional con anclaje y límites.

En navegador: rueda de 211 % a 384 % y de vuelta; desplazamiento de la vista sin alterar la revisión guardada; colocación de una columna C en el centro del croquis, lista de materiales disponible con una unidad y precio, y guardado como revisión 3 del registro de prueba local. Se inspeccionó la cuadrícula y la ausencia de leyendas en las esquinas.

El actualizador incluye un cálculo de columna independiente mediante la API, junto con guardado e importación en una transacción que se revierte. La actualización de producción requiere aprobar su paquete específico; estas pruebas locales no confirman por sí solas un despliegue.

## Despliegue confirmado

El usuario ejecutó el instalador y el inicio del paquete `907a291106cc`. Terminó el 26-10-2026 a las 16:40:23 de Costa Rica con `Result=success` y `ExecMainStatus=0`. La aplicación y PostgreSQL 18.6 quedaron saludables; no hubo migraciones pendientes.

Pasaron las 134 pruebas Django con PostgreSQL y la comprobación transaccional de la API, incluido el conteo de una columna independiente, guardado e importación con CSRF. Se verificaron los 11 artículos homologados mediante SELECT. La huella antes y después confirmó la conservación de 11 croquis, 3 atenciones, 1 plantilla de objeto y 4 artículos internos. La salud por LAN también respondió correctamente desde la PC tras el despliegue.

Respaldo previo: `/data/projects/croquis3r/backup-staging/update-20261026T223958Z`.

El comando que ejecuta el usuario instala la autorización específica e inicia la actualización completa en segundo plano. Si termina correctamente, la versión ya queda aplicada; la revisión posterior del agente verifica el resultado y lo documenta, sin una segunda activación. El mensaje de inicio no significa que haya terminado. `active (exited)` con resultado satisfactorio indica que la unidad conserva el resultado de la tarea completada.
