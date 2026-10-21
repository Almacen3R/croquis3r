# Actualización posterior

Las dudas de este informe sobre familias TP37/TP50 frente a TP40/TP48, alturas de 10 cm, puertas y uso para tapias se resolvieron en la reunión comunicada el 21-10-2026. Ver [aclaraciones confirmadas](aclaraciones-ticoblock-2026-10-21.md). El cuerpo conserva las fuentes y hallazgos originales del día 20.

# Croquis3R: investigación de los insumos y del cálculo actual de TicoBlock

Fecha: 20 de octubre de 2026. Estado: análisis de documentos recibidos; no se cambió la aplicación.

## 1. Lo que entiendo del proceso y del cambio de enfoque

**El proceso actual se basa en modulación: contar paños de determinados largos y tipos, identificar columnas y aplicar una tabla de piezas por paño.** El croquis sirve para producir esas cantidades. El cálculo principal del Excel es determinista y se puede llevar a Django sin usar IA para hacer las operaciones.

Para Croquis3R conviene conservar el editor y agregar una capa de paños, columnas y recetas de materiales. La estimación de ejemplo que hoy usa área neta × 12,5 blocks/m² no reproduce los Excel recibidos: estos separan TP37, TP50, paños completos, ventanas regulares, de cocina y de baño, puertas, columnas y vigabloques. Tampoco basta con descontar el área de una ventana: su receta ya incorpora una cantidad específica de bloques. [S1, S2]

**Hay dos archivos Excel entregados, pero ambos son variantes del modulador de casas.** Uno tiene visible la cuadrícula y el otro la tabla de ingreso manual. La capacitación menciona además una herramienta llamada **CÁLCULO TAPIA**, que aparece en un escaneo, pero no encontré ese libro como archivo editable en las carpetas revisadas. No se debe confundir tener dos archivos `.xlsm` con tener las dos herramientas funcionales completas de casas y tapias. [S1, S2, S10, S12]

Con lo recibido ya se puede especificar y reproducir una parte considerable del cálculo de casas, y explicar un ejemplo concreto de tapia. **Todavía no están cerradas las reglas de tapias, las equivalencias de productos, las columnas según geometría ni todos los materiales de la solución completa.**

## 2. Alcance de la revisión

Se revisó la carpeta principal compartida y sus subcarpetas de herramientas, manuales, fotografías, capacitación y cliente de ejemplo. Las copias originales en Drive no se modificaron.

| Grupo | Evidencia revisada | Qué aporta |
|---|---|---|
| Excel | Dos `.xlsm`, con las cuatro hojas de cada libro, incluidas las ocultas, fórmulas, resultados guardados, validaciones y código VBA | Entradas, tabla de recetas y fórmulas reales |
| Manuales y fichas | Ocho PDF técnicos: dos versiones de 52 páginas del manual de montaje, manual ilustrado de 9 páginas, tres fichas de bloques, catálogo y ficha de ventanas | Modulación, componentes, tamaños y pautas de montaje |
| Presentación | PowerPoint de 12 diapositivas y catálogo JPEG | Modelos comerciales y listas de materiales de paquetes |
| Capacitación | Notas, 25 fotografías y dos escaneos PDF | Explicaciones de uso y captura del calculador de tapias |
| Fotografías de ejemplo | 65 imágenes del ZIP: viviendas, detalles de aberturas, columnas, proceso constructivo y tapias | Interpretación visual del sistema; no son por sí solas un expediente cuantitativo |
| Videos | Tres MP4 incluidos en el ZIP, inventariados | Su audio y secuencia completa no se analizaron en esta revisión |
| Expediente de cliente | La subcarpeta de ejemplo continúa vacía | Sigue faltando un caso completo y versionado para validación de extremo a extremo |

Se extrajo texto de los PDF y se inspeccionaron visualmente el manual ilustrado, las fichas y las láminas relevantes del manual de montaje. Se leyeron las fotos mediante hojas de contacto y se ampliaron los documentos relevantes. El escaneo de tapias se leyó visualmente. No se ejecutaron macros ni se abrieron los libros en Excel para recalcularlos. Las comprobaciones numéricas de la sección 8 son reconstrucciones independientes de fórmulas extraídas, no una certificación de funcionamiento en Excel.

## 3. Cómo funcionan los dos moduladores recibidos

### 3.1 Versión con cuadrícula: `MODULADOR TICOBLOCK.xlsm`

Su hoja visible es `MODULACION`. Las otras son `Hoja1`, `Hoja3` y `Hoja2`, ocultas. `Hoja1` está vacía; `Hoja3` presenta un pequeño desglose; `Hoja2` contiene la tabla de cálculo. [S1]

El flujo que se desprende de sus fórmulas es:

1. Representar la distribución en la cuadrícula de las filas 1 a 23.
2. Colocar códigos de paños y aberturas en las celdas.
3. Usar símbolos de columnas y ejecutar el conteo de figuras cuando corresponda.
4. Contar cada código mediante `COUNTIF`.
5. Llevar las cantidades a `Hoja2!F4:F20`.
6. Multiplicar por las recetas de TP50, TP37, longitud y varilla.
7. Sumar y mostrar el desglose de materiales.

