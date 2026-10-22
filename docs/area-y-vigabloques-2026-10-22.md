# Área en planta y vigabloques — 22 de octubre de 2026

## Motivo del cambio

El usuario confirmó con TicoBlock que debe incluirse viga de amarre en cada pared de 12 cm, también a la altura base. Antes se había trasladado literalmente la selección del Excel: 2,50 m = cero hiladas; 2,70 m = una; 2,90 m = dos. Eso explica el cero observado; no era un problema de PostgreSQL ni del guardado.

La [ficha N-12 viga recibida](https://drive.google.com/file/d/1OMWvVb1OZDhDFzcKr5AZ18qmzj3DyjYI/view), página 1, se revisó nuevamente en su render local `.tools/ticoblock_20261020/visuals/bloque_viga_n12_p01.png`: tamaño nominal **12 × 20 × 40 cm**, tamaño real **12 × 19 × 39 cm**. Se calcula con 0,40 m nominales, no 0,39. La ficha respalda la longitud y el uso con acero horizontal y concreto; la inclusión a 2,50 m procede de la aclaración del usuario, no de una receta nueva atribuida al Excel.

## Regla aplicada

- Rendimiento teórico: 1 / 0,40 = 2,5 piezas por metro y por hilada.
- Compra: redondear **hacia arriba por pared recta continua** y sumar los resultados. Ejemplos: 0,50 m → 2; 1 m → 3; 1,50 m → 4; 2 m → 5; 3 m → 8; 4 m → 10.
- En el croquis se agrupan objetos contiguos colineales, incluso invertidos. Esquinas y tramos separados se calculan por separado. No se descuenta el módulo de puertas/ventanas ni se redondea otra vez en límites de paño o columnas. La preferencia de paños no cambia la viga.
- En el calculador manual no se conocen los encuentros: cada paño se considera independiente para redondear. La diferencia se explica junto al resultado. No se supone reutilización de recortes entre paredes o paños independientes.
- 12 cm: una hilada a 2,50 m; se conservan una a 2,70 y dos a 2,90 m. **No se agrega una tercera hilada** ni se altera la tabla de bloques de cerramiento. Es una corrección de la estimación de materiales; la composición de la altura terminada requiere validación de proyecto.
- 10 cm: se mantiene la regla confirmada del 21-10-2026, sin vigabloques. Perling o chorreado se cotizan aparte.
- La varilla de viga usa la fórmula heredada (metros / 6, entero más cercano) por hilada aplicada. Puede dar cero en tramos cortos y se advierte; no se ha confirmado una regla de despiece, traslapes o anclajes. El mortero y el peso parcial conservan sus factores anteriores y **no incluyen vigabloques, acero ni relleno**; no se presentan como totales de obra. Siguen pendientes los consumos/pesos de 10 cm.
- Versión nueva: `ticoblock-manual-2026-10-22-v4`. No hay migraciones ni edición de documentos/resultados guardados. Al recalcular se aplica la regla nueva; el resultado anterior guardado solo cambia si el usuario lo guarda expresamente.

## Área de la casa

Se muestra en m² la suma de superficies cerradas en planta sobre las líneas de referencia dibujadas. No es área neta de paredes ni área útil interior: no descuenta espesores. Las puertas y ventanas no cambian la huella de la casa. Los patios no se infieren ni descuentan automáticamente; el aviso lo indica.

El algoritmo divide los cruces/T, construye las caras cerradas del grafo y suma sin duplicar habitaciones ni recintos aislados ya contenidos. Usa las longitudes dibujadas, no el rectángulo envolvente. Un contorno abierto no genera un área inventada; cuando solo hay una parte cerrada y tramos exteriores abiertos, se rotula «Área cerrada parcial». Se actualiza al mover, redimensionar, borrar, abrir o deshacer.

## Verificación

93 pruebas Django y 27 de geometría aprobadas. Se cubren piezas enteras y redondeo, esquinas/gaps, objetos colineales invertidos, invariancia frente a paños/aberturas/columnas, alturas y excepción de 10 cm. Para área: rectángulo, L, triángulo diagonal, divisiones con T/cruces, paredes invertidas, conjuntos separados, recintos contenidos y contornos abiertos.

En navegador local, el ejemplo de 4 × 3 m muestra **12 m² y 36 vigabloques** (10 + 8 + 10 + 8). Se prueba sin guardar ni modificar los croquis reales. También se comprobó en navegador la excepción de 10 cm (cero vigabloques y consumos pendientes), la pérdida del área al abrir el contorno y la recuperación de 12 m² al deshacer. Evidencia: `screenshots/area-vigabloques-2026-10-22.png`. Estado de despliegue: corrección local pendiente de aplicar en servidor.
