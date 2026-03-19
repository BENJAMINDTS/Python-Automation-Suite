"""
Módulo de importación masiva de Productos y Listas de Precios (Tarifas).
Implementa un sistema de 'Turbo Caché' para precargar modelos en memoria (RAM)
y evitar bloqueos o timeouts del servidor por exceso de peticiones XML-RPC.

@author BenjaminDTS
"""

import csv
import xmlrpc.client
import json
import os
import sys
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Logger estructurado
logger.remove()
os.makedirs("logs", exist_ok=True)
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    level="DEBUG",
    colorize=True,
)
logger.add(
    "logs/tarifas_{time:YYYY-MM-DD}.log",
    format="{time} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    serialize=True,
)

# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
# Valores leídos desde variables de entorno para evitar exposición de secretos
# en el control de versiones. Ver .env.example para referencia.
URL      = os.environ.get("ODOO_URL", "https://tu-dominio-odoo.com")
DB       = os.environ.get("ODOO_DB", "nombre_base_datos")
USERNAME = os.environ.get("ODOO_USERNAME", "tu_usuario@email.com")
PASSWORD = os.environ.get("ODOO_PASSWORD", "tu_contraseña_segura")
ARCHIVO_TARIFAS = os.environ.get("ARCHIVO_TARIFAS", "tarifas_ejemplo.csv")

# Columnas configurables desde entorno; por defecto las 6 tarifas estándar
_columnas_env = os.environ.get("COLUMNAS_TARIFAS", "")
COLUMNAS_TARIFAS: list[str] = (
    [c.strip() for c in _columnas_env.split(",") if c.strip()]
    if _columnas_env
    else [
        "Tarifa PVP 2", "Tarifa PVP", "Tarifa PVP sin Iva",
        "Nuevos cliente", "Tarifa 15", "Cliente fidelizado",
    ]
)


def get_odoo_proxy(endpoint: str) -> xmlrpc.client.ServerProxy:
    """
    Genera el proxy de conexión XML-RPC.
    Se encapsula para centralizar la instanciación de los clientes y evitar redundancias.

    Args:
        endpoint: Nombre del endpoint XML-RPC de Odoo ('common' u 'object').

    Returns:
        Instancia de ServerProxy apuntando al endpoint indicado.
    """
    return xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/{endpoint}')


def pre_cargar_productos(uid: int, models) -> dict[str, int]:
    """
    Carga en memoria el mapeo de default_code -> id en una sola petición (Eager Loading).
    Previene consultas N+1 durante la iteración del CSV.

    Args:
        uid: ID de usuario autenticado en Odoo.
        models: Proxy XML-RPC del endpoint 'object'.

    Returns:
        Diccionario {default_code: product_template_id}.
    """
    prods = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read',
                              [[]], {'fields': ['id', 'default_code']})
    resultado = {p['default_code']: p['id'] for p in prods if p.get('default_code')}
    logger.info("Productos cargados en caché.", total=len(resultado))
    return resultado


def pre_cargar_reglas(uid: int, models, cache_tarifas: dict[str, int]) -> dict[tuple[int, int], int]:
    """
    Obtiene las reglas de precios existentes de las tarifas objetivo (Eager Loading).
    Evita consultar la base de datos por cada celda de precio procesada.

    Args:
        uid: ID de usuario autenticado en Odoo.
        models: Proxy XML-RPC del endpoint 'object'.
        cache_tarifas: Diccionario {nombre_tarifa: pricelist_id}.

    Returns:
        Diccionario {(pricelist_id, product_tmpl_id): pricelist_item_id}.
    """
    tarifas_ids = list(cache_tarifas.values())
    domain = [('pricelist_id', 'in', tarifas_ids)]
    reglas = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'search_read',
                               [domain], {'fields': ['id', 'pricelist_id', 'product_tmpl_id']})
    cache = {}
    for r in reglas:
        p_id = r['pricelist_id'][0] if isinstance(r['pricelist_id'], list) else r['pricelist_id']
        t_id = r['product_tmpl_id'][0] if isinstance(r['product_tmpl_id'], list) else r['product_tmpl_id']
        cache[(p_id, t_id)] = r['id']
    logger.info("Reglas de precio cargadas en caché.", total=len(cache))
    return cache


def limpiar_precio(valor) -> float:
    """
    Sanitiza strings de precios convirtiendo comas en puntos.
    Asegura que Odoo reciba un float numérico válido para evitar excepciones de tipo.

    Args:
        valor: Valor de precio en crudo proveniente del CSV (str, int o float).

    Returns:
        Precio como float. Devuelve 0.0 si el valor es inválido o vacío.
    """
    try:
        if not valor: return 0.0
        return float(str(valor).replace(',', '.').strip())
    except (ValueError, TypeError):
        return 0.0


