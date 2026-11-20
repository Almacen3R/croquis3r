# Selección de paredes junto a columnas — 19 de noviembre de 2026

La zona transparente de las columnas tenía radio 0,23 m y se pintaba por encima de las paredes. Un clic junto a una columna seleccionaba esa columna; al colocar puertas o ventanas, el editor no encontraba una pared asociada y rechazaba el clic.

Se reduce el radio a 0,12 m. En selección normal, un clic sobre la figura visible de la columna sigue seleccionándola; en su margen invisible se busca la pared cercana. Las herramientas Puerta y Ventana resuelven la pared por distancia al cursor real, independientemente del orden de las figuras SVG, incluso cuando el clic cae sobre una columna. Se conserva la selección de aberturas, anotaciones y extremos para editar y arrastrar.

No cambia el documento, las cantidades, los precios ni los permisos. Sin migraciones ni dependencias nuevas. El archivo privado usuarios.txt queda excluido de Git.

Validación: 155 pruebas Django y 64 pruebas JavaScript aprobadas; sintaxis del editor comprobada. Los cuatro casos nuevos cubren el margen de columna, su figura visible, ambas herramientas de abertura, paredes verticales invertidas y diagonales, esquinas, extremos, columnas independientes y clics fuera de paredes. No se completó la prueba visual: el proceso del navegador de pruebas terminó inesperadamente en ambos intentos.

Cuenta pleon: ya existe en producción como vendedor activo, sin permisos administrativos. La contraseña solicitada en el archivo privado fue rechazada por el formulario de Django por similitud con el usuario; no se cambió. El responsable eligió una contraseña temporal: se generó, se estableció mediante Django Admin y se verificaron ingreso y acceso a la API de croquis. Se conservaron sus permisos. La clave está únicamente en .deploy/acceso-pleon-temporal.txt, excluido de Git. No guardar contraseñas en esta documentación.

Estado: desplegado y verificado en producción con cd4df3a2666a, el 19 de noviembre. Después de la clave temporal, se estableció y verificó la nueva contraseña aportada en usuarios.txt; la temporal dejó de ser vigente.