El Excel **no mide automáticamente líneas dibujadas ni interpreta una fotografía**. Sus cantidades proceden de códigos de celdas y de símbolos, no de reconocer el espacio geométrico de una casa.

| Elemento | Códigos que cuentan las fórmulas | Celdas de cantidad en `MODULACION` |
|---|---|---|
| Paño completo | `2`, `1,5`, `1`, `0,5` | `E26:E29` |
| Ventana regular | `2V`, `1,5V`, `1V`, `0,5V` | `J26:J29` |
| Ventana cocina | `2VC`, `1,5VC`, `1VC`, `0,5VC` | `O26:O29` |
| Ventana baño | `2VB`, `1,5VB`, `1VB`, `0,5VB` | `T26:T29` |
| Puerta de módulo de 1 m | `P` | `AH27` |
| Puerta terraza de módulo de 2 m | `PT` | `AH28` |
| Columna lineal | Símbolo de hexágono reconocido por la macro | `Y27` |
| Columna T | Símbolo de cruz reconocido por la macro | `Y29` |

El primer conteo de paños usa `A1:AY23`, mientras los demás usan `B1:AY23`. Los códigos con coma decimal deben normalizarse en la aplicación; no conviene depender de cómo Excel interpreta texto y números según la configuración regional. Las fórmulas de `COUNTIF` no distinguen mayúsculas de minúsculas. [S1, `MODULACION!E26:AH29`]

### 3.2 Versión manual: `MODULADOR TICOBLOCK MANUAL.xlsm`

La hoja visible es **`MODULADOR `**, con un espacio final en su nombre. `MODULACION`, `Hoja1` y `Hoja3` están ocultas. La tabla de materiales conserva las mismas recetas de piezas de la versión con cuadrícula. [S2]

Aquí las entradas principales son `F4:F20`: el usuario escribe cuántos paños de cada clase tiene. Las columnas `G`, `H`, `I` y `J` calculan los totales a partir de esos conteos.

La diferencia relevante está en las columnas:

```text
MODULADOR !F22 = SUBTOTAL(109,F4:F21)   # cantidad de paños visibles
MODULADOR !F33 = F22 + 1               # columna lineal
MODULADOR !F34 = 0                    # columna T, valor inicial manual
MODULADOR !F35 = 0                    # columna codo, valor inicial manual
```

La regla `paños + 1` es compatible con una cadena abierta de paños que comparte una columna entre vecinos. **No determina por sí sola las columnas de una casa, un circuito cerrado, una intersección T, un portón o varias líneas independientes.** La aplicación deberá contar ubicaciones y tipos de columnas, no sumar esta regla a cada pared sin considerar conexiones.

En el archivo sin cantidades, esa fórmula produce una columna y 108 kg. Es un comportamiento que debe decidirse al migrar: no es evidencia de que un proyecto vacío deba presupuestar una columna.

### 3.3 Qué hace la macro

En ambos libros se extrajo el mismo procedimiento `Módulo1.bas / ContarFigurasPorTipo`. Recorre `ActiveSheet.Shapes`, cuenta formas automáticas de tipo hexágono y cruz, escribe los conteos en `Y27` y `Y29` y muestra un mensaje. No contiene un motor de cálculo adicional de bloques. [S1, S2, VBA]

Hay dos precauciones:

- Trabaja sobre la hoja activa. No identifica explícitamente la hoja de modulación.
- Solo escribe un contador cuando encuentra una figura de ese tipo. Si se elimina la última figura de un tipo, no hay una escritura explícita de cero al terminar; el valor anterior podría permanecer.

La migración web puede reemplazar esta macro por el conteo de columnas del modelo geométrico, incluyendo el caso de cero columnas.

## 4. Tabla de cantidades por paño que realmente contiene el Excel

Ambos libros titulan la tabla como **casa de 2,50 m de altura**. La siguiente tabla transcribe los coeficientes de `Hoja2!B4:J20` en S1 y de `'MODULADOR '!B4:J20` en S2. Son cantidades por **un paño**, no factores por m².

