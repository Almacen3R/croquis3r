# Aclaraciones de TicoBlock — 21 de octubre de 2026

Actualización posterior: las restricciones de puertas y la preferencia inicial del croquis cambiaron el [26-10-2026](panos-y-puertas-2026-10-26.md). Esa indicación más reciente prevalece sobre los apartados históricos de este documento.

Fuente: explicaciones del usuario tras su reunión con los compañeros de TicoBlock y respuestas de seguimiento en este chat. Estas aclaraciones complementan y corrigen las incertidumbres del informe del 20 de octubre. No se modificaron los archivos originales de TicoBlock ni los registros guardados.

## Reglas confirmadas

| Tema | Criterio para Croquis3R |
|---|---|
| Tapias | Se calculan como paredes. Comparten el croquis y el cálculo por paños; no hace falta otra herramienta. |
| Distribución por metros | Preferencias de 2, 1,50, 1 o 0,50 m. Por defecto 2 m. Completar el sobrante con medidas inferiores, respetando exactamente el largo. |
| Puerta baño | Medida comercial indicada: 1,375 m; módulo de pared de 1,50 m. |
| Puerta Estándar | Módulo de 2 m; su ancho comercial es menor. No confundir el vano con el módulo. |
| Puerta Amplia | Módulo de 3 m. |
| Familia 12 cm | TP50 y TP37. Recomendada para proyectos nuevos. Alturas 2,50, 2,70 y 2,90 m. |
| Familia 10 cm | TP48 y TP40. Mismas cantidades por paño: cambian el ancho, no el largo y alto de los bloques. Solo altura 2,50 m. |
| Promociones | Mantener y recomendar los bloques de 10 cm de las listas recibidas. Fuera de promoción los de 10 cm son más caros; no se infieren precios ni se recalculan listas por área. |
| Unión en 10 cm | No se usan vigas de bloques; se unen con perling o chorreado. Esos materiales y refuerzos no están cuantificados en las recetas actuales. |
| Segundo piso | Únicamente 12 cm con columnas. Esto es una restricción de materiales, no una aprobación estructural ni un cálculo de entrepiso. |

## Aplicación de las reglas

La relación de conteos es TP50 → TP48 y TP37 → TP40 al cambiar de 12 a 10 cm. Se conserva la cantidad por tipo de paño y se identifica la familia en el desglose. Los campos internos `tp50`/`tp37` se mantienen por compatibilidad, como conteos de bloque largo/corto; el resultado también guarda `block_family` y nombres explícitos de los productos.

Las puertas actualizadas usan módulo 1,50, 2 o 3 m. Continúa la regla de vano sin bloques del modulador: esas recetas suman longitud, sin añadir bloques de cerramiento dentro de la puerta. Marcos, dinteles y refuerzos no se calculan. Las entradas nuevas de 1,50 y 3 m indican su origen de confirmación, sin atribuirlas a filas inexistentes del Excel.

El módulo de puerta de 1 m de la transcripción inicial deja de ser una opción nueva. Los croquis antiguos que lo contengan se señalan para revisión, sin cambiar su geometría. Las atenciones antiguas conservan el resultado y versión guardados; al editarlas se pide revisar y sustituir explícitamente el conteo antiguo. No se cambia automáticamente una puerta de 1 m por una de baño de 1,50 m.

## Asistente por metros

Disponible dentro de Calcular por paños, para tramos continuos de pared completa o tapia. Ejemplo de 7,50 m:

| Preferencia | Propuesta |
|---|---|
| 2 m, predeterminada | 3 × 2 m + 1 × 1,50 m |
| 1,50 m | 5 × 1,50 m |
| 1 m | 7 × 1 m + 1 × 0,50 m |
| 0,50 m | 15 × 0,50 m |

Cada lado se distribuye por separado. Los encuentros, puertas y ventanas requieren ajustar los paños; sumar el perímetro entero como una sola cadena pierde esas restricciones. El asistente ofrece reemplazar los cuatro conteos de pared completa o sumar otro tramo, conservando las otras clases de paño y las columnas. Se calcula y guarda por las acciones existentes.

La sugerencia admite entre 0,50 y 200 m por tramo, en múltiplos exactos de 0,50 m. No redondea el largo del cliente. El formulario manual conserva el límite de 100 paños por clase: si se supera al aplicar una sugerencia, se avisa sin cambiar las cantidades.

## Datos todavía no cuantificados

- Pesos de TP48/TP40 y columnas de la familia de 10 cm.
- Consumo de mortero y varilla de pared específico de 10 cm; no se trasladan automáticamente los factores de 12 cm.
- Perling, chorreado, anclajes y refuerzos para las uniones de 10 cm.
- Dimensionamiento estructural, cimentación y entrepiso para segundo piso.

Para 10 cm estos consumos/pesos se muestran pendientes, no como cero. Los vigabloques se muestran en cero porque no corresponden a esa familia. No se infiere que perling o chorreado carezcan de acero.

## Estado de entrega

Implementado y verificado en local. No se actualizaron contenedores ni datos del servidor durante este cambio. Las rutas y versiones de producción se mantienen hasta un despliegue posterior de esta revisión.
