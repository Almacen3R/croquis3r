# Arquitectura de Croquis3R

## Decisiones iniciales — 2026-10-19

- Django 5.2 LTS y Python 3.12 para alinearse con las aplicaciones de la empresa. [Compatibilidad oficial de Django](https://docs.djangoproject.com/en/5.2/releases/5.2/).
- PostgreSQL 18 exclusivo del proyecto, como exige `GUIA_ARQUITECTURA_APLICACIONES.md`. SQLite es una alternativa exclusivamente local para revisar el prototipo sin Docker.
- Django templates + SVG + JavaScript modular, sin compilador ni dependencias de frontend. Permite empezar por las medidas y reglas del negocio; no obliga a incorporar una biblioteca CAD antes de validarlas.
- Identificador técnico: `croquis3r`; nombre visible: **Croquis3R**. TicoBlock describe la alianza y el sistema constructivo de referencia.
- Contenedores separados `app` y `db`. El editor y la API se sirven desde el mismo origen, con protección CSRF.

## Límites de módulos

`catalog` mantiene artículos de ejemplo. `get_catalog_provider()` entrega un proveedor con el contrato `articles()`. La futura conexión real se implementará aquí mediante consultas de solo lectura y mapeo a una identidad local estable; no debe crear tablas de Croquis3R en la base comercial ni escribir en ella. No se solicitan credenciales reales en esta etapa.

`sketches` guarda croquis y plantillas como documentos JSON versionados. El servidor valida todos los objetos antes de guardar. Una revisión numérica permite rechazar actualizaciones obsoletas con HTTP 409. Los usuarios del equipo comparten los croquis; aún no hay segregación por cliente o vendedor.

`sketches/domain.py` valida y calcula con `Decimal`. No consume IA ni toma cantidades calculadas por el navegador. Cada asignación guarda artículo, base de cálculo, factor y desperdicio dentro del documento, por lo que cambiar los valores de la interfaz no altera otros croquis guardados. Los nombres de artículos se consultan del catálogo actual; no existe todavía un historial inmutable de estimaciones ni versiones de catálogo.

## Geometría v1

Coordenadas sobre el eje de pared, en metros. Paredes definidas por dos extremos, altura y espesor. El trazo inicial es ortogonal; arrastrar cualquiera de sus extremos permite cambiar largo y ángulo libremente. La longitud se calcula como la distancia euclídea entre extremos, también en el servidor. Puertas y ventanas se anclan a una pared mediante `wall_id`; `offset` mide desde el primer extremo, incluso si el trazo va de derecha a izquierda. `sill` es la altura sobre el piso.

Los extremos pueden coincidir; las cotas agrupan tramos colineales contiguos. Los objetos siguen separados para preservar reglas y facilitar edición. Los cruces perpendiculares son válidos, pero el prototipo no descuenta intersecciones ni resuelve aparejo, refuerzo, dinteles, columnas, instalaciones, techo o normativa. Mover una pared mueve sus aberturas; otras paredes no se arrastran automáticamente.

Límite actual: 300 objetos por croquis, 20 asignaciones por objeto, coordenadas entre −100 y 100 m. Plantillas de objeto: paredes completas sin sus aberturas; plantillas de croquis: todos los objetos. La duplicación de paredes sí incluye sus aberturas.

## Regla de ejemplo

```text
área neta pared = longitud × altura − suma(ancho × alto de sus aberturas)
cantidad objeto/artículo = techo(base × factor × (1 + desperdicio / 100))
total artículo = suma de cantidades redondeadas de cada objeto
```

Para aberturas, la base de área es ancho × alto y la lineal es ancho. Para base fija, la base es 1. Las aberturas solo se descuentan de la regla de área de una pared. Todas las cantidades se redondean hacia arriba a unidades enteras; unidades fraccionarias, empaques y redondeo global necesitan una decisión posterior del negocio.

La semilla contiene cuatro artículos ficticios. El ejemplo de pared usa 12,5 blocks/m² y 5 % adicional **solo como supuesto de prueba**; no se afirma que corresponda al sistema de casas de TicoBlock.

## API inicial

| Ruta | Métodos | Función |
|---|---|---|
| `/health/` | GET | Salud de aplicación y conexión a base |
| `/api/catalog/` | GET | Artículos activos |
| `/api/estimate/` | POST | Validar y calcular un documento |
| `/api/sketches/` | GET, POST | Listar y crear croquis/plantillas |
| `/api/sketches/<id>/` | GET, PUT | Leer y actualizar con revisión |
| `/api/object-templates/` | GET, POST | Plantillas de pared |

En desarrollo local (`DEBUG=1`) se permite acceso anónimo para probar. Fuera de desarrollo, las rutas del editor y la API requieren una cuenta activa con `is_staff`. Esto es acceso inicial de equipo; los permisos granulares quedan pendientes antes de ampliar el piloto. Django Admin administra las cuentas y el catálogo.

## Infraestructura prevista

Repositorio: `/opt/apps/croquis3r`. Datos en servidor: `/data/projects/croquis3r/postgres`, montados en `/var/lib/postgresql` para PostgreSQL 18 ([ruta oficial](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)). Red privada de base separada. Producción agrega la red externa del proxy con alias `croquis3r`, sin publicar HTTP ni PostgreSQL directamente.

Estado del 21-10-2026: la instalación LAN funciona en `http://192.168.0.214:8013/` con PostgreSQL 18 y contenedores exclusivos. El código está en https://github.com/Almacen3R/croquis3r, rama `main`. Las revisiones pendientes de aplicar se describen en `docs/pendientes-ticoblock.md`; el procedimiento de actualización preserva los datos existentes. Dominio/TLS y respaldos externos siguen pendientes. Los documentos privados de conexión e inventario del servidor se conservan en la estación local, fuera de Git.