| Tipo | Largo del módulo (m) | TP50 por paño | TP37 por paño | Factor de varilla de pared del Excel | Fila |
|---|---:|---:|---:|---:|---:|
| Completo | 2,00 | 36 | 12 | 1,5 | 4 |
| Completo | 1,50 | 24 | 12 | 1 | 5 |
| Completo | 1,00 | 12 | 12 | 0,5 | 6 |
| Completo | 0,50 | 0 | 12 | 0 | 7 |
| Ventana regular | 2,00 | 15 | 5 | 1,5 | 8 |
| Ventana regular | 1,50 | 10 | 5 | 1 | 9 |
| Ventana regular | 1,00 | 5 | 5 | 0,5 | 10 |
| Ventana regular | 0,50 | 0 | 5 | 0 | 11 |
| Ventana cocina | 2,00 | 18 | 6 | 1,5 | 12 |
| Ventana cocina | 1,50 | 12 | 6 | 1 | 13 |
| Ventana cocina | 1,00 | 6 | 6 | 0,5 | 14 |
| Ventana cocina | 0,50 | 0 | 6 | 0 | 15 |
| Ventana baño | 1,50 | 20 | 10 | 1 | 16 |
| Ventana baño | 1,00 | 10 | 10 | 0,5 | 17 |
| Puerta terraza | 2,00 | 0 | 0 | Sin aporte en esta tabla | 18 |
| Puerta | 1,00 | 0 | 0 | Sin aporte en esta tabla | 19 |
| Ventana baño | 0,50 | 0 | 10 | 0 | 20 |

Lectura práctica:

- Un paño completo de 2 m usa **48 bloques de cerramiento: 36 TP50 y 12 TP37**. No incluye sus columnas ni vigabloques.
- El paño completo de 1,5 m usa **36: 24 TP50 y 12 TP37**.
- El paño completo de 1 m usa **24: 12 y 12**.
- El paño completo de 0,5 m usa **12 TP37**.
- Las recetas de ventanas regulares, cocina y baño tienen respectivamente 5, 6 y 10 TP37 por paño. Esto implica distintas cantidades de hiladas o zonas de cerramiento; el Excel no explica las cotas completas de cada abertura.
- Puertas y terraza aportan longitud al cálculo de la viga, pero cero TP37 y TP50 en sus filas. No significa que la puerta instalada no necesite marco, dintel, refuerzo u otros materiales.
- La columna `VARILLA` y el resultado final se rotulan como varilla de 3/8. Los factores fraccionarios no especifican por sí solos las longitudes de corte y aprovechamiento. Debe confirmarse si representan varillas comerciales equivalentes y bajo qué largo y traslapes.

**No hay receta operativa para baño de 2 m**, aunque existe su contador `T26`. No corresponde inventarla interpolando las otras filas.

## 5. Fórmulas adicionales y límites del desglose

En lo siguiente, `r` es una fila de la tabla anterior y `q[r]` la cantidad introducida o contada. Las referencias corresponden a `Hoja2` en S1 y `MODULADOR ` en S2, salvo indicación.

### 5.1 Bloques y longitud

```text
G[r] = F[r] × D[r]                   # TP50 de la clase
H[r] = F[r] × E[r]                   # TP37 de la clase
I[r] = F[r] × C[r]                   # metros de la clase
G21 = SUM(G4:G20)                    # TP50 total
H21 = SUM(H4:H20)                    # TP37 total
I21 = SUM(I4:I20)                    # metros lineales
F28 = H21
F30 = G21
```

La longitud incluye módulos de puertas y terraza. No debe equipararse sin revisión a la superficie neta de bloques ni al perímetro exterior de la casa: también puede contener paños interiores.

### 5.2 Vigabloques y alturas

```text
F38 = ROUND(I21 × 2.5, 0)            # una hilada, rotulada altura 2,70 m
F39 = F38 × 2                       # dos hiladas, rotulada altura 2,90 m
```

El factor es 2,5 vigabloques por metro lineal. El bloque N-12 viga tiene largo nominal 40 cm en su ficha, consistente con ese factor. La cantidad se redondea al entero más cercano, **no siempre hacia arriba**. [S5]

La hoja `MODULACION` tiene otro cálculo de presentación:

```text
G33 = G32 × 2.5
G34 = G33 × 2
G35 = G33 × 3                       # rotulado 3,10 m
```

Aquí no hay redondeo. Por tanto, el croquis y la tabla oculta pueden presentar cantidades distintas cuando `metros × 2,5` no es entero. La altura 3,10 aparece en el Excel, pero el manual comercial solo anuncia 2,50, 2,70 y 2,90 m. No debe habilitarse como configuración aprobada sin consulta. [S1, S2, S3 p. 2]

Las recetas base de bloques **no se recalculan con una altura libre**: son una tabla de 2,50 m y los niveles adicionales se resuelven con vigabloques. Falta confirmar cómo se compone la altura terminada con juntas, contrapiso y encuentros.

### 5.3 Mortero y varilla

```text
F42 = G21 + H21
F43 = ROUNDUP(F42 / 20, 0)           # mortero/pegablock
J21 = SUBTOTAL(109,J4:J20)           # suma de factores de varilla de pared
F45 = ROUND(J21,0)                  # varilla 3/8 pared
F46 = ROUND(I21/6,0)                # varilla 3/8 viga, una hilada
F47 = F46 × 2                       # varilla viga, dos hiladas
```

El mortero usa una unidad por cada 20 TP37/TP50 y la fila de peso considera 40 kg por unidad. No incluye explícitamente en esta fórmula el consumo por vigabloques, relleno de celdas, mochetas, cimentación o repello. Hay que confirmar producto, rendimiento y usos incluidos antes de presentarlo como lista completa.