def procesar_producto(codigo: str, nombre: str, fila: dict, uid: int, models, cache: dict) -> int:
    """
    Asegura la existencia del producto en Odoo y lo añade a la caché si es nuevo.
    Aísla la responsabilidad de creación de producto (Single Responsibility).

    Args:
        codigo: Código interno del producto (default_code).
        nombre: Nombre descriptivo del producto.
        fila: Fila del CSV como diccionario {columna: valor}.
        uid: ID de usuario autenticado en Odoo.
        models: Proxy XML-RPC del endpoint 'object'.
        cache: Diccionario de caché compartido con claves 'productos', 'tarifas' y 'reglas'.

    Returns:
        ID del product.template en Odoo.
    """
    if codigo not in cache['productos']:
        precio_base = limpiar_precio(fila.get('Tarifa PVP', 0))
        prod_id = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'create', [{
            'name': nombre,
            'default_code': codigo,
            'type': 'product',
            'list_price': precio_base
        }])
        cache['productos'][codigo] = prod_id
        logger.info("Producto creado en Odoo.", codigo=codigo, id=prod_id)
    return cache['productos'][codigo]


def procesar_reglas_tarifa(prod_id: int, fila: dict, uid: int, models, cache: dict) -> None:
    """
    Itera sobre las columnas configuradas y actualiza o crea las reglas de precio.
    Aísla la lógica de actualización de tarifas manteniendo la función bajo 30 líneas.

    Args:
        prod_id: ID del product.template en Odoo.
        fila: Fila del CSV como diccionario {columna: valor}.
        uid: ID de usuario autenticado en Odoo.
        models: Proxy XML-RPC del endpoint 'object'.
        cache: Diccionario de caché compartido con claves 'productos', 'tarifas' y 'reglas'.

    Returns:
        None
    """
    for tarifa_nombre in COLUMNAS_TARIFAS:
        try:
            precio_final = limpiar_precio(fila.get(tarifa_nombre, 0))
            if precio_final <= 0: continue

            tarifa_id = cache['tarifas'][tarifa_nombre]
            clave_regla = (tarifa_id, prod_id)

            if clave_regla in cache['reglas']:
                models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'write',
                                  [[cache['reglas'][clave_regla]], {'fixed_price': precio_final}])
            else:
                new_id = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'create', [{
                    'pricelist_id': tarifa_id,
                    'product_tmpl_id': prod_id,
                    'applied_on': '1_product',
                    'compute_price': 'fixed',
                    'fixed_price': precio_final
                }])
                cache['reglas'][clave_regla] = new_id
        except Exception as exc:
            logger.warning("Error procesando regla de tarifa.", tarifa=tarifa_nombre, prod_id=prod_id)


def inicializar_cache(uid: int, models) -> dict:
    """
    Orquesta la carga inicial de datos en RAM para acelerar el procesamiento masivo.

    Args:
        uid: ID de usuario autenticado en Odoo.
        models: Proxy XML-RPC del endpoint 'object'.

    Returns:
        Diccionario de caché con claves 'productos', 'tarifas' y 'reglas'.
    """
    logger.info("Inicializando caché de tarifas.")
    cache = {'productos': pre_cargar_productos(uid, models), 'tarifas': {}}

    for n in COLUMNAS_TARIFAS:
        tarifa = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'search', [[('name', '=', n)]])
        cache['tarifas'][n] = tarifa[0] if tarifa else models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'create', [{'name': n}])
        logger.debug("Tarifa procesada.", nombre=n)

    cache['reglas'] = pre_cargar_reglas(uid, models, cache['tarifas'])
    return cache


def ejecutar_importacion() -> str:
    """
    Punto de entrada principal. Coordina autenticación, lectura y procesamiento.
    Devuelve formato JSON estándar con el resultado del proceso para integraciones REST.

    Returns:
        JSON string con estructura { success, data, message }.
    """
    if not all([DB, USERNAME, PASSWORD]):
        logger.critical("Variables de entorno de Odoo incompletas. Revisa el archivo .env.")
        return json.dumps({"success": False, "data": None, "message": "Variables de entorno incompletas."})

    try:
        common = get_odoo_proxy('common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if not uid:
            return json.dumps({"success": False, "data": None, "message": "Autenticación fallida."})

        logger.info("Autenticado en Odoo.", uid=uid)
        models = get_odoo_proxy('object')
        cache = inicializar_cache(uid, models)

        with open(ARCHIVO_TARIFAS, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=',')
            reader.fieldnames = [c.strip() for c in reader.fieldnames if c]

            for fila in reader:
                codigo = fila.get('Artículo', '').strip()
                nombre = fila.get('Nombre artículo', '').strip()
                if not codigo or not nombre: continue

                prod_id = procesar_producto(codigo, nombre, fila, uid, models, cache)
                procesar_reglas_tarifa(prod_id, fila, uid, models, cache)

        logger.info("Importación completada.")
        return json.dumps({"success": True, "data": None, "message": "Importación procesada con éxito."})

    except Exception as e:
        logger.critical("Error crítico en importación.", error=str(e))
        return json.dumps({"success": False, "data": None, "message": f"Error crítico en ejecución: {str(e)}"})


if __name__ == "__main__":
    resultado = ejecutar_importacion()
    print(resultado)
