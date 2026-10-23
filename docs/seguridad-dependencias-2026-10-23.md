# RevisiÃ³n de dependencias â€” 23 de octubre de 2026

## Resultado y alcance

Croquis3R ejecuta Django/Python y Gunicorn, con PostgreSQL para sus datos y pymssql para consultas SELECT a la base comercial. JavaScript se ejecuta en el navegador; Node solo se utiliza aquÃ­ para probar geometrÃ­a. No hay PHP, React, Next.js, servidor Node, paquetes npm ni CDN de bibliotecas en este proyecto. No se modificaron otras aplicaciones del servidor ni el Node compartido de Codex.

Se confirmÃ³ por SSH el commit `5875b8b3f87cff3f57e073966fd286132efd540e` y el contenedor sano `croquis3r-app:git-5875b8b3f87c`. PostgreSQL aparece como `postgres:18-bookworm`. La regla sudo permite listar contenedores, pero no inspeccionarlos ni ejecutar comandos dentro sin autenticaciÃ³n interactiva: **no se comprobÃ³ aÃºn la versiÃ³n exacta de Python/PostgreSQL en esos contenedores**. El lock del commit desplegado identifica las bibliotecas anteriores; no sustituye un inventario del contenedor.

## Inventario y cambios

| Componente | Antes, local / cÃ³digo desplegado | DespuÃ©s, probado o preparado |
|---|---|---|
| Python local | 3.12.14, intÃ©rprete compartido | 3.13.17, `.venv` propio, probado |
| Python Docker | etiqueta flotante `3.12-slim-bookworm`, parche instalado sin verificar | `3.12.15-slim-bookworm`, desplegado y verificado |
| OpenSSL local de Python | 3.5.8 | 3.5.9, verificado |
| pip local | 25.0.1 | 26.2.2, verificado; fijado tambiÃ©n en Docker |
| Django | 5.2.18 | 5.2.18, conservado; mÃ­nimo del manifiesto elevado a 5.2.18 |
| Gunicorn, solo Linux | 23.0.0 | 26.2.2, probado en Linux; WSGI con worker `sync` explÃ­cito |
| asgiref | 3.12.1 | 3.13.0, actualizaciÃ³n de mantenimiento |
| pymssql | 2.4.4 | 2.4.5, actualizaciÃ³n de mantenimiento; 11 cÃ³digos/precios verificados por SELECT |
| psycopg / psycopg-binary | 3.3.6 | 3.3.6, conservados |
| python-dotenv | 1.2.4 | 1.2.4, conservado |
| WhiteNoise | 6.12.0 | 6.12.0, conservado |
| sqlparse | 0.6.0 | 0.6.0, conservado |
| packaging | 26.3 | 26.3, conservado |
| typing_extensions | 4.16.0 | 4.16.0, conservado |
| tzdata | 2026.5 | 2026.5, conservado |
| PostgreSQL Docker | `18-bookworm`, parche sin verificar | `18.6-bookworm`, preparado; misma versiÃ³n mayor |

La libpq incluida en psycopg-binary local informa 18.4: es la biblioteca cliente, **no** la versiÃ³n del servidor PostgreSQL. Los avisos de 18.6 revisados afectan al servidor o a herramientas como psql/pg_dump; no se atribuyen automÃ¡ticamente a libpq. El entorno local usa SQLite. No se afirma que todas las bibliotecas nativas embebidas estÃ©n libres de CVE a partir del anÃ¡lisis de paquetes Python.

## QuÃ© vulnerabilidades aplican

