# Recuperación de versión — 10 de noviembre de 2026

El paquete de anotaciones `6b8070e8c7d5` terminó correctamente el 9 de noviembre a las 17:35 UTC. Después, a las 22:44 UTC, systemd inició simultáneamente múltiples unidades históricas de actualización. La unidad `907a291106cc` terminó a las 22:45 UTC y volvió a publicar la aplicación antigua; el trabajador Blender permaneció en `6b8070e8c7d5`. El HTML remoto confirmó la pantalla antigua sin logo. No se atribuye a caché del navegador. No se ha confirmado qué operación inició simultáneamente esas unidades.

El diagnóstico administrativo solicitado (`git status --short` y `git diff --stat`) no produjo salida según el responsable: no había cambios locales que preservar en archivos versionados en ese momento. Los registros de la actualización antigua reportaron conservación de 4 artículos, 4 atenciones, 1 plantilla de objeto y 16 croquis.

## Corrección preparada

- El instalador retira las unidades históricas mediante una condición de systemd que exige una autorización inexistente, conservando scripts y registros. Comprueba primero que no haya unidades activas.
- La unidad nueva usa `RemainAfterExit=no` y una marca de intento previa al script, comprobada por systemd y por el ejecutor. Un paquete intentado no se repite automáticamente, aunque falle; una recuperación posterior necesita otro paquete revisado.
- Instalador y actualizador comparten un bloqueo exclusivo por proyecto. Las actualizaciones futuras rechazan commits que no desciendan del checkout instalado.
- Se mantienen respaldo PostgreSQL, verificación del volcado, comprobación de registros, pruebas independientes, render Linux y procedimiento de reversión existentes. No se restauran bases ni se importan datos locales.

Pendiente de autorización administrativa y verificación posterior. Este documento no certifica que la recuperación ya esté aplicada.
