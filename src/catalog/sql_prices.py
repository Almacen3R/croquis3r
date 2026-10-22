"""Consulta acotada de precios. Solo SELECT; no usa el ORM de la base comercial."""
import re
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .homologation import MAPPINGS


class PriceSourceUnavailable(Exception):
    pass


class SqlPriceProvider:
    def __init__(self, connector=None):
        self.connector = connector

    def fetch(self, skus, *, refresh=False):
        skus = sorted(set(skus))
        allowed = {entry[0] for entry in MAPPINGS.values()}
        if not skus or not set(skus).issubset(allowed):
            raise PriceSourceUnavailable('Consulta de artículos no permitida.')
        schema = settings.THREER_SQL_SCHEMA
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', schema):
            raise PriceSourceUnavailable('Configuración del catálogo no válida.')
        if not settings.THREER_SQL_HOST or not settings.THREER_SQL_PASSWORD:
            raise PriceSourceUnavailable('Conexión de precios pendiente de configurar.')
        key = '3r-prices:' + '|'.join((settings.THREER_SQL_HOST, settings.THREER_SQL_DATABASE,
              schema, settings.THREER_SQL_PRICE_LEVEL, settings.THREER_SQL_CURRENCY, ','.join(skus)))
        if not refresh:
            previous = cache.get(key)
            if previous is not None:
                return previous
        connection = None
        try:
            if self.connector is None:
                import pymssql
                connector = pymssql.connect
            else:
                connector = self.connector
            connection = connector(server=settings.THREER_SQL_HOST, port=str(settings.THREER_SQL_PORT),
                user=settings.THREER_SQL_USER, password=settings.THREER_SQL_PASSWORD,
                database=settings.THREER_SQL_DATABASE, appname='Croquis3R-readonly',
                charset='UTF-8', tds_version='7.4', encryption='require', read_only=True,
                login_timeout=4, timeout=5, autocommit=True)
            with connection.cursor(as_dict=True) as cursor:
                cursor.execute("SELECT IS_SRVROLEMEMBER('sysadmin') AS sysadmin, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','SELECT') AS can_select, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','INSERT') AS can_insert, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','UPDATE') AS can_update, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','DELETE') AS can_delete, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','CONTROL') AS can_control, "
                    "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','ALTER') AS can_alter")
                permissions = cursor.fetchone()
                if (permissions.get('can_select') != 1 or
                        any(permissions.get(k) != 0 for k in ('sysadmin', 'can_insert', 'can_update',
                                                              'can_delete', 'can_control', 'can_alter'))):
                    raise PriceSourceUnavailable('La conexión debe usar una cuenta de solo consulta.')
                cursor.execute(f'SELECT MONEDA_LOCAL AS currency FROM [{schema}].[GLOBALES_AS]')
                if cursor.fetchone().get('currency') != 'CRC':
                    raise PriceSourceUnavailable('La moneda local no corresponde a CRC; revisar la configuración.')
                placeholders = ','.join(['%s'] * len(skus))
                cursor.execute(f"""SELECT a.ARTICULO AS sku, a.DESCRIPCION AS description,
                    a.ACTIVO AS active, a.UNIDAD_VENTA AS sale_unit,
                    p.PRECIO AS price, p.VERSION AS version,
                    p.FECHA_INICIO AS starts_at, p.FECHA_FIN AS ends_at,
                    i.IMPUESTO1 AS tax_rate, i.IMPUESTO2 AS additional_tax
                    FROM [{schema}].[ARTICULO] a
                    LEFT JOIN [{schema}].[ARTICULO_PRECIO] p ON p.ARTICULO=a.ARTICULO
                      AND p.NIVEL_PRECIO=%s AND p.MONEDA=%s
                      AND p.FECHA_INICIO<=GETDATE() AND (p.FECHA_FIN>=GETDATE() OR p.FECHA_FIN IS NULL)
                    LEFT JOIN [{schema}].[IMPUESTO] i ON i.IMPUESTO=a.IMPUESTO
                    WHERE a.ARTICULO IN ({placeholders})""",
                    (settings.THREER_SQL_PRICE_LEVEL, settings.THREER_SQL_CURRENCY, *skus))
                rows = cursor.fetchmany(201)
                if len(rows) > 200:
                    raise PriceSourceUnavailable('Hay demasiadas versiones de precio; revisar el catálogo.')
            fetched = timezone.now().isoformat()
            grouped = {sku: [] for sku in skus}
            for row in rows:
                if row['sku'] in grouped:
                    grouped[row['sku']].append(row)
            result = {}
            for sku, matches in grouped.items():
                if len(matches) != 1:
                    result[sku] = {'status': 'unavailable', 'reason': 'Sin precio vigente único en la lista elegida.'}
                    continue
                row = matches[0]
                if row['active'] != 'S' or row['price'] is None or row['price'] < 0:
                    result[sku] = {'status': 'unavailable', 'reason': 'Artículo inactivo o sin precio de venta vigente.'}
                elif (row['sale_unit'] or '').strip().upper() != 'UND':
                    result[sku] = {'status': 'unavailable', 'reason': 'Unidad comercial distinta de pieza; falta conversión.'}
                elif (row['additional_tax'] != Decimal(0) or row['tax_rate'] is None
                      or not Decimal(0) <= row['tax_rate'] <= Decimal(100)):
                    result[sku] = {'status': 'unavailable', 'reason': 'Tratamiento de impuestos pendiente de revisar.'}
                else:
                    result[sku] = {**row, 'status': 'ready'}
            response = {'articles': result, 'fetched_at': fetched}
            cache.set(key, response, timeout=60)
            return response
        except PriceSourceUnavailable:
            raise
        except Exception:
            # No devolver mensajes del driver, DSN, credenciales ni SQL a la web.
            raise PriceSourceUnavailable('No se pudieron consultar los precios de 3R. Reintenta más tarde.') from None
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
