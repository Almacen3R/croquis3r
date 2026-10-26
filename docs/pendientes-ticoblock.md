# Pendientes y estado vigente de Croquis3R

Actualizado: 26 de octubre de 2026. Mantener este registro junto con las [reglas confirmadas](aclaraciones-ticoblock-2026-10-21.md) y la [actualización de paños y puertas](panos-y-puertas-2026-10-26.md), sin reemplazar los datos desconocidos por supuestos.

## Información pendiente de TicoBlock

| Dato | Estado | Tratamiento actual |
|---|---|---|
| Peso de bloques TP48/TP40 y columnas de 10 cm | Pendiente | No se calcula peso para la familia de 10 cm. |
| Consumo de mortero en 10 cm | Pendiente | Se muestra «Pendiente»; no se copia el factor de 12 cm. |
| Consumo de acero/varilla en 10 cm | Pendiente | Se muestra «Pendiente»; no se copia el factor de 12 cm. |
| Perling, chorreado, anclajes y refuerzos en uniones de 10 cm | Pendiente | Fuera del desglose actual. Cero vigabloques no significa cero refuerzo. |
| Reglas de entrepiso, cimentación y dimensionamiento para segundo piso | Pendiente | Solo se controla la compatibilidad: 12 cm con columnas. |

Las cantidades de bloques por paño de 10 cm **ya se confirmaron iguales** a las de 12 cm; esa tabla no es un pendiente. Desde el 26-10-2026 se admiten puertas por módulo de 0,50, 1, 1,50 y 2 m; se conserva la Amplia de 3 m previamente confirmada. La medida de 1,50 m no se etiqueta automáticamente como baño. El croquis nuevo propone paños de 1,50 m o menos, con preferencia ajustable.

## Estado técnico comprobado

- Desarrollo local: SQLite en `db.sqlite3`.
- Servidor LAN: `http://192.168.0.214:8013/`, PostgreSQL 18 exclusivo y contenedores `croquis3r-app-1` / `croquis3r-db-1`, ambos saludables. `/health/` devolvió 200 en la última comprobación. PostgreSQL está en uso, no solamente preparado.
- Código servidor: `/opt/apps/croquis3r`; datos: `/data/projects/croquis3r`. El acceso SSH existente es válido para el servidor; su nombre de perfil no limita su uso a Inventariotec.
- Reglas del 21 de octubre (familias, puertas y asistente por metros) y corrección de identificadores sobre HTTP LAN: aplicadas en el servidor; se verificó el commit `43db872e4d48` y `/health/` correcto. La corrección adicional de selección/guardado de puertas se aplicó posteriormente y se verificó en producción en el commit `a85dfb3aa61d`.
- Git remoto: publicado en https://github.com/Almacen3R/croquis3r, rama `main`. Código, pruebas y documentación están versionados; datos y secretos se excluyen.
- Actualizaciones de producción: mediante `scripts/update-server-lan.sh`; la versión `43db872e4d48` fue aplicada por el usuario y comprobada por SSH.
- Respaldos externos y Drive: pendientes de su etapa operativa; no se activaron tareas nuevas.

## Error de identificadores en HTTP LAN

Síntoma: el segundo clic al dibujar una pared fallaba con `globalThis.crypto.randomUUID is not a function`. También podía afectar puertas, ventanas, columnas y duplicaciones, que comparten el generador.

