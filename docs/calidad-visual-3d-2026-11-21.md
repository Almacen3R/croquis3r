# Calidad visual 3D — 21 de noviembre de 2026

## Estado y uso

Aplicado y verificado en producción con el commit 91246276f8c2. Los ejemplos descritos a continuación permanecen solo en la base local, sin importarse al servidor. Vista de prueba local: http://127.0.0.1:8014/?sketch=10. Ejemplo: Casa de demostración 3D - 54 m2 - 21-11-2026, propiedad de croquis_local. Se dejaron dos imágenes verificadas en su historial para revisar sin volver a generarlas.

En Vista 3D → Acabados y techo se agrega Alero propuesto (0 a 0,60 m; inicial 0,25). El techo conserva su perfil plano o a dos aguas. Los aleros se generan solo en el perímetro exterior, incluyendo habitaciones con encuentros en T y plantas en L/U; no se agregan encima de divisiones interiores. Se muestra una base ilustrativa bajo los pisos.

En Imágenes de presentación → Encuadre se puede elegir Fachada de presentación o Vista actual del visor. La fachada intenta mirar la puerta exterior; la vista actual captura cámara, techo visible y puertas abiertas, incluso en recorrido interior. Las transparencias de edición no se convierten en acabados del render. Las imágenes son de 1280 x 960 y la proporción puede diferir del espacio del visor.

## Calidad

Se agregan divisiones de ventanas, repisas, paneles de puertas y manijas metálicas. Las manijas quedan opuestas a la bisagra y todos los detalles acompañan la apertura de la hoja. Hay texturas procedurales locales para pintura, madera y cubierta, vidrio con transmisión, cielo y sombras suaves. Los renders interiores usan luz suave de presentación, sin crear instalaciones eléctricas ni partidas comerciales.

Blender conserva CPU con dos hilos. Perfil: 24 muestras adaptativas, OpenImageDenoise y AgX; se mantienen 1280 x 960 y el timeout de 600 segundos. Las primeras pruebas reales Windows terminaron en aproximadamente 164-192 s para fachada y 359-387 s para interiores. El pico informado fue cercano a 369 MiB. No son tiempos garantizados para otros proyectos o para Linux. La prueba aislada del contenedor Linux terminó correctamente durante el despliegue: PNG 1280 x 960 verificado, sin red ni credenciales de producción.

## Datos y compatibilidad

presentation3d incorpora roof_overhang opcional (0 a 0,60). El JSON de la escena admite detalles decorativos separados, limitados a 4000 cajas de tipos permitidos, y una cámara con posición, objetivo y campo de visión validados. No se aceptan rutas, scripts, archivos Blender ni recursos externos.

Se conservan propiedad, privacidad, cuotas y descarga autenticada de la cola existente. No hay migraciones. Las piezas decorativas y opciones visuales no modifican paredes, vanos, área ni cantidades/precios. Las imágenes previas permanecen sin regenerarse automáticamente.

Se corrigió además el giro de 90° de un croquis con techo: ahora intercambia los ejes admitidos x/z, en lugar de producir y, que el servidor rechazaba.

## Verificación

Verificación inicial: 162 pruebas Django y 78 JavaScript aprobadas (240). Incluyen cámaras y límites, aleros de varias formas, límites exteriores con encuentros en T, privacidad, piezas decorativas, cuatro aperturas de puerta, conservación de materiales y compatibilidad de documentos anteriores. Importación real de los módulos del visor y comprobación Django sin errores.

Se revisaron visualmente renders de fachada e interior generados por Blender y se probaron historial y descargas de ejemplos mediante la aplicación local. El navegador automatizado no pudo iniciar por un fallo del runtime (registered runtime ownership is missing); El responsable probó posteriormente el visor desde su navegador y aprobó su aspecto para desplegarlo.

La prueba completa adicional terminó correctamente: solicitud HTTP autenticada → cola → trabajador → Blender → descarga privada, en 229,4 s. Trabajo local 8dad4aab-c129-4d03-9c3b-e7ba505681cc. Las dos imágenes locales iniciales y esta nueva fachada se conservan en el historial del ejemplo. Ninguna prueba creó ni cambió proyectos en producción.


## Seguimiento de disponibilidad y errores

El trabajo local solicitado por el responsable sí terminó: 3eb11a61-7101-4591-9fc0-99b227b279cb, de 16:28:35 a 16:34:40 UTC (aproximadamente 6 min 5 s). Blender y el trabajador estaban configurados y disponibles. No se cambió esa configuración para investigar el caso.

La interfaz muestra tiempo transcurrido, distingue cola/procesamiento/servicio sin respuesta y permite seguir descargando imágenes listas cuando el trabajador falta. Las consultas tienen un límite de 15 s y vuelven a intentarse; una solicitud de creación no confirmada recomienda revisar el historial antes de repetir. No hay reintentos automáticos de generación.

El listado y la solicitud nueva detectan trabajos running que exceden el timeout configurado más 60 s de margen y los marcan como interrumpidos, liberando la cuota de la cuenta. La limpieza se limita al ámbito autorizado del usuario; una pérdida temporal de latido no se considera por sí sola un fallo definitivo. Se mantienen permisos, cuotas y el timeout de Blender existentes. Sin migraciones ni cambios de configuración local.

Verificación final para despliegue: 165 pruebas Django y 82 JavaScript aprobadas (247), sin errores de comprobación Django ni de sintaxis. El responsable autorizó el despliegue de la mejora visual y los avisos. La configuración local de Blender se mantuvo intacta; el paquete debe superar la prueba aislada Linux antes de cambiar la aplicación productiva.


## Despliegue confirmado

Aplicado el 21 de noviembre de 2026. Unidad croquis3r-update-91246276f8c2: Result=success, ExecMainStatus=0. Blender Linux generó y verificó el PNG de prueba y pasaron las 165 pruebas Django con PostgreSQL antes de promover la aplicación y el trabajador. Sin migraciones pendientes. Se conservaron 4 artículos, 5 atenciones, 1 plantilla de objeto y 20 croquis, con huella de datos comprobada.

Verificación HTTP autenticada posterior: controles de encuadre y alero presentes; módulos visual-details3d.mjs y render-status.mjs disponibles; /health/ correcto; trabajador disponible; listado de imágenes devuelve límite de tiempo y tiempo transcurrido por trabajo. Las cuentas existentes siguen vigentes.

Respaldo previo: /data/projects/croquis3r/backup-staging/update-20261121T184207Z. Acceso: http://192.168.0.214:8013/. Antes de recargar una pestaña vieja, guardar el dibujo pendiente.