El divisor 6 de la viga es compatible con un largo comercial de 6 m, pero las fórmulas no documentan pérdidas, anclajes ni traslapes. Además usan redondeo normal: un tramo corto puede producir cero varillas de viga. Eso es un límite del cálculo recibido, no una recomendación de omitir acero.

`SUBTOTAL(109,...)` excluye filas ocultas. Si se ocultan filas de entradas o refuerzos en una copia del libro, algunos totales pueden cambiar mientras las sumas normales de bloques y metros siguen incluyéndolas. Esa diferencia no debería trasladarse a una web como una regla de negocio implícita.

### 5.4 Peso

```text
M28 = 11 × F28                      # TP37
M30 = 16 × F30                      # TP50
M33 = 108 × F33                     # columna lineal
M34 = 108 × F34                     # columna T
M35 = SUM(M28:M34)
M43 = 40 × F43                      # mortero
F25 = M35 + M43
```

El rótulo `PESO TOTAL` no equivale al peso de toda la obra o de todo lo listado: el cálculo no incorpora explícitamente vigabloques, acero ni una multiplicación independiente para la columna codo de `F35`. En S1 los valores guardados, con los paños en cero, muestran dos columnas y 216 kg; en S2 muestran una columna y 108 kg.

## 6. Tamaños, variantes y pautas que aportan las fichas y los manuales

### 6.1 Fichas de producto

| Producto | Tamaño declarado | Peso por pieza | Unidades por cubo | Piezas/m² declaradas | Fuente |
|---|---|---:|---:|---:|---|
| TP37 | **Real:** 12 × 20 × 41 cm | 10,2 kg | 156 | 12,1 | S4, p. 1 |
| TP50 | **Nominal:** 12 × 20 × 54 cm | 15 kg | 108 | 9,25 | S6, p. 1 |
| N-12 viga | Nominal 12 × 20 × 40 cm; real 12 × 19 × 39 cm | 10,90 kg | 156 | 12,5 | S5, p. 1 |

Las fichas de los tres bloques declaran resistencia mínima a compresión de 133 kg/cm² y tolerancia de ±3 mm. Esto se registra como contenido de los documentos recibidos, no como una verificación independiente de cumplimiento o vigencia normativa.

Los nombres TP37 y TP50 **no coinciden literalmente con el largo declarado de la pieza** en las fichas. Deben existir campos separados para nombre comercial, dimensiones reales/nominales, largo modular de paño y SKU. No debemos convertir el nombre en una longitud física por simple división.

Las fichas muestran las combinaciones de 0,50, 1 y 1,50 m entre columnas: un TP37 para el módulo menor, TP37 con TP50 para 1 m y TP37 con dos TP50 para 1,50 m. El manual dibuja el traslape y el refuerzo vertical de las combinaciones. El Excel extiende su tabla a 2 m. **Falta confirmar en qué variantes y condiciones está autorizado ese paño de 2 m**, pues las láminas de modulación y la ficha destacan hasta 1,50 m. [S3 p. 3; S4; S6; S7 pp. 6–7]

### 6.2 Variantes del sistema

- El manual de montaje desarrolla un ejemplo de vivienda unifamiliar de aproximadamente 45 m² en espesores de **10 y 12 cm**, con detalles distintos de columnas, vigas y cimentación. Son ejemplos de un proyecto; no una receta universal por m² de casa. [S7 pp. 7–20]
- La capacitación distingue TicoBlock de 10 cm, de 12 cm y Ticolumna. Las notas asocian RESIN8 al bloque de 10 y mencionan Ticolumna para dos plantas. No hay aquí un cálculo completo entregado para Ticolumna o dos niveles. [S10, S11]
- El manual ilustrado indica adaptación de longitudes en incrementos de **50 cm**, y alturas de 2,50, 2,70 y 2,90 m. [S3 p. 2]
- Los diagramas muestran columnas y conexiones, acero perimetral, varillas verticales, contrapiso, refuerzo sobre aberturas y vigabloque. Por ello una receta de bloques no cubre automáticamente toda la solución constructiva. [S3 pp. 4–8]
- Las notas indican que las tapias se trabajan en 12 cm. Esa nota no define por sí sola separación máxima, cimentación, alturas autorizadas, cargas laterales o refuerzos para todos los casos. [S10]

### 6.3 Ventanas y puertas: dimensión comercial y dimensión del módulo

El catálogo contiene, con su notación original, ventanas de baño `1.375 × 600`, estándar `1.375 × 1.200`, cocina `1.375 × 800` y `1.875 × 800`, y puertas `1.375 × 1.900`, `1.875 × 2.100` y `2.875 × 2.100`. [S8 pp. 2–3]

Los valores parecen corresponder a milímetros: por ejemplo 1.375 × 600 sería 1,375 × 0,600 m. **Debe confirmarse esa unidad y la correspondencia de cada producto con el vano y con el módulo del Excel**, en lugar de tomar el código de módulo como ancho del marco.

