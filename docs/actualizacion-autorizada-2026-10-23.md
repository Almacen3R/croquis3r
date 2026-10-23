# Ejecutor de actualización aprobada de Croquis3R

Se confirmó que SSH responde, sudo requiere autenticación y producción permanece en `5875b8b3f87c`. No se encontró un proceso activo del actualizador de seguridad. Sin la salida del intento del usuario no se conoce el punto exacto del timeout.

`scripts/install-approved-security-update.sh` prepara una autorización administrativa **exclusivamente para el paquete 897308d80fbf**. Todavía no se ha instalado ni se han cambiado permisos del servidor. Se validaron sintaxis Bash/Python y compatibilidad de claves Git y permisos de carpetas.

El administrador debe ejecutar el instalador con sudo una vez, revisando sus efectos:

- Verifica servidor, commit y los SHA-256 fijados del bundle y script revisados.
- Copia el paquete a una carpeta privada de root. Protege el checkout instalado como propiedad de root, sin modificar propietarios del volumen PostgreSQL. El operador SSH dejará de poder editar directamente el código instalado; podrá preparar paquetes en su carpeta personal. El administrador conserva sus facultades normales mediante sudo autenticado.
- Valida la configuración Git y desactiva hooks, fsmonitor y configuración global para la ejecución administrativa.
- Instala una unidad systemd fija y un ejecutor de root. Ninguno permite seleccionar rutas, comandos o revisiones arbitrarias.
- Agrega solo tres comandos exactos a sudoers, comprobados con visudo: `croquis3r-update start`, `status` y `logs`. No concede sudo general, shell libre ni pertenencia al grupo docker.
- `start` inicia la tarea en segundo plano; sobrevive al cierre de SSH. `status` informa estado/resultado y `logs` muestra los últimos 120 renglones del registro de esa unidad. El límite de ejecución es 45 minutos. El resultado debe verificarse; no se supone éxito solo por iniciar la tarea.

El instalador por sí solo **no inicia** el despliegue. Después el agente puede ejecutar:

```bash
sudo -n /usr/local/sbin/croquis3r-update start
sudo -n /usr/local/sbin/croquis3r-update status
sudo -n /usr/local/sbin/croquis3r-update logs
```

La autorización no permite actualizar futuras versiones sin otra aprobación administrativa del paquete. Es una delegación de esta tarea concreta, no un mecanismo general de despliegue automático. No se almacena la contraseña de sudo.

Para retirar esta autorización el administrador debe quitar `/etc/sudoers.d/croquis3r-approved-update` y validar sudoers con visudo. Eso no cancela una tarea que ya esté ejecutándose; no debe interrumpirse una migración sin revisar su estado. Para que el agente gestione versiones futuras sin una nueva aprobación de root hace falta diseñar y revisar un ejecutor permanente con aislamiento y configuración protegida; no se habilita implícitamente en esta entrega.

La inspección del ejecutor administrativo de otra aplicación fue rechazada por revisión automática por estar fuera del alcance. No se leyó ni se utilizó; el mecanismo anterior se preparó únicamente para Croquis3R.