Causa: el editor invocaba directamente `crypto.randomUUID`, disponible en contextos seguros. HTTP por una IP LAN no es equivalente a `localhost` para esa restricción. La [especificación Web Crypto del W3C](https://www.w3.org/TR/WebCryptoAPI/#crypto-interface) marca `randomUUID` como `SecureContext`; `getRandomValues` no tiene esa restricción.

Corrección local: usar el generador nativo cuando exista; en HTTP construir UUID v4 con `crypto.getRandomValues`, conservando aleatoriedad criptográfica y bits de versión/variante. No se usa la hora ni `Math.random` como sustituto.

Verificación: prueba real de navegador en un origen HTTP por IP privada, con `isSecureContext=false`, `randomUUID=undefined` y `getRandomValues=function`. Se reprodujo el error anterior y se generaron 10.000 UUID v4 válidos y distintos con la corrección; duplicar pared y abertura conservó sus vínculos. La página temporal solo sirvió datos ficticios, sin acceso a base de datos.

No requiere migraciones ni cambios de PostgreSQL. No se cambiaron contenedores ni datos del servidor para esta corrección local.


## Puertas: selección y validación de catálogo

Corrección del 21 de octubre: el campo numérico de largo permitía guardar puertas de 0,50 m. Ahora se elige entre Baño (módulo 1,50 m), Estándar (2 m, opción inicial) y Amplia (3 m), tanto al colocar como al editar. Si la elegida no cabe, se informa sin sustituirla por otro tipo. Al estirar extremos solo se admiten esos tres módulos; el tipo se deriva de la medida y se muestra en el lienzo, la lista y las propiedades, independientemente del nombre personalizado.

El servidor valida el catálogo al crear o actualizar croquis y plantillas completas. Los documentos anteriores se siguen leyendo sin modificarlos; si contienen una puerta fuera del catálogo, deben corregirse expresamente antes de guardar. El cálculo geométrico auxiliar conserva la lectura de medidas anteriores para poder ajustar una pared y después corregir su puerta. El modulador TicoBlock sigue indicando que esas puertas no son calculables.

Verificación: 87 pruebas Django y 23 pruebas de geometría aprobadas, incluidas creación/actualización por API, preservación de documentos anteriores rechazados y arrastre de ambos extremos con y sin cuadrícula. En navegador se comprobó el cambio Estándar → Baño → Amplia y los rótulos visibles, usando un ejemplo sin guardar. Evidencia: `screenshots/puertas-catalogo.png`. No requiere migraciones ni importación de datos.


### Verificación posterior en producción

Tras la ejecución de la actualización por el usuario se comprobó por SSH el commit `a85dfb3aa61d848682c4608fe1ecf5cee35eb396`, sin cambios versionados en el servidor, y `/health/` respondió correctamente. En navegador autenticado contra la IP LAN se confirmó Estándar de 2 m como selección inicial y el cambio a Baño de 1,50 m con rótulos visibles. Se usó el ejemplo sin guardarlo.

Prueba HTTP autenticada del guardado: los módulos de 0,50, 1 y 2,50 m devolvieron 400 con el mensaje de catálogo. Los módulos de 1,50, 2 y 3 m superaron la validación de catálogo y devolvieron 409 por una revisión deliberadamente incompatible. Esta revisión impidió cualquier escritura en las seis comprobaciones. Se comparó el documento completo y su revisión antes y después: sin cambios. No se crearon registros. Evidencia visual: `screenshots/puertas-catalogo-produccion.png`.


## Actualización del 22 de octubre: área y viga de amarre

Ver [regla y verificación de área/vigabloques](area-y-vigabloques-2026-10-22.md). La estimación de 12 cm incluye ahora viga a 2,50 m. El factor de 2,5 piezas por metro se verificó con la ficha nominal de 40 cm; se redondea hacia arriba por pared recta continua en croquis, o por paño independiente en el manual. No cambia la excepción de 10 cm ni sus pendientes de peso/mortero/acero. El área se muestra para contornos cerrados en planta, sin descontar espesores o patios. No se modifican resultados históricos guardados. Código local pendiente de desplegar.


## Usuarios y precios — 22-10-2026

Se implementan propietarios por usuario, acceso global para superusuarios y cierre de sesión POST. [Reglas de privacidad y migración](usuarios-y-privacidad.md). Los históricos sin dueño se conservan y solo los administradores pueden verlos/asignarlos. Las referencias originales de promociones siguen comunes; las copias guardadas son personales. Antes no existía separación por usuario. Corrección local pendiente de despliegue y migración aditiva en el servidor.

La [lista para vincular artículos y precios](articulos-para-precios.md) identifica productos/variantes y datos comerciales pendientes. Todavía no se conectó la base comercial ni se confirmaron códigos/precios reales. Pesos, mortero y acero de 10 cm siguen pendientes.


## Homologación y precios — 22-10-2026

Se verificó el archivo Homologacion de Drive y la conexión SQL de solo SELECT. Los 11 códigos suministrados están activos y sus precios de la lista GENERAL/CRC coinciden a dos decimales. Se corrigieron las descripciones cruzadas de bloques en el mapeo (TP50 → 44648; TP37 → 44649), sin editar Drive. Aclaración del usuario: columna comercial T = cruz, por tanto C lineal del croquis → 44647 y E esquina/cruz → 51234. Los precios ya incluyen IVA. [Reglas y correspondencias](homologacion-precios-3r-2026-10-22.md).

Integración local en croquis, cálculo manual y plantillas, con precios/suma parcial y pendientes explícitos. Atenciones guardan una instantánea que no cambia al abrir. No se importó ni modificó la base comercial. Credenciales y reportes de valores fuera de Git. Falta aplicar al servidor el paquete de esta revisión. Mortero, varilla y varias medidas de aberturas siguen sin código; los consumos técnicos de 10 cm siguen pendientes.

Actualización del 23-10-2026: el usuario autorizó explícitamente la transferencia y almacenamiento de la credencial el 22-10. Se transfirió por SSH a configuración privada con permisos 600, fuera de Git. El 23-10 se confirmó el contenedor sano y commit `5875b8b3f87c` en producción; la restricción anterior quedó resuelta. El inventario interno requiere sudo interactivo.

## Revisión de seguridad — 23-10-2026

Se actualizó el entorno local a Python 3.13.17/OpenSSL 3.5.9/pip 26.2.2, asgiref 3.13.0 y pymssql 2.4.5. La imagen con Python 3.12.15, Gunicorn 26.2.2 y PostgreSQL 18.6 se desplegó correctamente como `897308d80fbf` mediante la autorización limitada instalada por el administrador. Aprobaron las pruebas Windows/Linux, 120 pruebas en Docker/PostgreSQL y las 11 consultas comerciales; se preservó el contenido de los registros. [Inventario, fuentes, pruebas y límites](seguridad-dependencias-2026-10-23.md). Continúan pendientes los datos técnicos de peso, mortero y acero para 10 cm, los códigos comerciales faltantes y HTTPS en la LAN.

## Revisión de ventanas regulares — 23-10-2026

El usuario detectó una diferencia al contar bloques en una imagen de ventana de 1,50 m. Se releyeron directamente las celdas de ambos XLSM originales: `MODULADOR !C8:E8` del manual y `Hoja2!C8:E8` del otro modulador contienen 2 m, 15 TP50 y 5 TP37; las filas 9 contienen 1,50 m, 10 TP50 y 5 TP37. Son coeficientes fijos de origen, no un cálculo por dimensiones del vano. La transcripción coincide.

La receta equivale aritméticamente a cinco hiladas totales: 3 TP50 + 1 TP37 por hilada para 2 m; 2 TP50 + 1 TP37 para 1,50 m; y 1 TP50 + 1 TP37 para 1 m. Las miniaturas del calculador son símbolos CSS repetidos, no despieces a escala.

Corrección del 26-10-2026: el usuario plantea tres hiladas debajo y dos sobre la ventana regular. Esa distribución suma las cinco hiladas de la receta, no siete. Se descarta la interpretación anterior del asistente de cinco hiladas inferiores más dos superiores; los totales de 14/7 y 21/7 mencionados bajo esa hipótesis no corresponden a esta distribución. La ventana regular de 1 m conserva 5 TP50 + 5 TP37; la de 1,50 m, 10 + 5; y la de 2 m, 15 + 5. La ventana de cocina de 1 m tiene 6 + 6, equivalentes a seis hiladas totales con esa composición por fila. Su reparto superior/inferior no se establece únicamente a partir del total. No corresponde sumar otras dos hiladas a los coeficientes actuales ni modificar la aplicación por esa interpretación.

El usuario confirmó con TicoBlock dos hiladas sobre la ventana. El refuerzo de esa zona se trata como opción; recuerda varilla y una alternativa descrita tentativamente como cemento, pero esta última sigue sin confirmar. El conteo de bloques es independiente de presupuestar el refuerzo. El manual 2024, p. 6, muestra varilla y relleno trabajando juntos; no documenta que cemento solo sustituya al acero. No se registra esa equivalencia como regla aprobada. Esta duda del refuerzo no impide conciliar el conteo de bloques con las cinco hiladas totales.
