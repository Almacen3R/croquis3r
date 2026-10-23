# Revisión de dependencias — 23 de octubre de 2026

## Resultado y alcance

Croquis3R ejecuta Django/Python y Gunicorn, con PostgreSQL para sus datos y pymssql para consultas SELECT a la base comercial. JavaScript se ejecuta en el navegador; Node solo se utiliza aquí para probar geometría. No hay PHP, React, Next.js, servidor Node, paquetes npm ni CDN de bibliotecas en este proyecto. No se modificaron otras aplicaciones del servidor ni el Node compartido de Codex.

Se confirmó por SSH el commit `5875b8b3f87cff3f57e073966fd286132efd540e` y el contenedor sano `croquis3r-app:git-5875b8b3f87c`. PostgreSQL aparece como `postgres:18-bookworm`. La regla sudo permite listar contenedores, pero no inspeccionarlos ni ejecutar comandos dentro sin autenticación interactiva: **no se comprobó aún la versión exacta de Python/PostgreSQL en esos contenedores**. El lock del commit desplegado identifica las bibliotecas anteriores; no sustituye un inventario del contenedor.

## Inventario y cambios

| Componente | Antes, local / código desplegado | Después, probado o preparado |
|---|---|---|
| Python local | 3.12.14, intérprete compartido | 3.13.17, `.venv` propio, probado |
| Python Docker | etiqueta flotante `3.12-slim-bookworm`, parche instalado sin verificar | `3.12.15-slim-bookworm`, pendiente de construir/aplicar |
| OpenSSL local de Python | 3.5.8 | 3.5.9, verificado |
| pip local | 25.0.1 | 26.2.2, verificado; fijado también en Docker |
| Django | 5.2.18 | 5.2.18, conservado; mínimo del manifiesto elevado a 5.2.18 |
| Gunicorn, solo Linux | 23.0.0 | 26.2.2, probado en Linux; WSGI con worker `sync` explícito |
| asgiref | 3.12.1 | 3.13.0, actualización de mantenimiento |
| pymssql | 2.4.4 | 2.4.5, actualización de mantenimiento; 11 códigos/precios verificados por SELECT |
| psycopg / psycopg-binary | 3.3.6 | 3.3.6, conservados |
| python-dotenv | 1.2.4 | 1.2.4, conservado |
| WhiteNoise | 6.12.0 | 6.12.0, conservado |
| sqlparse | 0.6.0 | 0.6.0, conservado |
| packaging | 26.3 | 26.3, conservado |
| typing_extensions | 4.16.0 | 4.16.0, conservado |
| tzdata | 2026.5 | 2026.5, conservado |
| PostgreSQL Docker | `18-bookworm`, parche sin verificar | `18.6-bookworm`, preparado; misma versión mayor |

La libpq incluida en psycopg-binary local informa 18.4: es la biblioteca cliente, **no** la versión del servidor PostgreSQL. Los avisos de 18.6 revisados afectan al servidor o a herramientas como psql/pg_dump; no se atribuyen automáticamente a libpq. El entorno local usa SQLite. No se afirma que todas las bibliotecas nativas embebidas estén libres de CVE a partir del análisis de paquetes Python.

## Qué vulnerabilidades aplican

