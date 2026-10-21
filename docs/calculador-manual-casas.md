# Estado vigente — 21 de octubre de 2026

Las aclaraciones de TicoBlock del 21-10-2026 sustituyen las dudas y opciones anteriores sobre puertas, espesores y alturas. Consulta [reglas confirmadas](aclaraciones-ticoblock-2026-10-21.md). La versión actual es `ticoblock-manual-2026-10-21-v3`; las secciones de verificación fechadas conservan la historia de pruebas.

# Calculador manual de casas

Disponible en `/calculador-casas/`, desde el encabezado del editor. Implementado el 20-10-2026.

## Uso

1. Indicar nombre y altura de referencia: 2,50, 2,70 o 2,90 m.
2. Ingresar cantidades enteras entre 0 y 100 para cada una de las 18 clases actuales de paño.
3. Indicar columnas C (lineales) y E (esquina/cruz). Alternativamente, elegir cadena abierta (paños + 1).
4. Pulsar **Calcular materiales**. El resultado incluye el aporte de cada clase y las fórmulas agregadas.
5. Usar **Imprimir resultado** para imprimir o guardar PDF mediante el navegador.

**Cargar ejemplo** completa seis paños de 2 m y uno de 1,50 m, una hilada adicional y cadena abierta. Después hay que pulsar Calcular materiales.

El cálculo manual se ejecuta en Django y funciona sin JavaScript. JavaScript facilita cargar el ejemplo, marcar resultados desactualizados e imprimir. Ahora permite guardar entradas y resultados por cliente con el botón Guardar atención, recuperarlos desde /atenciones/ y conservar la versión de recetas utilizada. El editor tiene ahora una integración geométrica con estas mismas recetas, descrita al final de esta guía; sus croquis sí usan el guardado existente.

## Plantillas de diseños recibidos

