# Paneles ajustables y listas PDF · 27/10/2026

Implementado y comprobado en local; pendiente de despliegue.

## Uso

- Arrastrar el borde entre cada panel y el croquis para cambiar su ancho. El centro ocupa el espacio disponible inmediatamente.
- Los tamaños se recuerdan en ese navegador. Doble clic en cualquier borde restablece ambos tamaños. También permite Tab y flechas; Inicio/Fin aplican los límites.
- Mínimos: izquierda 180 px, derecha 210 px. Se limita el máximo para conservar espacio central; en pantallas de 900 px o menos se conserva la distribución móvil y se ocultan los tiradores.
- Descargar ofrece croquis PDF/PNG y dos listas PDF independientes: Con precios y Sin precios.
- La lista se calcula con el documento abierto, sin exigir guardarlo. Si hay configuración sin aplicar o medidas inválidas, se muestra el error y no se descarga una lista incompleta como correcta.
- La lista sin precios nunca consulta la base comercial. Incluye cantidades, unidades y pendientes de construcción.
- La lista con precios usa la homologación y consulta vigentes del servidor: importes con IVA, fecha de consulta y subtotal parcial cuando faltan precios; pendientes identificados expresamente. No se aceptan precios ni cantidades enviados por el navegador como resultados confiables.
- No se modifica la revisión del proyecto al descargar o ajustar paneles. No hay migraciones ni dependencias nuevas.

## Validación

139 pruebas Django y 42 JavaScript. Casos de PDF: PNG existente, listas con/sin precios, cantidades recalculadas, precios del servidor, errores de documento, autenticación y CSRF. PDF de ambas listas renderizados con Poppler y revisados visualmente. Tabla con cabecera repetida y flujo de páginas automático.

Editor local: arrastre real del borde, ajuste por teclado, mayor ancho del lienzo, persistencia al recargar, menú de descarga y descarga sin precios. Croquis de prueba conservado en revisión 3. El script de despliegue comprueba ambos PDF dentro de su prueba transaccional.