La ficha general de ventanas indica hasta 1,50 m de ancho y 1,20 m de alto, mientras el catálogo menciona una ventana de cocina de 1,875 m. Esto puede corresponder a series diferentes, pero no se especifica. No es correcto unir ambas fuentes como un único rango de productos aprobado. [S8 p. 4; S9]

## 7. Qué puedo afirmar sobre el cálculo de tapias

### 7.1 Evidencia encontrada

Las notas dicen que se elige entre casa/modulación y tapia/Excel Tapias, y mencionan formas en C y cajón. El escaneo `Archivo_escaneado_20261020-1002.pdf` muestra un libro titulado **CÁLCULO TAPIA**, con pestañas `Tapia`, `DESGLOSE` y `DIAGRAMA`. [S10, S12]

En esa captura se distinguen entradas para módulos de 2, 1,50, 1 y 0,50 m a altura base 2,50 m. **Las unidades de entrada no son uniformes:** la primera fila muestra `12 METROS` de módulos de 2 m y la segunda `1 PAÑOS` de 1,50 m. La web debería pedir unidades claras y convertirlas explícitamente.

### 7.2 Ejemplo verificable de 13,50 m

| Concepto | Valor leído en el escaneo | Comprobación independiente |
|---|---:|---|
| Longitud de paños de 2 m | 12 m | Equivale a 6 paños de 2 m |
| Paños de 1,50 m | 1 | Aporta 1,50 m |
| Metros lineales | 13,50 | 12 + 1,50 |
| TP37 | 84 | (6 + 1) × 12 |
| TP50 | 240 | 6 × 36 + 1 × 24 |
| Columnas lineales | 8 | 7 paños + 1, consistente con una cadena abierta |
| Vigabloque una línea | 34 | Redondeo normal de 13,50 × 2,5 |
| Vigabloque dos líneas | 68 | 34 × 2 |

Las cantidades de bloques coinciden con las recetas de paño completo de los moduladores. Esto respalda una lógica común para este ejemplo, **pero no prueba las fórmulas completas ni los casos de esquina, circuito cerrado o terreno desnivelado del calculador de tapias**.

La captura también permite leer referencias comerciales: `708-24` para columna lineal TicoBlock 3,20; `708-21` para TicoBlock 37 cm; `708-22` para TicoBlock 50 cm; `708-5` para block viga. Son candidatos de mapeo observados en una captura, no artículos confirmados contra la base real de 3R.

Junto a ellos aparecen valores auxiliares cuyo encabezado no está visible y algunos dígitos no se leen con suficiente certeza: **no los clasifico como pesos ni precios confirmados**. También aparece una entrada aislada `+15000`, sin suficiente contexto para asignarle un concepto.

El recuadro lateral muestra un conversor de 27 m a 18 paños de 1,50 m. Es consistente con 27 / 1,50; no permite deducir cómo resuelve sobrantes de longitudes no moduladas.

### 7.3 Lo que todavía falta para tapias

- Archivo original **CÁLCULO TAPIA**, con sus hojas, fórmulas y diagramas.
- Criterios para tapia recta, C, L, cajón cerrado, tramos independientes y portones.
- Uso y conteo de columna lineal, codo, T y terminal; altura total de columna y empotramiento.
- Paño máximo por espesor y altura; tratamiento de largos sobrantes y pendientes.
- Cimentación, refuerzo, relleno y viga según condición del proyecto.
- Política de redondeo y desperdicio para compras.

No se encontró el libro mediante las carpetas revisadas ni mediante búsqueda de `tapia` y `tapias`. Sí hay un ejemplo visual útil; no hay base para afirmar que ya se puede migrar íntegramente esa herramienta.

## 8. Comprobaciones numéricas realizadas

Se reconstruyeron escenarios usando los coeficientes extraídos del Excel manual y aritmética decimal. No se alteraron las celdas originales ni se ejecutó su macro.

| Escenario | TP50 | TP37 | Metros | Columnas según `N+1` manual | Vigabloque 1 hilada | Mortero según Excel | Varilla pared según Excel | Varilla viga 1 hilada según Excel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sin paños | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| Un paño completo de 2 m | 36 | 12 | 2 | 2 | 5 | 3 | 2 | 0 |
| Seis de 2 m y uno de 1,50 m | 240 | 84 | 13,50 | 8 | 34 | 17 | 10 | 2 |
| Un paño completo de 0,50 m | 0 | 12 | 0,50 | 2 | 1 | 1 | 0 | 0 |

La segunda fila da 1.044 kg con la fórmula de peso del Excel: 36 × 16 + 12 × 11 + 2 × 108 + 3 × 40. Este peso excluye componentes ya señalados. La tercera reproduce las seis cantidades visibles principales del escaneo de tapia; mortero y varilla de esa fila son **resultados de la reconstrucción del modulador**, no datos visibles del escaneo.