- **PHP y Node:** los avisos oficiales del 21 de octubre son reales, pero no corresponden al servidor de esta aplicaciÃ³n. No se deduce que los demÃ¡s contenedores del equipo estÃ©n cubiertos por esta revisiÃ³n. [PHP](https://www.php.net/archive/2026.php#2026-10-21-5), [Node](https://nodejs.org/en/blog/vulnerability/october-2026-security-releases).
- **Django:** 5.2.18 ya contiene las correcciones de octubre, entre ellas CVE-2026-77050 y CVE-2026-84429. Se conserva la serie 5.2 LTS; cambiar de versiÃ³n mayor no es necesario para esos parches. [Aviso oficial](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/).
- **Python:** 3.12.14 era anterior a 3.12.15, que corrige problemas de SSL, extracciÃ³n de archivos y agotamiento de memoria. La aplicaciÃ³n no implementa importaciÃ³n de archivos comprimidos ni un servidor TLS Python; presencia de una versiÃ³n afectada no demuestra explotaciÃ³n remota del croquis. [Python 3.12.15](https://www.python.org/downloads/release/python-31215/).
- **pip:** el anÃ¡lisis inicial devolviÃ³ 12 entradas en pip 25.0.1, correspondientes a seis identificadores Ãºnicos: CVE-2025-8869, CVE-2026-1703, CVE-2026-3219, CVE-2026-6357, CVE-2026-8643 y CVE-2026-13346. Son rutas de instalaciÃ³n/descarga, no endpoints del croquis. La primera tiene mitigaciÃ³n por PEP 706 en Python 3.12; no se presenta como seis ataques remotos explotables. Se actualizÃ³ a 26.2.2, que tambiÃ©n renueva certifi ante el incidente de autoridades certificadoras. [pip](https://pip.pypa.io/en/stable/news/), [Python](https://blog.python.org/2026/10/python-3151-3149-31317/).
- **OpenSSL:** el intÃ©rprete local antiguo incluÃ­a 3.5.8; 3.5.9 contiene parches de septiembre. El nuevo Python incorpora 3.5.9. No todas las rutas afectadas, como QUIC/DTLS, se usan en Croquis3R. [OpenSSL](https://openssl-library.org/news/openssl-3.5-notes/).
- **Gunicorn:** 23.0.0 estÃ¡ fuera del soporte indicado por el mantenedor. La auditorÃ­a no le asignÃ³ un CVE conocido; se reemplaza para obtener soporte y las correcciones del analizador HTTP. Se comprobÃ³ el rechazo de Host/Content-Type duplicados y de Content-Length combinado con Transfer-Encoding. [PolÃ­tica](https://github.com/benoitc/gunicorn/security), [cambios](https://gunicorn.org/news/).
- **PostgreSQL:** 18.6 corrige fallos del servidor, incluidos desbordamientos con posible ejecuciÃ³n de cÃ³digo. Si la etiqueta descargada ya contenÃ­a 18.6, no hay cambio de parche del motor; se verifica al desplegar. [Avisos](https://www.postgresql.org/support/security/18/), [notas 18.6](https://www.postgresql.org/docs/release/18.6/).

## Procedencia y reproducciÃ³n

Gunicorn tiene 26.2.2 en su repositorio oficial, mientras PyPI todavÃ­a publica 26.2.0. Se verificÃ³ el tag contra el commit `8d98faa9a13d3399a7bea81b5169e5cd72225395`; el archivo oficial queda fijado por URL inmutable y SHA-256 `b42561d72978f30c97b65ea1ba54b0171dfe7f1ef8603b13085647cacec2077d`. Se instalÃ³ y ejecutÃ³ en Linux. No se usa una rama mÃ³vil ni un espejo de terceros.

El Python local portable procede del [manifiesto oficial 3.13.17](https://www.python.org/ftp/python/3.13.17/windows-3.13.17.json): ZIP amd64, SHA-256 `b26ca4b4ee51e157836049934d2b8eabd55939be296f3130254251b6df96ec2f`. El instalador MSI firmado fallÃ³ al abrir su cachÃ©; se usÃ³ la distribuciÃ³n completa portable oficial, sin cambiar PATH ni el intÃ©rprete de Codex. El entorno anterior se conserva fuera de Git en `.tools/venv-before-security-20261023`, sin uso por la aplicaciÃ³n.

La imagen obtiene actualizaciones Debian durante la construcciÃ³n y actualiza pip desde la URL y hash publicados por Python. El despliegue utiliza `build --pull` y descarga la imagen PostgreSQL explÃ­cita; no confÃ­a en una imagen base antigua almacenada en cachÃ©.

## ValidaciÃ³n

- 120 pruebas Django aprobadas con Python 3.13.17 en Windows y otras 120 con Gunicorn 26.2.2 instalado en un entorno Linux aislado. El anfitriÃ³n Linux utiliza Python 3.14.4; no se confunde con la futura imagen 3.12.15 ni se actualizÃ³ el Python del anfitriÃ³n.
- 27 pruebas de geometrÃ­a y sintaxis JavaScript aprobadas. Node compartido no forma parte del despliegue.
- ComprobaciÃ³n real de arranque WSGI, health HTTP y rechazo de tres clases de cabeceras ambiguas: aprobada en Linux, por socket privado. SQLite de prueba, sin acceder a registros ni secretos de producciÃ³n.
- `pip check`, comprobaciones Django y ausencia de nuevas migraciones: aprobados. Los 11 precios del Excel coinciden despuÃ©s del cambio de Python/controlador.
- pip-audit 2.10.1, PyPI para estado previo y OSV para el posterior: **13 nombres/versiones posteriores consultados, cero omitidos, cero avisos conocidos**. Gunicorn 26.2.2 se consulta semÃ¡nticamente en OSV porque aÃºn no existe su ficha de versiÃ³n en PyPI. Los informes originales estÃ¡n en `.deploy/security-2026-10-23`, fuera de Git.

No se realizÃ³ un pentest ni un escaneo completo de las imÃ¡genes, Debian o todas las bibliotecas C embebidas. Un resultado sin avisos conocidos no garantiza ausencia de vulnerabilidades. No se revisaron privilegios o parches del servidor SQL comercial, Docker/Ubuntu ni otras aplicaciones.

## AplicaciÃ³n en producciÃ³n completada

El script `scripts/update-server-lan.sh` respalda datos y configuraciÃ³n, registra inventario antes/despuÃ©s, conserva identidades de imÃ¡genes para recuperaciÃ³n y ejecuta las pruebas antes de sustituir servicios. Verifica Python y paquetes exactos, actualizaciÃ³n menor a PostgreSQL 18.6 y conservaciÃ³n de los registros comerciales. Se detiene ante otra versiÃ³n mayor, un retroceso, extensiones adicionales o replicaciÃ³n que necesiten revisiÃ³n. No importa datos locales ni cambia la base comercial.

El administrador instalÃ³ la autorizaciÃ³n limitada y el agente ejecutÃ³ la unidad aprobada. La construcciÃ³n Docker, verificaciÃ³n del runtime exacto y 120 pruebas sobre PostgreSQL aprobaron. El despliegue `897308d80fbf` finalizÃ³ el 23-10-2026 a las 11:50:44 de Costa Rica. AplicaciÃ³n y PostgreSQL 18.6 quedaron saludables; editor, calculador, atenciones, distribuciÃ³n y cierre de sesiÃ³n aprobaron comprobaciones autenticadas. Las 11 consultas comerciales funcionaron y se comprobÃ³ que los registros de negocio conservaron cantidades y hash. No hubo migraciones pendientes. [EjecuciÃ³n y respaldo](actualizacion-autorizada-2026-10-23.md).

La comprobaciÃ³n `config.security_inventory --verify` aprobÃ³ dentro de la imagen nueva y del contenedor en ejecuciÃ³n, por lo que se confirmÃ³ Python 3.12.15, Django 5.2.18, Gunicorn 26.2.2, pip 26.2.2, asgiref 3.13.0 y pymssql 2.4.5. El inventario completo, incluida la versiÃ³n exacta de OpenSSL de producciÃ³n, quedÃ³ en los archivos privados `runtime-new.json` y `runtime-after.json` del respaldo. El permiso del agente permite consultar estado/registros, no leer esos archivos privados; por tanto no se atribuye a OpenSSL del contenedor la versiÃ³n 3.5.9 comprobada solo en Windows.

Sigue pendiente HTTPS: el piloto solicitado funciona por HTTP en LAN y tiene cookies Secure desactivadas expresamente. Actualizar dependencias no cifra el acceso del navegador. Para cerrar ese riesgo se necesita configurar HTTPS con un nombre/certificado vÃ¡lido para los equipos del almacÃ©n. No se cambiÃ³ la URL ni el proxy compartido durante esta tarea.
