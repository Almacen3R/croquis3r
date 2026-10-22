# Homologación y precios de 3R — 22-10-2026

## Fuente y aclaraciones

Se leyó el archivo [Homologacion](https://docs.google.com/spreadsheets/d/19sEv02yI8LzaI3dB4t2DEVWF3KlATenWDA3I_8E4THA/edit), pestaña `Hoja 1`, rango `B2:F19`. No se modificó el archivo de Drive. Las descripciones manuales de TP50/TP37 están cruzadas: los códigos y precios del Excel sí coinciden con los productos correctos en la base. El usuario confirmó usar la descripción real y aclaró que la columna comercial **T es cruz**, y que los precios del Excel **ya incluyen IVA**.

## Correspondencias activas

| Producto de Croquis3R | SKU 3R | Identidad comprobada en la base |
|---|---|---|
| TP50 · 12 cm | 44648 | BLOCK 12X20X50 TB PREFA PEDREGAL |
| TP37 · 12 cm | 44649 | BLOCK 12X20X37 TB PREFA PEDREGAL |
| TP48 · 10 cm | 51976 | BLOCK 10X20X48 TB PREFA PEDREGAL |
| TP40 · 10 cm | 51975 | BLOCK 10X20X40 TB PREFA PEDREGAL |
| Columna C del croquis · lineal | 44647 | Columna comercial TIPO C, 3,25 m |
| Columna E del croquis · esquina/cruz | 51234 | Columna comercial TIPO T, 3,25 m |
| Vigabloque N-12 | 45245 | VIGA BLOCK TB PEDREGAL 12 X 20 X 40 |
| Ventana baño · módulo 1,50 m | 49190 | PVC con cedazo, 137 × 60 cm |
| Ventana regular · módulo 1,50 m | 49192 | PVC con cedazo, 137 × 120 cm |
| Ventana cocina · módulo 1,50 m | 49191 | PVC con cedazo, 137 × 80 cm |
| Puerta Estándar · módulo 2 m | 53798 | UPVC blanca, 1,87 × 2,10 m |

La C/E del dibujo representa la función del encuentro. La E no se busca por la letra E en el ERP: corresponde al artículo tipo T por la aclaración del usuario. No se usan codos. Las medidas de los marcos son comerciales; los módulos del croquis no se reemplazan por sus medidas libres.

## Origen de precio comprobado

La base comercial es SQL Server y permanece independiente del PostgreSQL de Croquis3R. Se consultaron únicamente metadatos y los artículos indicados. Esquema `ALMACEN_3R`: `ARTICULO`, `ARTICULO_PRECIO`, `IMPUESTO` y la moneda local de `GLOBALES_AS`.

Los 11 precios coinciden con el Excel **redondeados a dos decimales**, en la lista `GENERAL`, moneda `L`, cuya moneda local es `CRC`. Todos los artículos están activos y tienen unidad de venta `UND`. Se validó una fila vigente única por artículo. `PRECIO_BASE_LOCAL` está en cero para estos productos: **no se usa como precio de venta**. Los importes reales provienen de `ARTICULO_PRECIO.PRECIO` con lista, moneda y vigencia explícitas. No se elige la lista más barata ni se aplican descuentos de promoción por el espesor del bloque.

La cuenta suministrada se verificó con permiso SELECT, sin INSERT, UPDATE, DELETE, CONTROL o ALTER de base, y sin rol sysadmin. No se cambiaron permisos. El conector usa TLS obligatorio y modo de conexión read_only; el servidor presenta certificado interno, sin CA pública validada por esta integración. No se cambió la configuración de SQL Server. Las únicas instrucciones SQL que emite el proveedor son SELECT parametrizados y acotados a los SKU de la homologación.

## Comportamiento en la aplicación

- Croquis, cálculo por paños y listas de promociones muestran códigos, descripción comercial, precio unitario e importe.
- Puertas y ventanas físicas se añaden al apartado de precios por sus cantidades, separadas de la receta de bloques que deja sus vanos. No se descuentan otra vez bloques ni se multiplica la abertura por cada paño vecino.
- Los precios ya contienen IVA. Se desglosa el impuesto incluido usando la tasa del artículo; no se añade por segunda vez. Los once artículos comprobados tienen tasa 13 % y sin impuesto adicional.
- Se conserva la precisión decimal de la base al multiplicar y se redondea cada importe a dos decimales. El precio unitario mostrado se redondea a dos decimales; por eso puede haber centavos de diferencia frente a multiplicar la copia manual del Excel, cuyos unitarios ya estaban redondeados. No se usa float para calcular dinero.
- Se muestra **subtotal con precio**, número de renglones pendientes y fecha/hora de consulta. No se presenta como costo total de la casa; quedan materiales fuera del alcance de las recetas.
- Un código sin abrir, una cantidad desconocida, un artículo inactivo, un precio ausente/duplicado o una descripción/unidad incompatible se muestran pendientes. Una cantidad desconocida no equivale a cero. Un precio cero explícito sí se distingue de un precio inexistente.
- Las ventanas de 1,875 m no reutilizan el código de 137 cm. Los módulos de 0,50/1 m y puertas de baño/amplia no toman el precio de otro tamaño.
- Caché en memoria de hasta 60 segundos por lote/lista; sin sincronización ni tareas programadas. Se conserva la fecha real de la lectura. Si falla la consulta después de vencer la caché, no se inventan precios ni se conservan como actuales unos precios vencidos. Las cantidades siguen calculándose.
- Al guardar una atención se guarda la instantánea de precios, impuestos, códigos, subtotal y fecha junto a las cantidades. La vista histórica no consulta nuevamente la base comercial; recalcular prepara precios actuales y guardarlos crea/actualiza una revisión explícita. Se mantienen los permisos de propietario de Croquis3R.
- Las asignaciones antiguas con artículos ficticios conservan sus IDs y no se suman a este apartado. No se sobrescribió el catálogo histórico ni se importó masivamente la base comercial.

## Pendientes

Mortero/pegablock; varilla 3/8 con largo, grado y unidad de venta; puertas Baño y Amplia; ventanas amplias y correspondencias comerciales para otros módulos. El bloque 10×20×24 indicado sin código no se encontró mediante la descripción exacta proporcionada; no se le asignó otro artículo ni una receta. No se cambiaron las medidas admitidas de puertas por el rótulo antiguo «Puerta 1m (Baño)» del Excel: Baño sigue siendo módulo 1,50 m.

Siguen pendientes de TicoBlock peso, mortero y acero de 10 cm, y reglas de perling/chorreado. Tener precios comerciales no resuelve cantidades técnicas desconocidas.

## Configuración y verificación

Credenciales exclusivamente en `.env` local. Su transferencia y almacenamiento en configuración privada del servidor están pendientes de autorización explícita; no se incluyen contraseñas ni capturas/listados de precios en Git. El código solo versiona identidades y configuración de ejemplo vacía. El paquete de despliegue admite un archivo privado modo 600 fuera del checkout; no importa datos locales ni modifica la base comercial.

`python manage.py check_3r_prices --reference .deploy/homologacion-source.json --output .deploy/homologacion-verificada.json` contrastó los 11 códigos: activos, unidad compatible, descripción canónica correcta y todos los precios del Excel coincidentes a dos decimales. El informe y los precios quedan en `.deploy`, excluidos de Git. Ese comando no escribe en la base comercial.

120 pruebas Django y 27 de geometría aprobadas. Se cubren SELECT parametrizados, rechazo de cuenta con escritura, cifrado/read_only, moneda, precios duplicados/ausentes, descripción/unidad, precio cero real, errores sin secretos, caché, IVA sin doble cargo, precisión decimal, códigos confirmados, aberturas pendientes y conservación de la instantánea histórica. Verificación de navegador local: consultas reales sin guardar registros de prueba. Estado: probado en local; pendiente de aplicar en producción.

La revisión automática rechazó el intento de preparar la configuración SQL privada en producción por no existir autorización explícita para enviar/almacenar esa contraseña en ese destino. No se realizó la transferencia. Se completan código, pruebas y paquete sin secretos; el envío de la credencial y la activación en producción quedan pendientes de autorización.
