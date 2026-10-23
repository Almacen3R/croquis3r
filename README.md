# Croquis3R

Prototipo web para dibujar croquis de casas, vincular objetos con artículos de ferretería y obtener una estimación de materiales. Surge del flujo de atención de clientes de la alianza con TicoBlock.

**Estado: 22 de octubre de 2026.** Prototipo con recetas TicoBlock documentadas, servidor LAN con PostgreSQL y consulta de precios comerciales homologados probada en local, pendiente de aplicar al servidor. Las revisiones locales pendientes de aplicar están en [pendientes](docs/pendientes-ticoblock.md). No sustituye la revisión profesional de la construcción.

## Qué se puede probar

- Dibujar paredes horizontales y verticales con dos clics, ajuste a 0,50 m y a extremos cercanos.
- Arrastrar cualquiera de los puntos de una pared seleccionada para cambiar su largo y dirección, incluyendo inclinaciones. El otro extremo permanece fijo y las aberturas siguen vinculadas. No permite acortar por debajo de 10 cm ni dejar aberturas fuera de la pared.
- Ver cotas en metros; los tramos contiguos sobre la misma línea comparten una cota total.
- Seleccionar, arrastrar, duplicar y borrar paredes. La duplicación conserva sus aberturas y artículos.
- Editar coordenadas, altura y espesor con medidas exactas.
- Colocar puertas y ventanas sobre paredes y editar su posición, ancho, altura y altura sobre el piso.
- Vincular varios artículos a un objeto: cantidad por m² neto, metro lineal o cantidad fija por objeto, con desperdicio configurable.
- Calcular en el servidor, descontando aberturas del área de pared, con desglose y descarga CSV.
- Guardar croquis, guardar copias, crear plantillas de croquis y de paredes; deshacer y rehacer durante la sesión.

En esta versión, «unir» significa alinear extremos y presentar una cota continua. Los segmentos conservan sus artículos y su identidad; no se fusionan destructivamente. Cada pared conserva su espesor para la representación, pero este no modifica la fórmula de área. Los cruces y esquinas no tienen una corrección técnica de volumen o aparejo.

## Inicio rápido en Windows (sin Docker)

