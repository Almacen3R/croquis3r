# Investigación del módulo 3D de Croquis3R

Fecha de consulta: 6 de noviembre de 2026. Alcance: investigación y propuesta; sin implementación, instalaciones, compras ni cambios en producción.

La ruta recomendada es generar una casa 3D desde los datos del croquis y añadir una presentación cuidada de materiales, iluminación y entorno. La IA puede complementar esa presentación, pero no hace falta para construir la geometría base. Una suscripción de generación 3D no sustituye la integración ni confirma las dimensiones de una casa.

## Qué debe recibir el vendedor

Conviene distinguir tres productos:

1. **Casa 3D interactiva:** girar, acercarse, ocultar el techo y examinar la distribución. Sus distintas vistas deben representar la misma casa.
2. **Render publicitario:** imagen de alta calidad de fachada o interior, obtenida al iluminar y fotografiar virtualmente ese modelo.
3. **Imagen generativa:** propuesta visual producida o modificada con IA. Puede ser atractiva, pero exige comprobar puertas, ventanas y volúmenes; una imagen no implica que exista un modelo navegable detrás.

Propuesta de experiencia: abrir un croquis → pulsar Ver en 3D → elegir techo y acabados → revisar fachada y vista sin techo → descargar imagen o solicitar render de calidad alta. Los muebles, jardines y accesorios deben diferenciarse visualmente de los materiales incluidos en la estimación comercial.

## Datos que ya tiene Croquis3R

El código actual conserva paredes con extremos, altura y espesor; puertas/ventanas vinculadas a una pared con posición, ancho, alto y elevación; orientación visual de puertas; columnas con posición y tipo C/E; y documento JSON versionado. Esto permite proponer una conversión geométrica directa, evitando reinterpretar un PNG del croquis. Fuentes locales: `src/sketches/domain.py`, `src/static/croquis/geometry.mjs` y documentos de aclaraciones TicoBlock.

Hay límites importantes para la fidelidad física:

- Un módulo de puerta o ventana no equivale automáticamente al vano libre, al marco o a la hoja. El catálogo y las aclaraciones distinguen estas medidas; por ejemplo, baño de 1,375 m asociado a módulo de 1,50 m. Los módulos de puerta de 0,50 y 1 m que ahora permite el dibujo tampoco prueban que exista una puerta comercial idéntica.
- Los largos de referencia y encuentros deben convertirse con una convención clara: eje, cara o módulo. Extruir cada rectángulo por separado puede dejar solapes o huecos en esquinas y cruces.
- El tipo C/E indica función, pero para modelar el perfil real hacen falta secciones y dimensiones vigentes de columnas.
- Las alturas y elevaciones visuales de aberturas admitidas por el editor necesitan contrastarse con las medidas comerciales y su instalación real.
- `floor_level` es una configuración de cálculo; todavía no es un modelo con plantas independientes, elevaciones, losas y escaleras.
- El croquis no define techo, pendiente, aleros, cielo raso, acabados, terreno ni mobiliario.

La primera visualización puede usar valores de presentación seleccionados y revisables. Para presentarla como una representación fiel de la casa del cliente, los parámetros físicos deben quedar confirmados y guardados con la revisión utilizada.

## Comparación de opciones

| Opción | Qué aporta | Integración y valoración para Croquis3R | Costo público consultado |
|---|---|---|---|
| Visor propio con Three.js | Geometría, materiales e interacción en navegador | Mayor control sobre el croquis y sus módulos; requiere desarrollar encuentros, aberturas, techos y catálogo visual | Licencia MIT sin tarifa por casa; sí hay costo de desarrollo y recursos |
| Blender | Imágenes y animaciones de calidad alta desde una escena preparada | Complemento del visor; puede ejecutarse por lotes con scripts | Software gratuito, incluido uso comercial; cómputo, preparación artística y operación aparte |
| Planner 5D Business | Reconocimiento de planos, proyectos interactivos y renders | Alternativa comercial relevante. Verificar importación desde nuestros datos, catálogo TicoBlock, edición, exportación y marca antes de elegir | Prueba anunciada de €99, una vez; integración de producción personalizada |
| Floorplanner | Planos, visualización 3D e infraestructura de exportación | Alternativa con API para integraciones a medida; necesitamos alcance y cotización de empresa | Contrato de integración por consultar; no equiparar planes individuales a API empresarial |
| Meshy | Generación de objetos 3D y texturas mediante IA/API | Útil para accesorios o pruebas. No lo adoptaría como generador de la geometría oficial de la vivienda sin una prueba de fidelidad | Pro anunciado a US$20/mes. API Image to 3D estándar con textura 2K/4K: 30 créditos en modelos indicados por la tabla |
| Tripo | Generación de objetos 3D desde imagen, texto o varias vistas | Candidato a experimentos de decoración o modelos auxiliares; comprobar escala, geometría y resultado antes de reutilizar | Tabla API H: imagen a 3D con textura estándar, US$0,30 por tarea base; extras aparte |
| Twinmotion | Presentaciones, imágenes, video y panoramas a partir de modelos existentes | Alternativa para producción visual asistida por una persona; no asumir que sea un servicio automático integrable con Django | US$445/puesto/año si corresponde licencia pagada o Cloud; condiciones gratuitas ligadas al umbral de ingresos publicado |