Estos ejercicios permiten comparar una futura versión web con la lógica recibida. Los resultados extraños —una columna sin paños, cero varilla de viga en tramos cortos o redondeo normal de piezas— se conservan como hallazgos para consulta, no como reglas aprobadas para construir.

## 9. Diferencias, vacíos y riesgos de migrar literalmente

| Hallazgo | Evidencia | Qué debe resolverse |
|---|---|---|
| Falta el archivo de tapias | Solo está la captura y la mención en notas | Obtener el libro original |
| Nombres de bloques diferentes | Excel: TP37/TP50; catálogo comercial: TP40/TP48 | Confirmar equivalencias, variantes, fechas y SKU; no asumir renombramiento |
| Pesos distintos | Excel: 11 y 16 kg; fichas: 10,2 y 15 kg | Elegir datos vigentes por producto y propósito del peso |
| Paño de 2 m vs documentación ilustrada hasta 1,50 m | Recetas de ambos Excel vs S3/S4/S6 | Confirmar alcance por sistema y proyecto |
| Baño de 2 m sin receta | `MODULACION!T26` existe, pero no tiene fila en la tabla y no entra en `G32` | Rechazar o resolver ese módulo explícitamente |
| Vigabloque decimal en una vista y entero en otra | `MODULACION!G33` vs tabla `F38` | Definir cantidad de compra única y política de redondeo |
| Dos reglas diferentes para columnas | Macro de símbolos vs manual `N+1` | Modelo geométrico y tipología de conexiones |
| Conteo de columna potencialmente obsoleto | Macro no escribe cero si desaparece un tipo | Recalcular desde cero, sin conservar conteos anteriores |
| Peso incompleto | `F25`, `M35`, `M43` | Definir componentes incluidos y peso logístico |
| Altura de 3,10 m solo en Excel | `MODULACION!B35:G35` | Confirmar si está autorizada o es una posibilidad no operativa |
| Mortero de juntas verticales contradictorio | Notas: sin sisa vertical; S7 p. 21: horizontales; S13 p. 21 agrega verticales | Obtener instrucción técnica aplicable y versión de manual autorizada |
| Resistencia de concreto no uniforme dentro del manual | S7/S13 p. 5: 210 kg/cm²; p. 33: 280 para varios elementos y 175 para relleno de bloques | Que el responsable técnico determine qué especificación aplica a cada elemento |
| Series y medidas de ventanas no conciliadas | Ficha hasta 1,50 m; catálogo con 1,875 m | Separar series, medidas de marco y de vano |
| Diferencia entre catálogo JPEG y PowerPoint | Casa de 48 m²: JPEG indica ventana `1,875 × 1200`; texto de diapositiva 7 indica `1,375 × 1200` | Confirmar lista comercial vigente |
| Los libros no tienen un proyecto cargado | Paños en cero y columnas predeterminadas | Solicitar un caso real con croquis y resultado aprobado |

No se verificó la vigencia de normas citadas, la autenticidad o alcance de una aprobación profesional a partir del nombre de un PDF, ni la idoneidad estructural de una solución. El manual de montaje desarrolla ejemplos y exige decisiones de diseño e inspección según el proyecto; no hay una fórmula universal de cimentación o refuerzo aplicable a cualquier croquis.

## 10. Modelos comerciales: útiles como referencia, no como fórmula por área

El PowerPoint y el catálogo incluyen ocho modelos. Estas son las cantidades publicadas en las diapositivas 3 a 10; se conserva su nomenclatura comercial. [S14, S15]

| Modelo | Área declarada (m²) | Columna C | Columna E | TP48 | TP40 |
|---|---:|---:|---:|---:|---:|
| Casa 25 | 24,75 | 12 | 7 | 316 | 182 |
| Casa 39 | 39 | 18 | 9 | 432 | 282 |
| Casa 46 | 45,5 | 20 | 9 | 516 | 306 |
| Casa 49 | 48,75 | 20 | 10 | 482 | 307 |
| Casa 48 | 48 | 23 | 10 | 508 | 344 |
| Casa 42 + WC | 42, con walk-in closet | 22 | 11 | 594 | 360 |
| Casa 54 | 54 | 23 | 11 | 580 | 362 |
| Casa 63 | 63 | 28 | 12 | 620 | 402 |

También hay ventanas y precios de paquete. No incorporé esos precios como tarifas vigentes del sistema: deben confirmarse su fecha, alcance y relación con el catálogo de 3R. Las denominaciones C/E tampoco están conciliadas con lineal/T/codo de los moduladores.

Las cantidades no crecen simplemente en proporción al área: depende de la distribución y de las aberturas. Estos modelos pueden convertirse en plantillas y casos de validación cuando se obtengan sus croquis modulares, espesor, altura, versión y lista aprobada. Los renders pequeños de distribución no aportan por sí solos todas esas medidas.

## 11. ¿Tenemos los datos necesarios?