Requiere Python 3.12.15 o 3.13.17 (parches verificados el 23-10-2026). PowerShell, desde esta carpeta:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
.venv\Scripts\python.exe manage.py migrate
.venv\Scripts\python.exe manage.py seed_demo
.venv\Scripts\python.exe manage.py createsuperuser
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8013
```

Abrir <http://127.0.0.1:8013/> e iniciar sesión. Toda cuenta debe ser individual; vendedores activos ven sus registros y superusuarios ven todos. Las referencias originales de TicoBlock son comunes. Ver [usuarios y privacidad](docs/usuarios-y-privacidad.md). SQLite se utiliza solo para facilitar esta prueba local; los croquis guardados quedan en `db.sqlite3`. No hace falta copiar `.env.example` para este modo. Si existe `.env`, debe tener `DB_ENGINE=sqlite`.

En esta estación, `.venv` usa Python 3.13.17, preparado desde la distribución portable oficial con SHA-256 verificado en `.tools/python31317/python.exe`. No depende del intérprete compartido de Codex. La imagen de producción usa Python 3.12.15 para conservar la serie existente. Ver [revisión de seguridad y pendientes de producción](docs/seguridad-dependencias-2026-10-23.md).

## Ejecución local en Docker + PostgreSQL 18

```powershell
Copy-Item .env.example .env
# Editar .env: POSTGRES_PASSWORD con un valor local propio.
docker compose config --quiet
docker compose build
docker compose up -d db
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py seed_demo
docker compose up -d app
```

Abrir <http://127.0.0.1:8013/>. Compose fuerza PostgreSQL para el contenedor de aplicación aunque `.env` diga `DB_ENGINE=sqlite`. La base no publica puertos. Los datos locales permanecen en el volumen `croquis3r_postgres_data`, montado en `/var/lib/postgresql` según el formato de PostgreSQL 18.

Para la administración del catálogo de ejemplo:

```powershell
docker compose exec app python manage.py createsuperuser
```

En ejecución directa, usar `.venv\Scripts\python.exe manage.py createsuperuser`. Abrir `/admin/`.

## Probar el flujo

1. Se abre una casa de ejemplo con cinco paredes, una puerta y una ventana, sin guardar automáticamente.
2. Seleccionar una pared; editar medidas o vincular un artículo usando base, factor y desperdicio.
3. En «Materiales», revisar cantidades, avisos y desglose. Un objeto sin artículos muestra una advertencia.
4. Dibujar con «Pared»: clic en el inicio y clic en el final. `Esc` cancela. `V` selecciona, `P` dibuja.
5. Elegir «Puerta» o «Ventana» y hacer clic en el espacio deseado sobre una pared.
6. Guardar el croquis. En biblioteca, abrirlo para recuperar sus objetos y reglas.
7. Guardarlo como plantilla: al abrir una plantilla, se trabaja en una copia nueva.

Si una operación de dibujo o arrastre deja geometría inválida, se muestra el error y se bloquea el cálculo y el guardado. Se puede corregir con coordenadas o deshacer. El servidor rechaza paredes colineales superpuestas, aberturas fuera de su pared y aberturas que se solapan en altura y longitud.

## Estructura

```text
manage.py                        # entrada Django, incorpora src/ a PYTHONPATH
src/config/                      # configuración, rutas, WSGI/ASGI
src/catalog/                     # artículos ficticios y proveedor de consulta
src/sketches/                    # documentos, plantillas, API y cálculo
src/*/migrations/                # migraciones versionadas por aplicación Django
src/templates/sketches/          # editor web
src/static/croquis/              # editor SVG, estilos y geometría
tests/geometry.test.mjs          # pruebas de cotas, ajuste y duplicación
docs/                            # decisiones y operación
scripts/verify.sh                # verificación en contenedores
Dockerfile / compose*.yaml       # aplicación y PostgreSQL aislados
requirements.txt                # rangos para futuras actualizaciones deliberadas
requirements.lock               # versiones verificadas para instalación
```

## Verificación

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe manage.py test sketches catalog
node --test tests/geometry.test.mjs
node --check src/static/croquis/editor.js
```

Las pruebas cubren descuentos de aberturas, desperdicio, redondeo, geometría inválida, CSRF, acceso, guardado y conflictos de revisiones. El frontend requiere un navegador moderno; Node solo es necesario para sus pruebas.

## Próximas etapas

La entrada recomendada para vendedores es `/atenciones/`, con búsqueda, guardado de cálculos/listas por cliente y acceso a croquis. Ya está disponible el [calculador manual de casas](docs/calculador-manual-casas.md) en `/calculador-casas/`, con las recetas del modulador, las aclaraciones del 21-10-2026 y desglose por paño, además de siete plantillas de listas de materiales. El editor usa estas recetas mediante una propuesta de división geométrica; las columnas se dibujan en el croquis o se ingresan por cantidades y las medidas sin receta dejan el cálculo pendiente. La vinculación de los códigos de los mismos productos en 3R y las reglas pendientes se documentan en la [investigación de TicoBlock](docs/investigacion-ticoblock-2026-10-20.md).

Validar el prototipo con el equipo y un expediente completo de TicoBlock. Acordar fórmulas, tipos de pared, unidades comerciales y reglas de redondeo. Después se implementará la consulta de solo lectura al catálogo real mediante `catalog/providers.py`, manteniendo la base de Croquis3R independiente.

La IA para interpretar croquis a mano, la generación de planos constructivos, precios, existencias y cotizaciones no forman parte de este primer prototipo.

El despliegue, Git remoto y los respaldos quedan pendientes. Por indicación del responsable, el futuro respaldo en Drive de este proyecto no requerirá cifrado adicional del archivo. No se configuró todavía ninguna tarea, destino ni credencial de respaldo.

Consultar [arquitectura](docs/architecture.md), [operación](docs/operations.md), [verificaciones realizadas](docs/verification.md) y [alcance pendiente de recuperación](docs/disaster-recovery.md).


## Actualización de reglas — 21 de octubre de 2026

Estado y datos pendientes: [registro vigente de Croquis3R](docs/pendientes-ticoblock.md). El servidor LAN ya funciona con PostgreSQL 18; el desarrollo local usa SQLite. Las revisiones locales aún no desplegadas se identifican en ese registro.

Asistente por metros en el cálculo manual; preferencias de 2, 1,50, 1 y 0,50 m. Familias de 12 y 10 cm con las mismas cantidades de bloques, restricciones de altura y segundo piso, y puertas de módulos 1,50, 2 y 3 m. Las promociones conservan 10 cm. Ver [reglas confirmadas](docs/aclaraciones-ticoblock-2026-10-21.md). Esta revisión se verificó en local; no se desplegó sobre la instalación LAN existente.


## Repositorio y actualización del servidor

Repositorio oficial: https://github.com/Almacen3R/croquis3r · rama `main`. La instalación LAN existente se actualiza mediante [Git y actualización](docs/git-y-actualizacion.md), con respaldo previo y sin volver a importar datos locales. Los scripts de primera instalación no deben repetirse sobre el proyecto existente.

## Usuarios y precios

- [Cuentas, propiedad de registros, cierre de sesión y migración](docs/usuarios-y-privacidad.md).
- [Artículos y variantes pendientes de vincular a precios de 3R](docs/articulos-para-precios.md).

- [Homologación y consulta de precios 3R](docs/homologacion-precios-3r-2026-10-22.md): configuración externa de solo lectura, lista GENERAL/CRC e IVA incluido.