Las capacidades y precios anteriores se apoyan en las fuentes enlazadas a continuación; las valoraciones de encaje son conclusiones de esta investigación, no garantías de los proveedores.

### Base propia con Three.js

Three.js permite extruir formas, aplicar materiales PBR y exportar GLB/glTF. Lo usaríamos para construir una escena desde las medidas confirmadas y mantener correspondencia entre objetos del plano y objetos 3D. La biblioteca ofrece las piezas de visualización; la lógica específica de TicoBlock seguiría siendo nuestra. Fuentes: [extrusión](https://threejs.org/docs/pages/ExtrudeGeometry.html), [materiales PBR](https://threejs.org/docs/pages/MeshStandardMaterial.html), [exportación GLB/glTF](https://threejs.org/docs/pages/GLTFExporter.html) y [licencia MIT](https://github.com/mrdoob/three.js/blob/dev/LICENSE).

### Blender y calidad publicitaria

Blender permite renderizar sin interfaz y automatizar tareas; su uso comercial está permitido. Proponemos preparar cámaras, luz, materiales y una biblioteca visual reutilizable, y generar imágenes de alta calidad en un proceso separado. Su coste de licencia cero no significa renderizado instantáneo ni infraestructura gratuita. Fuentes: [renderizado por línea de comandos](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html), [uso comercial y propiedad de creaciones](https://www.blender.org/support/faq/).

Texturas y luces de entorno con licencia adecuada pueden mejorar mucho la apariencia sin IA. Poly Haven publica sus activos bajo CC0, con uso comercial permitido. Los modelos específicos de productos TicoBlock podrían prepararse una vez y reutilizarse. [Licencia de activos de Poly Haven](https://polyhaven.com/license).

### Servicios de planos y visualización

Planner 5D Business distingue entre proyectos editables/navegables y resultados de imagen. Anuncia una prueba de €99 que incluye 10 reconocimientos de plano a proyecto 3D, 10 imágenes y un mes de acceso; la producción requiere definición comercial y técnica. Su ejemplo de marketing no debe copiarse como si fuera ya un contrato de API validado para Croquis3R. [Integraciones y prueba empresarial](https://planner5d.com/business/api-integrations).

Antes de contratar habría que probar si acepta geometría estructurada de Croquis3R o exige reconocer de nuevo una imagen; cómo conserva escala, aberturas y columnas; y qué formatos reales permite recuperar. Una imagen de planta con apariencia 3D y un proyecto interactivo son resultados distintos.

Floorplanner confirma integración mediante API y remite las integraciones personalizadas a su equipo. Sus planes de usuario no bastan para presupuestar una integración con Croquis3R. [Programa de integración](https://floorplanner.com/partners).

### IA para modelos auxiliares

Meshy documenta generación asíncrona desde imagen. Su ayuda anuncia Pro a US$20/mes con acceso API; su tabla API cobra 30 créditos para una generación estándar texturizada 2K/4K en las configuraciones publicadas. Para presupuestar hay que confirmar saldo, modalidad de créditos y opciones de la cuenta, sin convertir créditos a dólares por una tasa inventada. Fuentes: [planes](https://help.meshy.ai/en/articles/12062933-which-meshy-plan-is-right-for-you-free-vs-pro-vs-premium-vs-ultra), [precio API](https://docs.meshy.ai/en/api/pricing), [entrada imagen a 3D](https://docs.meshy.ai/en/api/image-to-3d).

Tripo publica pago por uso, US$0,01 por crédito y, en su tabla H, 30 créditos por imagen a 3D con textura estándar. Extras de resolución, geometría y posprocesado incrementan el costo. Cien tareas de esa configuración base sumarían US$30; no equivalen a cien casas terminadas y revisadas. [Precios API Tripo](https://developers.tripo3d.ai/en/pricing).

Una malla generada desde una vista aislada no ofrece por sí sola el contrato de paredes, vanos y habitaciones del croquis. Usaríamos estas herramientas inicialmente para muebles, decoración o pruebas controladas. Para adornos comerciales también debe quedar clara la licencia aplicable al plan y la posibilidad de almacenar y reutilizar los archivos.

### Ruta asistida de publicidad

Twinmotion está orientado a visualización de modelos importados. Su licencia publicada permite uso gratuito a determinados usuarios y empresas bajo el umbral de US$1 millón de ingresos; la licencia pagada cuesta US$445 por puesto al año y cubre también los casos que requieren Cloud. Antes de elegirlo, corresponde verificar la condición de la empresa y la estación gráfica necesaria. [Licencias](https://www2.twinmotion.com/license), [descripción del producto](https://www.twinmotion.com/ai-info).

Para imágenes con IA, Veras documenta un control de variación geométrica. Eso refuerza la necesidad de revisar la correspondencia visual cuando se utiliza generación para publicidad; no supone una garantía dimensional. No se propone como API automática ya confirmada. [Controles de imagen de Veras](https://documentation.chaos.com/space/Veras/1175388181).

## Propuesta de arquitectura futura

```text
Croquis guardado y revisión
        ↓
Conversión a dimensiones físicas confirmadas
        ↓
Modelo 3D + acabados + techo + cámaras
        ├── Visor web: giro, zoom, vista sin techo e imágenes rápidas
        ├── Escena de render: imágenes publicitarias y, después, video
        └── IA opcional: accesorios o propuestas visuales sujetas a revisión
```

Django seguiría gestionando usuarios, permisos, trabajos y archivos; PostgreSQL guardaría parámetros y referencias, y los modelos/texturas/imágenes irían a almacenamiento de archivos. El modelo derivado debe vincularse al identificador y revisión del croquis y a la versión del generador. Si cambia el plano, el sistema debe indicar que las imágenes anteriores corresponden a otra revisión.

El visor puede aprovechar el equipo del vendedor para dibujar en tiempo real. Los renders pesados deben ir a un trabajador separado con cola y límites de recursos, evitando bloquear las peticiones de la aplicación o los otros contenedores del servidor. La necesidad de GPU o cómputo externo se mediría con escenas reales; no se afirma un tiempo de render para el servidor actual.

La integración con un proveedor sería por su API, con credenciales en el servidor y consumo limitado por trabajo. MCP puede ayudar durante pruebas o autoría asistida, pero no es una condición para que el vendedor pulse un botón en Croquis3R. No se debe automatizar una página con la cuenta personal como sustituto de una API autorizada.

## Qué hace que se vea atractivo

La calidad no depende solo del generador: requiere materiales con escala coherente, luz, sombras, cámaras bien elegidas, un techo plausible y modelos de puertas/ventanas reconocibles. Prepararíamos pocos estilos consistentes: bloque aparente, acabado pintado y una variante de fachada; con techo y sin techo, sin convertir detalles decorativos en cantidades de la cotización.

Para publicidad, proponemos una aprobación del vendedor que confirme distribución, huecos, cubierta, acabados y elementos incluidos antes de compartir. Un techo o jardín de presentación elegido para una imagen no se vuelve automáticamente una especificación constructiva ni parte del precio.

## Plan para decidir antes de desarrollar

1. Elegir cinco croquis representativos: casa rectangular, casa en L, varias divisiones, paredes diagonales y segundo nivel como caso de alcance pendiente.
2. Completar una ficha física con vanos, alturas, perfiles de columnas, encuentros y dos o tres cubiertas de referencia. Reutilizar fotos y catálogo ya recibidos cuando corresponda.
3. Comparar la ruta propia con una prueba de Planner 5D Business si interesa reducir desarrollo. Confirmar primero la importación de nuestros datos y las condiciones de integración.
4. Usar el mismo conjunto de casos para cualquier experimento con Meshy/Tripo; evaluar corrección en varias vistas, no solo la belleza de una imagen.
5. Medir tiempo de preparación del vendedor, fidelidad de la distribución, calidad de una fachada, rendimiento del visor, costo por resultado aprobado y esfuerzo de corrección.
6. Elegir el alcance inicial: una planta, paredes/columnas/aberturas, acabados básicos y techo sencillo revisable; imágenes de fachada y vista sin techo. Posteriormente interiores detallados, recorridos y segundos niveles.

La decisión inicial fue comenzar por **visor propio Three.js y biblioteca visual reutilizable**, sumar **Blender** para material publicitario y reservar la IA para usos donde aporte una mejora comprobada. La aclaración siguiente actualiza la prioridad y el papel de la IA.

## Actualización del alcance — 2026-11-07

El usuario aclara que la prioridad es presentar al cliente cómo podría verse su casa terminada. La primera versión debe conservar la estructura general del croquis: posición de paredes, puertas y ventanas, y sus alturas. No requiere modelar cada bloque ni reproducir todos los detalles de montaje. Los acabados, mobiliario, iluminación y entorno pueden ir más allá de TicoBlock y del catálogo de materiales cotizados.

Esto permite probar el resultado visual antes de completar los perfiles constructivos. El techo y los acabados que no estén definidos en el croquis serán propuestas revisables, no datos deducidos con certeza ni partidas añadidas automáticamente a la cotización.

### Papel de OpenAI

La documentación oficial de GPT Image 2.6 Sunburst indica que genera y edita imágenes a partir de texto e imágenes. Es un candidato para probar fachadas e interiores terminados utilizando vistas del modelo base y fotografías de referencia. Esta es una propuesta de uso, no una prueba de fidelidad ya realizada. [Modelo](https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst), [guía de generación de imágenes](https://developers.openai.com/api/docs/guides/image-generation).

Una imagen generada no equivale a una escena 3D navegable. Hay que revisar que respete los vanos y proporciones; distintas vistas generadas independientemente pueden producir discrepancias. No se plantea generar cada cuadro de un recorrido de forma independiente.

Para video, la tabla oficial de retiradas indica que Sora 2, Sora 2 Pro y Videos API dejaron de estar disponibles en la API el 24 de septiembre de 2026, sin reemplazo indicado en esa tabla. Por tanto, no se recomienda basar una integración nueva en esas API, aunque permanezcan páginas antiguas de modelos y ejemplos. Esta conclusión se refiere a la API, no a la disponibilidad de productos de consumo. [Retiradas oficiales](https://developers.openai.com/api/docs/deprecations).

### Flujo recomendado con el alcance aclarado

1. Derivar del JSON del croquis una escena sencilla con paredes y aberturas a sus alturas. No pedir a la IA que reconstruya las medidas desde una captura si ya existen como datos.
2. Obtener vistas de fachada, vista superior sin techo e interiores seleccionados.
3. Usar esas vistas y referencias fotográficas para probar propuestas de acabado con GPT Image. No se requiere entrenar un modelo propio para esta prueba inicial.
4. Revisar distribución y aprobar un estilo. Para un recorrido coherente, trasladar los acabados elegidos a materiales y objetos de la escena 3D; no asumir que el modelo de imagen los convierte automáticamente en una escena.
5. Ofrecer dos salidas: recorrido interactivo en el visor y video de una cámara que recorre la misma escena, renderizado por ejemplo con Blender. La generación de video por IA es opcional, no necesaria para tener un recorrido.

Como primera prueba de investigación, se propone un croquis representativo y unas pocas referencias para comparar una fachada terminada y un interior. Se medirán conservación de aberturas, calidad visual, esfuerzo de corrección y costo por imagen aprobada antes de elegir proveedor y presupuesto. La API de imágenes tiene consumo facturado; no se fija un costo por casa sin medir resolución, calidad y repeticiones.

Se identificó en Drive la carpeta [Fotografías presentación](https://drive.google.com/drive/folders/1NAIz4gKKGcf3a8yyCCjUANoiRobgXQV6). Esta actualización no supone una revisión visual de sus fotografías ni su envío a un proveedor de IA. No se implementó el módulo ni se contrataron servicios.
