# Usuarios, privacidad y cierre de sesión

Actualizado: 22-10-2026. Corrección local; aplicar la migración `0003_record_owners` antes de usar esta versión en producción.

## Antes

Croquis, plantillas de paredes y atenciones no guardaban creador; el personal autorizado compartía todos los registros. El acceso anónimo también estaba permitido cuando DEBUG era verdadero.

## Reglas actuales

- Toda entrada a la aplicación requiere una cuenta activa, también en local. `/ingresar/` acepta vendedores sin habilitar acceso al administrador Django.
- Vendedor: usuario activo sin `is_superuser`; ve y modifica solo sus propios registros, aunque tenga `is_staff` para otros permisos. «Miembro del personal» no equivale a administrador global de Croquis3R.
- Administrador: superusuario activo; ve todos los croquis, plantillas de pared y atenciones/listas personalizadas. En Administración puede asignar el campo Propietario de los registros anteriores.
- Las siete promociones originales de TicoBlock siguen siendo referencias comunes. Al guardar una lista modificada, esa atención pertenece a quien la crea. Lo mismo ocurre al guardar una copia de un registro permitido. Editar un registro ajeno como administrador conserva su propietario.
- El propietario se toma de la sesión. Enviar un `owner` por JSON o formulario no permite apropiarse de registros. Se filtran listas, búsquedas, enlaces directos, actualizaciones, reaperturas y copias. No basta con ocultar un botón.
- Las tres tablas ganan un FK nullable a usuario, con `SET_NULL`. No se adivina la autoría anterior ni se borran datos. Los registros sin dueño son visibles solo para administradores; si se elimina un usuario desde Administración, sus registros quedan conservados sin dueño.
- El módulo de Administración de estas tres tablas está restringido a superusuarios, incluso si a un vendedor con `is_staff` se le asignaron permisos Django de esos modelos.
- Cerrar sesión está en los encabezados del editor, calculador, plantillas y atenciones. Es POST con CSRF, invalida la sesión y vuelve al ingreso. Los GET a `/salir/` no cierran sesión. Las respuestas privadas incluyen `no-store`; tras salir, la API rechaza nuevas consultas.
- Cada persona necesita su propia cuenta; una cuenta compartida continúa representando un solo propietario y no separa a quienes la utilizan.

## Uso por el administrador

En Administración → Usuarios, crear cuentas activas individuales. Para vendedores, dejar sin marcar Superusuario y Miembro del personal. El formulario público de ingreso funciona con ellas. Solo habilitar Superusuario para quienes deban administrar y ver todos los registros. No se crearon cuentas nuevas en producción ni se cambiaron sus contraseñas.

Para asignar históricos: Administración → Sketches → croquis/plantilla/atención → Propietario → Guardar. El contenido JSON permanece de solo lectura en esos formularios. La asignación no recalcula materiales.

Antes no existían usuarios en la base local. Se creó únicamente allí `croquis_local`, con contraseña aleatoria en `.deploy/acceso-local.txt`, excluida de Git. No se trasladará esa cuenta al servidor. Se hizo respaldo SQLite local antes de migrar y se compararon todos los campos anteriores de las cuatro tablas de negocio: contenido intacto.

## Pruebas y despliegue

Pruebas con dos vendedores (uno con is_staff), administrador, registros de ambos y registros sin dueño. Incluyen filtrado, URLs adivinadas, actualización y copia falsificadas, asignación de propietario desde sesión, atenciones manuales y de promoción, permisos de Administración, login de vendedor normal, rechazo de inactivos, redirección externa de login rechazada, CSRF/cierre de sesión y falta de acceso anónimo con DEBUG verdadero/falso.

El script de actualización admite únicamente la migración aditiva esperada y conserva respaldo. Prueba en PostgreSQL de prueba antes de detener brevemente la aplicación para migrar. Compara registros antes/después normalizando únicamente la ausencia histórica del campo owner a NULL. El rollback puede usar la imagen anterior con estos campos nulos adicionales; no restaura ni sobrescribe la base automáticamente.

Resultado de verificación: 102 pruebas Django y 27 de geometría aprobadas (129 en total). Navegador local: ingreso real, identificación de cuenta/rol y botón Cerrar sesión; al pulsarlo volvió a `/ingresar/`. Evidencia: `screenshots/usuarios-cerrar-sesion.png`.