- **PHP y Node:** los avisos oficiales del 21 de octubre son reales, pero no corresponden al servidor de esta aplicación. No se deduce que los demás contenedores del equipo estén cubiertos por esta revisión. [PHP](https://www.php.net/archive/2026.php#2026-10-21-5), [Node](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases).
- **Django:** 5.2.18 ya contiene las correcciones de octubre, entre ellas CVE-2026-77050 y CVE-2026-84429. Se conserva la serie 5.2 LTS; cambiar de versión mayor no es necesario para esos parches. [Aviso oficial](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/).
- **Python:** 3.12.14 era anterior a 3.12.15, que corrige problemas de SSL, extracción de archivos y agotamiento de memoria. La aplicación no implementa importación de archivos comprimidos ni un servidor TLS Python; presencia de una versión afectada no demuestra explotación remota del croquis. [Python 3.12.15](https://www.python.org/downloads/release/python-31215/).
- **pip:** el análisis inicial devolvió 12 entradas en pip 25.0.1, correspondientes a seis identificadores únicos: CVE-2025-8869, CVE-2026-1703, CVE-2026-3219, CVE-2026-6357, CVE-2026-8643 y CVE-2026-13346. Son rutas de instalación/descarga, no endpoints del croquis. La primera tiene mitigación por PEP 706 en Python 3.12; no se presenta como seis ataques remotos explotables. Se actualizó a 26.2.2, que también renueva certifi ante el incidente de autoridades certificadoras. [pip](https://pip.pypa.io/en/stable/news/), [Python](https://blog.python.org/2026/10/python-3151-3149-31317/).
- **OpenSSL:** el intérprete local antiguo incluía 3.5.8; 3.5.9 contiene parches de septiembre. El nuevo Python incorpora 3.5.9. No todas las rutas afectadas, como QUIC/DTLS, se usan en Croquis3R. [OpenSSL](https://openssl-library.org/news/openssl-3.5-notes/).
- **Gunicorn:** 23.0.0 está fuera del soporte indicado por el mantenedor. La auditoría no le asignó un CVE conocido; se reemplaza para obtener soporte y las correcciones del analizador HTTP. Se comprobó el rechazo de Host/Content-Type duplicados y de Content-Length combinado con Transfer-Encoding. [Política](https://github.com/benoitc/gunicorn/security), [cambios](https://gunicorn.org/news/).
- **PostgreSQL:** 18.6 corrige fallos del servidor, incluidos desbordamientos con posible ejecución de código. Si la etiqueta descargada ya contenía 18.6, no hay cambio de parche del motor; se verifica al desplegar. [Avisos](https://www.postgresql.org/support/security/18/), [notas 18.6](https://www.postgresql.org/docs/release/18.6/).

## Procedencia y reproducción

Gunicorn tiene 26.2.2 en su repositorio oficial, mientras PyPI todavía publica 26.2.0. Se verificó el tag contra el commit `8d98faa9a13d3399a7bea81b5169e5cd72225395`; el archivo oficial queda fijado por URL inmutable y SHA-256 `b42561d72978f30c97b65ea1ba54b0171dfe7f1ef8603b13085647cacec2077d`. Se instaló y ejecutó en Linux. No se usa una rama móvil ni un espejo de terceros.

El Python local portable procede del [manifiesto oficial 3.13.17](https://www.python.org/ftp/python/3.13.17/windows-3.13.17.json): ZIP amd64, SHA-256 `b26ca4b4ee51e157836049934d2b8eabd55939be296f3130254251b6df96ec2f`. El instalador MSI firmado falló al abrir su caché; se usó la distribución completa portable oficial, sin cambiar PATH ni el intérprete de Codex. El entorno anterior se conserva fuera de Git en `.tools/venv-before-security-20261023`, sin uso por la aplicación.

La imagen obtiene actualizaciones Debian durante la construcción y actualiza pip desde la URL y hash publicados por Python. El despliegue utiliza `build --pull` y descarga la imagen PostgreSQL explícita; no confía en una imagen base antigua almacenada en caché.

## Validación

- 120 pruebas Django aprobadas con Python 3.13.17 en Windows y otras 120 con Gunicorn 26.2.2 instalado en un entorno Linux aislado. El anfitrión Linux utiliza Python 3.14.4; no se confunde con la futura imagen 3.12.15 ni se actualizó el Python del anfitrión.
- 27 pruebas de geometría y sintaxis JavaScript aprobadas. Node compartido no forma parte del despliegue.
- Comprobación real de arranque WSGI, health HTTP y rechazo de tres clases de cabeceras ambiguas: aprobada en Linux, por socket privado. SQLite de prueba, sin acceder a registros ni secretos de producción.
- `pip check`, comprobaciones Django y ausencia de nuevas migraciones: aprobados. Los 11 precios del Excel coinciden después del cambio de Python/controlador.
- pip-audit 2.10.1, PyPI para estado previo y OSV para el posterior: **13 nombres/versiones posteriores consultados, cero omitidos, cero avisos conocidos**. Gunicorn 26.2.2 se consulta semánticamente en OSV porque aún no existe su ficha de versión en PyPI. Los informes originales están en `.deploy/security-2026-10-23`, fuera de Git.

No se realizó un pentest ni un escaneo completo de las imágenes, Debian o todas las bibliotecas C embebidas. Un resultado sin avisos conocidos no garantiza ausencia de vulnerabilidades. No se revisaron privilegios o parches del servidor SQL comercial, Docker/Ubuntu ni otras aplicaciones.

## Aplicación en producción pendiente de sudo

El script `scripts/update-server-lan.sh` respalda datos y configuración, registra inventario antes/después, conserva identidades de imágenes para recuperación y ejecuta las pruebas antes de sustituir servicios. Verifica Python y paquetes exactos, actualización menor a PostgreSQL 18.6 y conservación de los registros comerciales. Se detiene ante otra versión mayor, un retroceso, extensiones adicionales o replicación que necesiten revisión. No importa datos locales ni cambia la base comercial.

La construcción Docker y las pruebas PostgreSQL se ejecutarán en ese paso con sudo; todavía no se han completado para esta revisión. La aplicación actual sigue operativa. No se afirma que producción ya esté corregida.

Sigue pendiente HTTPS: el piloto solicitado funciona por HTTP en LAN y tiene cookies Secure desactivadas expresamente. Actualizar dependencias no cifra el acceso del navegador. Para cerrar ese riesgo se necesita configurar HTTPS con un nombre/certificado válido para los equipos del almacén. No se cambió la URL ni el proxy compartido durante esta tarea.