Disponible desde «Elegir una casa de plantilla» o `/calculador-casas/plantillas/`. Se incorporaron siete diseños del archivo [DISEÑOS DE CASAS CON CANTIDAD DE MATERIAL.docx](https://drive.google.com/file/d/17Pl4Paa5EPlqT16Z8UQVXnZq-rbxfOmA/view):

| Plantilla | Área declarada (m²) | Columna C | Columna E | TP48 | TP40 |
|---|---:|---:|---:|---:|---:|
| Modelo E | 24,75 | 12 | 7 | 316 | 182 |
| Modelo D | 39 | 18 | 9 | 432 | 282 |
| Promo A | 45,5 | 20 | 9 | 516 | 306 |
| Modelo estándar | 48,75 | 20 | 10 | 482 | 307 |
| Modelo J | 48 | 23 | 10 | 508 | 344 |
| Modelo G | 54 | 23 | 11 | 580 | 362 |
| Modelo 63 | 63 | 28 | 12 | 620 | 402 |

También se incluyen las ventanas de cada tabla. Las imágenes se extrajeron del documento, sin reconstruir geometría. El nombre Modelo 63 identifica el encabezado «MODELO 63 m2» de la fuente.

### Cómo usar una plantilla

1. Elegir una casa en la galería y revisar su dibujo. Pulsar la imagen para ampliarla.
2. Leer su lista original y asignar nombre a la copia de trabajo.
3. Modificar cantidades si el caso lo requiere y pulsar **Actualizar mi lista**. Cada renglón modificado conserva la cantidad original como referencia.
4. Usar **Restablecer cantidades originales** para volver a empezar.
5. Imprimir o guardar PDF para conservar la lista. Usar Guardar atención para recuperar los ajustes por cliente; también se puede imprimir o guardar PDF.

Las plantillas son listas de materiales, independientes del cálculo por paños. Los totales TP48/TP40 y C/E no permiten reconstruir inequívocamente la cantidad y clase de paños. C corresponde a lineal y E a esquina/cruz, según confirmación del responsable. Sigue pendiente aclarar los nombres TP48/TP40 frente a TP50/TP37. Tampoco se escala automáticamente por área ni se atribuye una altura no especificada.

Los guiones del original se guardan como **sin indicar**, no como cero. El Modelo E repite «Ventana 1,375 × 1200» con cantidad 2 y después con guion; se conserva una sola cantidad conocida de 2 y se muestra una nota de procedencia. Las medidas de ventanas, incluida «1,375 × 60», conservan su texto pendiente de aclaración de unidades. No se añaden mortero, varilla o precios a estas listas mediante factores de productos sin equivalencia confirmada.

Fuente: siete tablas, documento de 698.798 bytes, SHA-256 `b33c406448aa6d32add2e1d0156cb38d7738818f15aef0c0d2a1f8fe4b92a224`. Datos versionados en `src/sketches/house_templates.py`; imágenes originales en `src/static/croquis/houses/`. Las plantillas permanecen disponibles sin depender de Drive en tiempo de ejecución.

## Conceptos para una primera capacitación

- **Paño:** un tramo o módulo de pared; una pared larga puede contener varios paños.
- **Paño completo:** módulo sin abertura de puerta o ventana.
- **Columna:** elemento vertical del sistema. La cantidad y el tipo deben corresponder al proyecto; el sistema no determina aún los encuentros de una casa.
- **Hilada:** una fila horizontal de bloques. El modulador añade hiladas de vigabloque para sus alturas de referencia.
- **Receta:** cantidades de piezas que el Excel asigna a un tipo y largo de paño.

Si se parte de un modelo del documento, conviene usar Plantillas de casas. Si ya se conocen los tipos y cantidades de paños de un diseño propio, se usa Calcular por paños. Modificar cantidades en una plantilla no actualiza su dibujo. El área de la casa describe el diseño; no es un multiplicador de todos los materiales.

## Próximos cambios propuestos, todavía sin implementar

El guardado y recuperación por cliente ya está implementado. Queda convertir las imágenes de plantilla en croquis editables verificados; confirmar las reglas de división y clasificación de columnas, los códigos de los mismos productos en el catálogo de 3R y agregar su consulta. El cálculo de tapias sigue pendiente del Excel original. La lectura por foto será una entrada posterior hacia el mismo modelo revisable.

## Integración del croquis con las recetas

El editor ahora calcula su pestaña Materiales mediante `/api/ticoblock-estimate/`, usando las mismas recetas actuales y redondeos del calculador manual. El endpoint anterior `/api/estimate/` se conserva para validar geometría y para las reglas personalizadas previas; sus factores de ejemplo no se suman al desglose TicoBlock. La galería de diseños sigue siendo un flujo independiente de listas publicadas: sus imágenes no se han convertido en geometría editable.

### Cómo se propone la división

- Divide cada pared en sus encuentros con otras paredes y en los límites de los módulos de puertas y ventanas.
- En cada tramo libre propone paños completos, tomando primero el largo máximo configurado que quepa y luego el sobrante. El máximo predeterminado es 2 m, con prioridad 2 → 1,50 → 1 → 0,50 m confirmada por el responsable. Puede elegirse 1,50, 1 o 0,50 m como preferencia del cliente.
- Las aberturas sustituyen al paño completo, no se suman ni se descuentan otra vez por área. Puertas actuales: baño con módulo de 1,50 m, Estándar de 2 m y Amplia de 3 m. Las entradas antiguas de 1 m requieren revisión explícita. Ventanas permiten elegir regular, cocina o baño. No existe receta de baño de 2 m.
- Las medidas dibujadas se usan como **referencias modulares**. Todavía no se ha confirmado si cada largo del Excel es entre ejes, entre caras u otra referencia. No se suma ni resta media columna por extremo.
- Las posiciones y largos de módulo deben ser múltiplos de 0,50 m, con tolerancia numérica de 0,000001 para representación geométrica. El ancho de una ventana o puerta en este flujo es el módulo ocupado, no un vano libre confirmado.
- Admite una altura uniforme de referencia de 2,50, 2,70 o 2,90 m. La familia predeterminada es 12 cm (TP50/TP37). También admite 10 cm (TP48/TP40) con las mismas cantidades de bloques por paño, solo a 2,50 m y sin vigabloques. Ambos parámetros se aplican explícitamente desde Configurar altura, división y columnas.
- Altura visual y antepecho de una ventana no modifican su receta: el usuario elige la clase de ventana. La correspondencia exacta de vanos y cotas queda por confirmar.

Los pequeños círculos del dibujo representan límites de paños propuestos y posiciones de columnas por revisar. Una posición compartida entre paredes cuenta una vez. Se utilizan únicamente columna C (lineal) y columna E (esquina/cruz). Sus cantidades se ingresan manualmente en la configuración; aún no se clasifican automáticamente las posiciones geométricas. Si no se ingresan, los renglones de columnas indican **Pendiente**, no cero columnas necesarias. Las posiciones dibujadas no son una aprobación estructural ni una clasificación de productos.

Si hay medidas sin receta, alturas mixtas, encuentros no modulares o encuentros que atraviesan una abertura, la lista queda pendiente sin ofrecer una suma parcial. Cada observación permite seleccionar el objeto para corregirlo. Los croquis anteriores conservan sus medidas al abrirlos; pueden requerir correcciones para usar estas recetas.

El ejemplo nuevo es un rectángulo de 4 × 3 m, altura 2,50 m, puerta modular de 2 m y ventana regular de 1 m. Con máximo de paño de 1,50 m propone 10 paños, 173 TP50, 101 TP37, 14 sacos de mortero y 8 equivalentes de varilla de pared. No incluye hiladas adicionales de vigabloque; detecta 10 posiciones de columna por clasificar. Esto es un caso de software comprobado contra las recetas, no un expediente aprobado de construcción.

El CSV incluye la versión de recetas, observaciones y aporte de cada paño. Las opciones de modulación, cantidades manuales de columnas y clase de ventana se guardan con el croquis y sus plantillas, utilizando el mecanismo de guardado existente. No se alteran automáticamente los documentos ya guardados.

Pruebas: 52 pruebas Django y 8 de geometría aprobadas. Los casos nuevos cubren el ejemplo 4 × 3 m, el caso de 13,50 m, ventanas por clase, alturas y espesores incompatibles, puertas sin receta, encuentros T/X, paredes invertidas/diagonales, posiciones compartidas, persistencia y acceso/CSRF.

## Reglas y límites

Fuente: [investigación de insumos](investigacion-ticoblock-2026-10-20.md), secciones 4 y 5. Versión de recetas: `ticoblock-manual-2026-10-20-v2`.

- Las 17 recetas son las filas 4–20 del modulador manual. No se inventó la receta de ventana de baño de 2 m.
- Se usa aritmética decimal y redondeo Excel (mitades hacia arriba), incluyendo el redondeo inicial antes de duplicar la segunda hilada. El mortero se redondea hacia arriba.
- Las alturas superiores añaden vigabloques; no escalan los bloques base proporcionalmente al área.
- Las columnas se ingresan explícitamente por defecto. En cadena abierta se ignoran las entradas manuales y todas las columnas se muestran como lineales. Sin paños se devuelven cero columnas, diferencia deliberada frente al N+1 vacío del Excel, señalada en pantalla.
- El peso es parcial y conserva los factores del Excel, con sus discrepancias documentadas respecto de las fichas. No incluye vigabloques ni acero. El factor de columnas (108 kg) procede del Excel anterior; confirmar los pesos vigentes de C y E.
- Varillas son equivalentes del Excel. No se infieren cortes, traslapes o anclajes.
- No se incluyen cálculos de tapias, diseño estructural, recetas generales de cimentación, catálogo real, precios ni cotizaciones.
- La pantalla mantiene el control de acceso existente: anónimo solo en desarrollo; personal autenticado con `is_staff` en producción. POST protegido por CSRF.

## Verificación

`src/sketches/test_house_calculator.py` cubre el caso de 13,50 m (240 TP50, 84 TP37, 8 columnas, 34 vigabloques), un ejemplar de cada una de las 17 recetas, medios en redondeo, alturas, puertas, columnas manuales y cadena abierta, entradas inválidas, escape de HTML, acceso y CSRF.

`src/sketches/test_house_templates.py` compara las siete listas con la transcripción de origen y verifica ajustes sin modificar el original, guiones, ventana repetida, límites, acceso, CSRF y escape de HTML. Con esta incorporación pasaron 37 pruebas de Django; no se requieren migraciones nuevas.

El motor está en `src/sketches/house_calculator.py`. Para verificar:

```powershell
.venv/Scripts/python.exe manage.py test sketches catalog
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

## Aclaraciones del responsable sobre productos vigentes

Se confirmó que 3R compra y vende los mismos productos de TicoBlock; la tarea pendiente es vincular sus códigos en el catálogo, no buscar materiales sustitutos.

- Columna C: lineal, utilizada en tramos rectos.
- Columna E: esquina/cruz, utilizada tanto en esquinas como en intersecciones en cruz.
- El codo dejó de ser una opción vigente. Se retiró de formularios, resultados y exportaciones; no se conserva conversión o compatibilidad con esa opción en este prototipo local.

Las plantillas mantienen sus cantidades originales de C y E y muestran estos nombres aclarados. La clasificación de encuentros en T y otros casos particulares no se deduce automáticamente de esta aclaración. Los datos técnicos de peso siguen sujetos a confirmación. El cambio corresponde a la versión v2 de la configuración del cálculo, sin cambios en las recetas de bloques.

El usuario autorizó limpiar los datos locales relacionados con esta opción obsoleta. Se inspeccionaron los dos croquis y la plantilla de objeto existentes: no contenían codos, por lo que no hubo datos que eliminar. Para futuras eliminaciones de datos debe pedirse confirmación previa; esta autorización se limita a esta limpieza local.

## Flujo de atención y pruebas para vendedores

La entrada recomendada es `/atenciones/`. Ofrece tres opciones: partir de una plantilla conocida, ingresar paños o dibujar un croquis. Las atenciones manuales y de plantilla se buscan por cliente o proyecto; los croquis mantienen su biblioteca propia, también accesible desde esta pantalla.

- Guardar atención calcula en el servidor y almacena entradas, resultado, cliente, notas, fecha, versión y revisión. No acepta como resultado una lista enviada por el navegador.
- Abrir una atención muestra el resultado de su última revisión guardada sin recalcular. Continuar/editar utiliza las recetas actuales y requiere guardar de nuevo para actualizarla.
- Guardar copia conserva la atención original y crea otra. Si otra sesión guardó primero, se rechaza la sobrescritura y se ofrece conservar una copia.
- Las etiquetas de revisión distinguen columnas pendientes y cantidades sin confirmar; guardar no representa aprobación técnica.
- En el editor, los cambios de configuración sin aplicar bloquean el guardado y el CSV. Deshacer permite descartar ese borrador de configuración; no borra registros.
- El editor empieza vacío. Ver ejemplo carga un caso de práctica. Las medidas antiguas de croquis existentes no se corrigen automáticamente.

Se añadió la migración `0002_attention`, aplicada solamente a la base local. No se borraron registros ni se desplegó al servidor. Se conservaron dos atenciones claramente marcadas PRUEBA UX para comprobar recuperación. El detalle de escenarios y límites para retirar Excel está en `docs/verification.md`.

## Conciliación con el dibujo del usuario de 4 × 4 m

Se confirmó la prioridad de paños 2 → 1,50 → 1 → 0,50 m. El selector del máximo se aplica y recalcula automáticamente. Altura, espesor y cantidades de columnas conservan la acción Aplicar configuración; si hay cambios pendientes en esos campos, se indica expresamente.

La comparación original no tenía las mismas entradas: el cálculo manual incluía una ventana regular de 2 m y otra de 1 m; la versión guardada del croquis tenía ambas de 1 m. La ventana inferior estaba en medio de un tramo de 2 m, con 0,50 m de pared completa a cada lado. Eso cambia la lista de materiales aunque el perímetro siga siendo 16 m.

Se creó una copia local de verificación, sin modificar el croquis original. En la copia, la ventana inferior ocupa el módulo completo de 2 m y la puerta de 1 m está en el módulo central, tal como en el papel. Con C = 6 y E = 4, altura 2,50 m y máximo de 2 m, coincide con el cálculo manual: 10 paños, 16 m, 224 TP50, 94 TP37, 16 sacos de mortero, 11 equivalentes de varilla de pared, sin vigabloques adicionales ni varilla de viga y 6.338 kg de peso parcial según Excel.

Las cotas ahora tienen dos niveles exteriores: partes cercanas a la pared y total más afuera. La pared derecha muestra 1,50 + 1 + 1,50 m y, en la segunda línea, 4 m. Se consideran extremos de paredes, aberturas y límites de paños calculados, con soporte para tramos contiguos invertidos y diagonales.

La preferencia de paños largos procede de la indicación del usuario. Con las recetas actuales puede cambiar la combinación TP50/TP37 sin reducir el número total de bloques: en esta casa las variantes de máximo 1,50 y 2 m suman ambas 318 bloques, pero proponen 12 y 10 paños respectivamente. No se cuantifica un ahorro monetario sin consultar precios.


### Colocar columnas desde el croquis

1. Dibuja las paredes y sus puertas o ventanas. Las marcas pequeñas indican límites de paño propuestos.
2. Elige **Columna C** para una posición lineal, o **Columna E** para una esquina o cruce, y haz clic sobre la pared o una marca. Puedes colocar varias seguidas; pulsa **Esc** o **Seleccionar** al terminar. Las letras C/E quedan visibles en el dibujo.
3. Arrastra una columna para moverla. Para cambiar su clase, selecciónala y cambia **Tipo de columna**, luego pulsa **Aplicar medidas**. Duplicar activa la colocación de otra columna de la misma clase.
4. Revisa **Materiales**: cuenta cada columna dibujada una sola vez, aunque sea compartida por varias paredes. Desde la primera columna colocada se usan exclusivamente las dibujadas; las cantidades manuales anteriores no se suman. Los croquis antiguos conservan sus cantidades manuales mientras no coloques columnas.
5. Una columna intermedia divide los paños y cambia las cantidades de bloques. El sistema señala ubicaciones propuestas sin columna; mientras falten, el peso queda pendiente. Columnas fuera de pared, dentro de una puerta/ventana o fuera de un módulo de 0,50 m impiden mostrar un total.

Las columnas se guardan con el croquis y sus plantillas. Su dibujo es un marcador de posición, sin descontar dimensiones físicas de columnas a los largos modulares. La clasificación C/E se elige manualmente.


### Sugerir paños desde metros

En Calcular por paños, introduce los metros de cada tramo y elige 2 m (predeterminado), 1,50, 1 o 0,50 m. Pulsa Sugerir distribución. Usar reemplaza los cuatro conteos de pared completa; Agregar suma otro tramo. Luego revisa las aberturas y columnas y pulsa Calcular materiales. Las tapias usan este mismo flujo.

### Familias y puertas vigentes

La primera opción es 12 cm; las plantillas de promociones muestran su familia original de 10 cm. Cambiar de familia conserva las cantidades de bloques pero cambia los productos: TP50/TP37 ↔ TP48/TP40. 10 cm solo admite 2,50 m; su peso y consumos auxiliares no confirmados se muestran pendientes. Segundo piso solo permite 12 cm con columnas; no sustituye un cálculo estructural. Las puertas son Baño de módulo 1,50 m, Estándar de 2 m y Amplia de 3 m.

El ejemplo histórico de 4×4 m con puerta de 1 m conserva su evidencia antigua, pero no corresponde a una puerta de la oferta actual. Al abrir ese croquis el sistema pide revisar la puerta; no la estira automáticamente. Las atenciones mantienen sus resultados y recetas guardados.