| Capacidad | Estado con los archivos actuales |
|---|---|
| Explicar el proceso y las entradas de ambos moduladores | Sí |
| Reconstruir la tabla de bloques por paño base de 2,50 m | Sí, con las 17 clases existentes y las limitaciones señaladas |
| Reproducir las fórmulas de vigabloque, mortero, varilla y peso del modulador | Sí como compatibilidad con el Excel, pendiente aprobación de reglas y redondeos |
| Migrar la captura manual de cantidades de paños | Hay evidencia suficiente para especificarla |
| Conocer algunos tamaños y pesos | Sí para las fichas recibidas; hay discrepancias con otros documentos |
| Calcular una tapia del ejemplo de 13,50 m | Sí como reconstrucción de ese caso, no de todos los casos de tapia |
| Migrar íntegramente el calculador de tapias | No: falta el archivo original |
| Generar automáticamente columnas correctas para cualquier croquis | No todavía: falta la regla de tipología y conexiones |
| Vincular productos inequívocamente al catálogo de 3R | No: faltan equivalencias confirmadas y consulta real |
| Presupuestar todos los materiales de una casa | No: faltan recetas de cimentación, rellenos, techo, instalaciones y otros alcances |
| Extraer con IA un croquis a partir de una foto y validarlo contra ejemplos | Falta un conjunto de croquis originales y resultados aprobados de la misma versión |

## 12. Enfoque propuesto para Croquis3R, sin implementarlo en esta etapa

1. **Ingreso por cantidades**, equivalente a la versión manual: elegir sistema, altura y número de paños por clase; producir un desglose trazable por receta.
2. **Ingreso por croquis**, aprovechando el editor: dividir cada pared en paños válidos, insertar columnas como objetos compartidos y asignar aberturas a módulos. Conservar las medidas libres como intención de diseño y señalar lo que requiere modulación; no redondear toda una casa silenciosamente.
3. **Ingreso por foto**, como una tercera vía hacia esos mismos objetos. La IA propone trazos, cotas y tipos; el motor de modulación valida y el usuario revisa. No se delega a la IA la invención de cantidades o reglas técnicas.
4. **Catálogo con equivalencias**, separando códigos comerciales, nombres de documentos, familias de sistema, medidas, pesos y SKU de 3R.
5. **Reglas versionadas**, diferenciando reproducción del Excel recibido de cambios que apruebe TicoBlock. Cada resultado debería conservar la versión de receta, entradas y redondeo utilizados.
6. **Tapias como flujo propio**, cuando se reciba el original y se aclaren los casos geométricos. No presentar la tabla manual de casas como si ya fuera la migración del libro de tapias.

El modelo de pared actual puede seguir sirviendo para dibujar, pero el material debería depender de sus paños y conexiones. Un usuario podría seleccionar «paño completo de 1,50 m» o «ventana de cocina de 1,50 m» y ver automáticamente la composición validada, con posibilidad de consultar su origen.

## 13. Preguntas concretas para TicoBlock y 3R

1. ¿Pueden entregar **CÁLCULO TAPIA** original y un ejemplo que coincida con el escaneo de 13,50 m?
2. ¿Cuál versión de los moduladores está vigente y cuándo se usa cada una?
3. ¿TP37/TP50 equivalen a TP40/TP48? ¿Son cambios de nombre o productos/espesores distintos?
4. ¿Cómo se mapea columna C/E a lineal, T, codo y terminal? ¿Puede una misma pieza servir a varias conexiones por rotación?
5. ¿El largo modular se mide a eje de columna, entre caras u otra referencia? ¿Cómo se consideran espesor y encuentros?
6. ¿Cuándo se permite un paño de 2 m? ¿Qué límites cambian entre casa, tapia, 10 cm, 12 cm y Ticolumna?
7. ¿Qué medidas de vano y de marco corresponden a V, VC, VB, P y PT? ¿Existe ventana de baño para módulo de 2 m?
8. ¿Se compra redondeando al alza, al entero más cercano o por empaque? ¿Los cortes permiten compartir sobrantes entre paños?
9. ¿Qué producto cubre el rendimiento de mortero de 20 piezas por saco? ¿Incluye vigabloques, rellenos y mochetas?
10. ¿Se mantienen los factores de varilla y el divisor de 6 m? ¿Cómo se agregan traslapes, anclajes y pérdidas?
11. ¿Qué manual e instrucción prevalecen para juntas verticales y resistencia del concreto?
12. ¿Quién aprueba recetas y modificaciones? ¿Qué resultados puede entregar 3R como estimación y cuáles requieren revisión profesional?
13. ¿Pueden aportar dos o tres expedientes completos: croquis, modulador con datos, lista de materiales, plano y versión aprobada?

## 14. Fuentes y localización de la evidencia

Las referencias de celdas se tomaron de los archivos recibidos. En S2 el espacio final de la hoja `MODULADOR ` forma parte de su nombre. Los links apuntan a los originales de Drive y no a enlaces temporales de descarga.

