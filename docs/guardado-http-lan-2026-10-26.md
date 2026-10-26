# Guardado de croquis y acceso HTTP en la LAN

## Reporte y alcance

El usuario informa que el croquis no se guarda, el editor empieza a presentar errores y no muestra una explicación visible. La consola muestra además un aviso de Cross-Origin-Opener-Policy (COOP) sobre el origen HTTP de la LAN. Se verificó que producción enviaba `same-origin` por HTTP.

Ese aviso significa que el navegador ignora COOP en ese origen; por sí solo no demuestra la causa de un POST/PUT fallido. No se dispone aún de la respuesta de la solicitud original del usuario para atribuirle una causa definitiva. Un dominio servido por HTTP tampoco resolvería la advertencia: hace falta un origen confiable, como HTTPS o localhost.

## Cambios

- El modo explícito `DJANGO_LAN_HTTP=1`, activado en Compose de la LAN, omite únicamente COOP para HTTP fuera de loopback. HTTPS, localhost y las IP de loopback conservan COOP. El modo general conserva la configuración de Django.
- Las cookies se llaman `croquis3r_sessionid` y `croquis3r_csrftoken`. Los nombres predeterminados de Django podían colisionar con otras aplicaciones de la misma IP, porque las cookies no se separan por puerto. Es una posible causa del problema reportado, no una causa comprobada en su solicitud concreta.
- Guardar muestra progreso, confirmación o error junto al botón, bloquea clics repetidos mientras espera y conserva el dibujo ante un fallo.
- Una sesión vencida indica cómo iniciar sesión en otra pestaña y reintentar sin cerrar el dibujo. El token CSRF se lee de la cookie actual en cada solicitud.
- Una respuesta HTML o una redirección al login no se interpreta como un guardado correcto. Si el guardado tiene éxito y falla la actualización posterior de la biblioteca, se informa que el croquis ya está guardado.

No se desactivan autenticación, CSRF ni los demás encabezados de seguridad. No hay migraciones ni cambios en recetas, cantidades o registros existentes.

## Dónde encontrarlo

En **Atenciones → Croquis y plantillas dibujadas**, debajo de la tabla de cálculos por paños. Los croquis conservan su guardado independiente de las atenciones del calculador manual.

## Verificación local

- 126 pruebas Django y 34 pruebas JavaScript aprobadas; sintaxis JavaScript, dependencias Python y ausencia de migraciones comprobadas.
- Pruebas específicas: guardar, abrir desde Atenciones, actualizar revisión, cookies de otra aplicación, rechazo sin sesión/CSRF y encabezados HTTP/HTTPS/loopback.
- En navegador se guardó un croquis de prueba local, se abrió desde Atenciones y se simuló cerrar sesión en otra pestaña. El aviso de fallo quedó visible y el dibujo permaneció abierto. Al iniciar sesión de nuevo, se guardó como revisión 2; al repetir con la versión final quedó en revisión 3 sin recargar el editor.
- Las pruebas automáticas usan una base de prueba independiente. El croquis de prueba local está identificado por nombre; no se borraron registros.

## Despliegue

La autorización administrativa instalada corresponde únicamente al paquete anterior `897308d80fbf`. Esta entrega necesita un paquete e instalador de aprobación propios, con commit y SHA-256 fijos; no se reutiliza el permiso anterior para ejecutar código nuevo.

Al aplicar el cambio de nombres de cookies, los usuarios deberán iniciar sesión de nuevo una vez. Antes de actualizar, conservar cualquier dibujo todavía sin guardar; no recargar una pestaña con cambios pendientes. Las cuentas y los croquis existentes permanecen en la base.

Referencias: [Django: SECURE_CROSS_ORIGIN_OPENER_POLICY](https://docs.djangoproject.com/en/5.2/ref/settings/#secure-cross-origin-opener-policy), [HTML: obtención de COOP](https://html.spec.whatwg.org/multipage/browsers.html#obtain-a-cross-origin-opener-policy).
