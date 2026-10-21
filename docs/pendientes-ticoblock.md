# Pendientes y estado vigente de Croquis3R

Actualizado: 21 de octubre de 2026. Mantener este registro junto con las [reglas confirmadas](aclaraciones-ticoblock-2026-10-21.md), sin reemplazar los datos desconocidos por supuestos.

## Información pendiente de TicoBlock

| Dato | Estado | Tratamiento actual |
|---|---|---|
| Peso de bloques TP48/TP40 y columnas de 10 cm | Pendiente | No se calcula peso para la familia de 10 cm. |
| Consumo de mortero en 10 cm | Pendiente | Se muestra «Pendiente»; no se copia el factor de 12 cm. |
| Consumo de acero/varilla en 10 cm | Pendiente | Se muestra «Pendiente»; no se copia el factor de 12 cm. |
| Perling, chorreado, anclajes y refuerzos en uniones de 10 cm | Pendiente | Fuera del desglose actual. Cero vigabloques no significa cero refuerzo. |
| Reglas de entrepiso, cimentación y dimensionamiento para segundo piso | Pendiente | Solo se controla la compatibilidad: 12 cm con columnas. |

Las cantidades de bloques por paño de 10 cm **ya se confirmaron iguales** a las de 12 cm; esa tabla no es un pendiente. Las puertas por módulo también están confirmadas: baño 1,50 m, Estándar 2 m, Amplia 3 m.

## Estado técnico comprobado

- Desarrollo local: SQLite en `db.sqlite3`.
- Servidor LAN: `http://192.168.0.214:8013/`, PostgreSQL 18 exclusivo y contenedores `croquis3r-app-1` / `croquis3r-db-1`, ambos saludables. `/health/` devolvió 200 en la última comprobación. PostgreSQL está en uso, no solamente preparado.
- Código servidor: `/opt/apps/croquis3r`; datos: `/data/projects/croquis3r`. El acceso SSH existente es válido para el servidor; su nombre de perfil no limita su uso a Inventariotec.
- Cambios locales pendientes de desplegar: reglas del 21 de octubre (familias, puertas y asistente por metros) y corrección de identificadores sobre HTTP LAN.
- Git remoto: publicado en https://github.com/Almacen3R/croquis3r, rama `main`. Código, pruebas y documentación están versionados; datos y secretos se excluyen.
- Actualización de producción: preparada mediante `scripts/update-server-lan.sh`, pendiente de ejecución con sudo y comprobación posterior.
- Respaldos externos y Drive: pendientes de su etapa operativa; no se activaron tareas nuevas.

## Error de identificadores en HTTP LAN

Síntoma: el segundo clic al dibujar una pared fallaba con `globalThis.crypto.randomUUID is not a function`. También podía afectar puertas, ventanas, columnas y duplicaciones, que comparten el generador.

Causa: el editor invocaba directamente `crypto.randomUUID`, disponible en contextos seguros. HTTP por una IP LAN no es equivalente a `localhost` para esa restricción. La [especificación Web Crypto del W3C](https://www.w3.org/TR/WebCryptoAPI/#crypto-interface) marca `randomUUID` como `SecureContext`; `getRandomValues` no tiene esa restricción.

Corrección local: usar el generador nativo cuando exista; en HTTP construir UUID v4 con `crypto.getRandomValues`, conservando aleatoriedad criptográfica y bits de versión/variante. No se usa la hora ni `Math.random` como sustituto.

Verificación: prueba real de navegador en un origen HTTP por IP privada, con `isSecureContext=false`, `randomUUID=undefined` y `getRandomValues=function`. Se reprodujo el error anterior y se generaron 10.000 UUID v4 válidos y distintos con la corrección; duplicar pared y abertura conservó sus vínculos. La página temporal solo sirvió datos ficticios, sin acceso a base de datos.

No requiere migraciones ni cambios de PostgreSQL. No se cambiaron contenedores ni datos del servidor para esta corrección local.