| ID | Documento o carpeta | Localización principal usada |
|---|---|---|
| S1 | [MODULADOR TICOBLOCK.xlsm](https://drive.google.com/file/d/1b9O9toBTdEyQ6E_uPm-FQ_NFsRJbvai1/view) | `MODULACION!E26:AH29`, `G32:G35`, `Y27`, `Y29`; `Hoja2!B4:M47`; `Módulo1.bas` |
| S2 | [MODULADOR TICOBLOCK MANUAL.xlsm](https://drive.google.com/file/d/1C_4BnWNQI1c44GxvQDMOSw2U1WaVpQuE/view) | `'MODULADOR '!B4:M47`, especialmente `F22`, `F33:F36`, `F38:F47`; `Módulo1.bas` |
| S3 | [Manual de construcción TicoBlock 2024](https://drive.google.com/file/d/1hnF0wBizGz3OTIzMku8kGOjnDb-VyX0z/view) | 9 páginas, especialmente 2–3 y 4–8 |
| S4 | [Bloque TP37, ficha](https://drive.google.com/file/d/1MZ1KaQlnoL1-eVQagSuzvrrwJqlDrPBb/view) | Página 1, datos técnicos y combinaciones |
| S5 | [Bloque N-12 viga, ficha](https://drive.google.com/file/d/1OMWvVb1OZDhDFzcKr5AZ18qmzj3DyjYI/view) | Página 1, dimensiones y peso |
| S6 | [Bloque TP50, ficha](https://drive.google.com/file/d/1B99HOtC8hpuBGmpvDuzZZyKFovDcDetX/view) | Página 1, datos técnicos y combinaciones |
| S7 | [Manual de montaje, Ing. Mauricio Carranza](https://drive.google.com/file/d/1GSKAFfXgevPQzSsw-13v06CwskxSMgoO/view) | 52 páginas; 5–24, 25, 30–33 y 42–45 para alcances, componentes y diferencias |
| S8 | [Catálogo de ventanas](https://drive.google.com/file/d/1R1f3Yy2rcWmqfttJQjqu6aLkumWL5NvX/view) | 4 páginas; medidas en 2–3 y ficha general en 4 |
| S9 | [Ficha técnica de ventanas](https://drive.google.com/file/d/1exJ0uOO0hkZsmgPqsTi4aha1VDz22QEr/view) | Página 1 |
| S10 | [Notas de capacitación](https://docs.google.com/document/d/1xgagzocDZKhBRTry--e75l507JkCcZsx4JhoYOyreyc/edit) | Fecha 20-10-2026; flujo, tapias en 12 y juntas |
| S11 | [Fotografías de presentación](https://drive.google.com/drive/folders/1NAIz4gKKGcf3a8yyCCjUANoiRobgXQV6) | 25 JPG y dos PDF; modelos, combinaciones y aspectos técnicos |
| S12 | [Escaneo del calculador de tapia](https://drive.google.com/file/d/1HWhhpqploeb2oZhfWDGa0uaAf1eYz3jd/view) | `Archivo_escaneado_20261020-1002.pdf`, página 1 |
| S13 | [TicoBlock sellado CFIA.pdf](https://drive.google.com/file/d/11BIhWJXgpUXOPq6Gv6-PXw67gBIlz-Ai/view) | 52 páginas; diferencia sobre juntas en p. 21 y especificaciones de concreto en pp. 5 y 33 |
| S14 | [Presentación Catálogo 3R y TicoBlock](https://drive.google.com/file/d/1v1X04qqt21-pYPbJVWP4M2ExLSYGf_4Y/view) | Archivo PowerPoint de 12 diapositivas; modelos en 3–10 |
| S15 | [Catálogo JPEG](https://drive.google.com/file/d/1a3_ggneAePtCldJMQV6oDroei1FVu-_E/view) | Tabla de paquetes y diferencias de nomenclatura/ventanas |
| S16 | [Fotografías de ejemplo](https://drive.google.com/drive/folders/1HjkhCzdCI5ayHGb4qReYPI8ZkbXZHkRU) | ZIP con 65 imágenes y 3 videos; obra, aberturas y tapias |
| S17 | [Carpeta del cliente de ejemplo](https://drive.google.com/drive/folders/1cnYbMp0_nkZrwknkbsDJGK3kuLVxFX0N) | Vacía al revisarla |

### Identidad de los dos Excel analizados

| Archivo | Tamaño | SHA-256 |
|---|---:|---|
| S1, modulador con cuadrícula | 45.582 bytes | `82d4a611367f0c9d1b4dad89e21e86ac34d4252e8c0383083f610e89d2436e31` |
| S2, modulador manual | 45.528 bytes | `5d73ce07bf796744b477ef37526d8ec824775c65ae48a7a588ca55da7302846f` |

Las copias y extracciones de trabajo se conservaron separadas del código de la aplicación. Este informe documenta lo observado y las decisiones pendientes; no convierte automáticamente los coeficientes recibidos en pautas técnicas aprobadas.
