# Lista PDF de materiales simplificada — 20 de noviembre de 2026

Las variantes con precios y sin precios muestran fecha de emisión, altura del cálculo, espesor, largo total y cantidad de paños. La altura proviene del cálculo validado en el servidor; no se acepta un rótulo de altura enviado por el navegador.

Se mantienen cantidades, precios de consulta, IVA y total/subtotal parcial, con su fecha de consulta. Se retiran los párrafos generales repetidos, el aviso técnico extenso del proveedor y los motivos largos insertados en cada descripción. Los importes ausentes continúan marcados Pendiente y excluidos de cualquier subtotal parcial. Las columnas pendientes y los datos aún no confirmados de 10 cm conservan una nota breve explícita.

El nuevo resumen Cómo se calcularon los bloques agrupa por receta: tipo y largo de paño, número de paños, bloques de cada referencia por paño y aporte total. Ejemplo de 13 m a 2,70 m: 6 x (36 TP50 + 12 TP37) = 216 TP50 + 72 TP37; 1 x (12 TP50 + 12 TP37) = 12 TP50 + 12 TP37. No lista una fila por cada pared ni añade referencias técnicas del Excel al PDF comercial. Los detalles completos siguen disponibles en pantalla.

No cambia las cantidades ni consulta precios para la copia sin precios. Sin migraciones. Los textos continúan escapados para ReportLab.

Se generaron y revisaron visualmente dos muestras A4 de una página: con precios ficticios rotulados expresamente como ejemplo y sin precios. Sin desbordes ni cortes. Prueba adicional verifica altura 2,70 m, agrupación 6+1, cantidades 216/72 y 12/12 y que se recalcula desde el documento, ignorando valores inventados por el navegador.

Estado: implementado, pendiente de desplegar. Las muestras están en output/pdf, excluido de Git. La entrega incluye las mejoras anteriores de recálculo, saltos de línea y giro.


## Ampliación: otros materiales

El PDF también muestra el cálculo de vigabloques por pared continua y número de hiladas; varilla de pared por factor de cada grupo de paños; varilla de viga según metros / 6 y número de hiladas; y mortero según bloques / 20. Cada resultado explica si se redondea hacia arriba o con el redondeo del Excel. Se usan los mismos totales del motor, sin convertir los equivalentes de varilla en un despiece comercial confirmado.

Se mantienen pendientes de 10 cm: no se imprimen fórmulas heredadas de 12 cm para mortero o acero. Las tablas admiten división interna en varias páginas para proyectos con muchos tramos. Probados el ejemplo de 13 m a 2,70/2,90 m y un proyecto de 100 tramos distintos; muestras visuales sin cortes.

Verificación final de esta ampliación: 159 pruebas Django aprobadas.
