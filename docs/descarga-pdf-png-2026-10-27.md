# Descargar croquis en PDF o PNG — 27-10-2026

La última versión confirmada en producción al iniciar esta tarea es `907a291106cc`, con las mejoras de zoom, cuadrícula y columnas independientes. La siguiente entrega incorpora el cambio solicitado al botón de descarga.

## Comportamiento

El botón de la lámina ahora dice **Descargar**. Al pulsarlo abre un diálogo con **PDF**, **PNG** y **Cancelar**. Se desactiva mientras el croquis está vacío/cargando y durante la preparación del archivo. El diálogo admite cancelación con Escape y bloquea los atajos de edición mientras está abierto.

PNG conserva la exportación de la lámina completa desde SVG, con nombre, área y cotas visibles, sin depender del zoom. PDF usa exactamente esa lámina y la ajusta sin distorsión a una página A4, horizontal o vertical según su proporción, con márgenes de 12 mm. Se descarga como archivo, sin abrir el diálogo de impresión. El PDF contiene una imagen de la lámina; no es un plano vectorial ni un proyecto editable.

**Descargar proyecto** mantiene el archivo `.croquis3r.json` para continuar editando. No se modifica el formato del proyecto, su importación ni el cálculo de materiales. Exportar PDF/PNG no guarda ni cambia revisiones del proyecto.

## Implementación y límites

El navegador genera el PNG. Para PDF lo envía por POST multipart a `/api/export-pdf/`, en el mismo servidor de Croquis3R. Se requiere sesión activa y CSRF. No se envía el dibujo a servicios de terceros ni se almacena el archivo en el servidor.

El servidor admite únicamente PNG estático de hasta 8 MB y 2400 × 2400 píxeles. Verifica y decodifica la imagen, la compone sobre fondo blanco y genera el PDF en memoria. Rechaza archivos corruptos, formatos distintos y dimensiones excesivas. La respuesta es un adjunto privado con `no-store`.

ReportLab genera el PDF y Pillow verifica la imagen. Se fijan `reportlab==5.1.0`, `Pillow==13.0.0` y `charset-normalizer==3.5.2` en el archivo de dependencias; el inventario de versiones comprueba también estos paquetes. Fuentes de las versiones consultadas: [ReportLab en PyPI](https://pypi.org/project/reportlab/5.1.0/) y [Pillow en PyPI](https://pypi.org/project/pillow/13.0.0/).

## Verificación local

137 pruebas Django y 42 JavaScript aprobadas. Se verifican respuesta binaria PDF, imágenes horizontal/vertical, fondo transparente, sesión/CSRF, rechazo sin crear proyectos, errores de red/sesión y el selector de formatos. Dependencias coherentes y sin migraciones nuevas.

En navegador se descargó un PDF real y se comprobó la opción PNG y Cancelar. El croquis conservó su revisión 3. Con pypdf se verificó una única página A4 y que la imagen quedara dentro de los márgenes; con Poppler se renderizó y se inspeccionó visualmente la página completa, sin recortes ni elementos de selección.

El actualizador incorpora una descarga PDF con sesión/CSRF dentro de su comprobación transaccional. Se prepara un paquete específico para aplicar estos cambios; la confirmación del despliegue se registra después de ejecutarlo.
