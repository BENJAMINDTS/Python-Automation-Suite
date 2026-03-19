"""
Script de importación masiva a Odoo con sistema de reanudación inteligente.
Lee el catálogo CSV, gestiona las familias, ignora artículos dados de baja
y comprueba la existencia de productos previos para evitar duplicados o
reinicios desde cero en caso de fallo de red.

@author BenjaminDTS
"""

import os
import csv
import base64
import xmlrpc.client
import sys
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# Logger estructurado — se elimina el handler por defecto y se reemplazan
# con uno coloreado para consola y otro persistente en JSON para fichero.
logger.remove()
os.makedirs("logs", exist_ok=True)
logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    level="DEBUG",
    colorize=True,
)
logger.add(
    "logs/subida_productos_{time:YYYY-MM-DD}.log",
    format="{time} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    serialize=True,
)

# Configuración desde variables de entorno — las credenciales ya no están
# en el código fuente para evitar su exposición accidental en el repositorio.
URL            = os.environ.get("ODOO_URL", "")
DB             = os.environ.get("ODOO_DB", "")
USERNAME       = os.environ.get("ODOO_USERNAME", "")
PASSWORD       = os.environ.get("ODOO_PASSWORD", "")
CARPETA_FOTOS  = os.environ.get("CARPETA_FOTOS", "./fotos")
ARCHIVO_CSV    = os.environ.get("ARCHIVO_CSV", "catalogo.csv")
LIMPIAR_CATALOGO = os.environ.get("LIMPIAR_CATALOGO", "False").upper() == "TRUE"


# ==========================================
# 1. ORQUESTACIÓN PRINCIPAL (Alto Nivel)
# ==========================================

def subir_catalogo() -> None:
    """
    Orquestador principal: valida la configuración, conecta, ejecuta limpieza
    si procede y lanza la importación.
    """
    # Fallo rápido si las variables de entorno obligatorias están ausentes,
    # evitando errores crípticos de red más adelante.
    if not all([URL, DB, USERNAME, PASSWORD]):
        logger.critical("Variables de entorno de Odoo incompletas. Revisa el archivo .env.")
        sys.exit(1)

    uid = conectar_odoo()
    if not uid:
        return

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    limpieza_inicial(uid, models)
    iniciar_importacion(uid, models)


def limpieza_inicial(uid: int, models) -> None:
    """
    Gestiona la ejecución de la limpieza inicial del catálogo si está habilitada.

    :param uid: ID del usuario autenticado.
    :param models: Objeto de conexión a modelos.
    """
    if LIMPIAR_CATALOGO:
        vaciar_productos_odoo(uid, models)
    else:
        logger.info("Modo seguro activo: catálogo previo no se vaciará.")


def iniciar_importacion(uid: int, models) -> None:
    """
    Bucle principal de lectura e inserción con escudos de seguridad (bajas y duplicados).

    :param uid: ID del usuario autenticado.
    :param models: Objeto de conexión a modelos de Odoo.
    """
    logger.info("Iniciando importación o reanudación.")
    try:
        with open(ARCHIVO_CSV, mode='r', encoding='utf-8-sig') as f:
            reader, cabeceras = preparar_normalizar_csv(f)
            col_codigo, col_nombre, col_familia, col_baja = preparar_cabeceras(cabeceras)

            for fila in reader:
                codigo, nombre, nombre_familia, estado_baja = leer_csv(
                    col_codigo, col_nombre, col_familia, col_baja, fila
                )

                if not codigo or not nombre:
                    continue

                # --- ESCUDO 1: PRODUCTOS DESCATALOGADOS ---
                if estado_baja == 'TRUE':
                    logger.debug("Producto dado de baja omitido.", codigo=codigo)
                    continue

                # --- ESCUDO 2: REANUDACIÓN AUTOMÁTICA ---
                try:
                    producto_existente = models.execute_kw(
                        DB, uid, PASSWORD, 'product.template', 'search',
                        [[('default_code', '=', codigo)]]
                    )
                    if producto_existente:
                        logger.debug("Producto ya existe en Odoo, omitido.", codigo=codigo)
                        continue
                except Exception as e:
                    logger.warning("Error comprobando existencia.", codigo=codigo, error=str(e))
                    continue

                id_categoria = obtener_o_crear_categoria(uid, models, nombre_familia)
                foto_64 = preparar_foto(codigo)
                datos_producto = estructura(codigo, nombre, id_categoria, foto_64)

                insertar(uid, models, codigo, nombre, datos_producto)

    except Exception as e:
        logger.critical("Error crítico leyendo el archivo CSV.", error=str(e))


# ==========================================
# 2. FUNCIONES DE CONEXIÓN Y BASE DE DATOS (Nivel Medio)
# ==========================================

def conectar_odoo() -> int | bool:
    """
    Autentica al usuario en Odoo vía XML-RPC.

    :return: int o bool. El UID si la conexión es exitosa, False en caso contrario.
    """
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if uid:
            logger.info("Autenticado en Odoo.", uid=uid)
            return uid
        else:
            logger.error("Credenciales incorrectas.")
            return False
    except Exception as e:
        logger.error("Error de red al conectar.", error=str(e))
        return False


def vaciar_productos_odoo(uid: int, models) -> None:
    """
    Intenta eliminar todos los productos de Odoo.
    Si están en uso (pedidos, facturas), los archiva (active = False) por seguridad referencial.

    :param uid: ID del usuario.
    :param models: Objeto de conexión a modelos.
    """
    logger.warning("Iniciando limpieza de base de datos.")
    try:
        lista_ids = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search', [[]])

        if lista_ids:
            logger.info("Productos encontrados para limpiar.", total=len(lista_ids))
            try:
                models.execute_kw(DB, uid, PASSWORD, 'product.template', 'unlink', [lista_ids])
                logger.info("Productos eliminados correctamente.")
            except Exception as error_borrado:
                if 'sale.order.line' in str(error_borrado) or 'another model requires' in str(error_borrado):
                    logger.warning("Productos en uso, archivando en lugar de eliminar.")
                    models.execute_kw(
                        DB, uid, PASSWORD, 'product.template', 'write',
                        [lista_ids, {'active': False}]
                    )
                    logger.info("Productos antiguos archivados.")
                else:
                    logger.error("Error en limpieza.", error=str(error_borrado))
        else:
            logger.info("Base de datos ya estaba limpia.")
    except Exception as e:
        logger.error("Error al contactar con Odoo.", error=str(e))


def obtener_o_crear_categoria(uid: int, models, nombre_categoria: str) -> int | bool:
    """
    Busca una categoría por nombre en Odoo. Si no existe, la crea dinámicamente.

    :param uid: ID del usuario.
    :param models: Objeto de conexión a modelos.
    :param nombre_categoria: str. Nombre de la familia a buscar/crear.
    :return: int o bool. El ID de la categoría (categ_id) o False si hay error.
    """
    if not nombre_categoria:
        return False

    try:
        ids_categoria = models.execute_kw(
            DB, uid, PASSWORD, 'product.category', 'search',
            [[('name', '=', nombre_categoria)]]
        )

        if ids_categoria:
            return ids_categoria[0]
        else:
            nuevo_id = models.execute_kw(
                DB, uid, PASSWORD, 'product.category', 'create',
                [{'name': nombre_categoria}]
            )
            logger.info("Categoría creada en Odoo.", nombre=nombre_categoria)
            return nuevo_id
    except Exception as e:
        logger.error("Error gestionando categoría.", nombre=nombre_categoria, error=str(e))
        return False


def insertar(uid: int, models, codigo: str, nombre: str, datos_producto: dict) -> None:
    """
    Ejecuta la petición XML-RPC final para crear el registro del producto en Odoo.

    :param uid: ID del usuario autenticado.
    :param models: Objeto de conexión a modelos.
    :param codigo: str. Código del producto para logging.
    :param nombre: str. Nombre del producto para logging.
    :param datos_producto: dict. Estructura de datos a insertar.
    """
    try:
        models.execute_kw(DB, uid, PASSWORD, 'product.template', 'create', [datos_producto])
        logger.info("Producto subido.", codigo=codigo, nombre=nombre[:30])
    except Exception as e:
        logger.error("Error subiendo producto.", codigo=codigo, error=str(e))


# ==========================================
# 3. FUNCIONES AUXILIARES (Bajo Nivel)
# ==========================================

def preparar_normalizar_csv(f) -> tuple[csv.DictReader, list[str]]:
    """
    Preparación y normalización del archivo CSV para asegurar consistencia.

    :param f: file object. Archivo CSV abierto.
    :return: tuple. Objeto DictReader y la lista de cabeceras en mayúsculas.
    """
    reader = csv.DictReader(f, delimiter=';')
    cabeceras = [c.strip().upper() for c in reader.fieldnames]
    reader.fieldnames = cabeceras
    return reader, cabeceras


def preparar_cabeceras(cabeceras: list[str]) -> tuple[str, str, str | None, str | None]:
    """
    Mapea y prepara las cabeceras del CSV buscando dinámicamente columnas clave.

    :param cabeceras: list. Lista con los nombres de las columnas.
    :return: tuple. Nombres exactos de las columnas mapeadas.
    """
    col_codigo = cabeceras[0]
    col_nombre = cabeceras[1]

    col_familia = None
    col_baja = None

    for c in cabeceras:
        if 'NOMBRE FAMILIA' in c:
            col_familia = c
        if 'BAJA' in c and 'FECHA' not in c:
            col_baja = c

    return col_codigo, col_nombre, col_familia, col_baja


def leer_csv(
    col_codigo: str,
    col_nombre: str,
    col_familia: str | None,
    col_baja: str | None,
    fila: dict,
) -> tuple[str, str, str, str]:
    """
    Extrae y limpia los datos esenciales de la fila iterada del CSV.

    :param col_codigo: str. Clave de la columna de código.
    :param col_nombre: str. Clave de la columna de nombre.
    :param col_familia: str. Clave de la columna de familia.
    :param col_baja: str. Clave de la columna de baja.
    :param fila: dict. Diccionario con los datos de la fila actual.
    :return: tuple. Valores extraídos y limpios.
    """
    codigo = fila.get(col_codigo, '').strip()
    nombre = fila.get(col_nombre, '').strip()
    nombre_familia = fila.get(col_familia, '').strip() if col_familia else ''
    estado_baja = fila.get(col_baja, '').strip().upper() if col_baja else 'FALSE'
    return codigo, nombre, nombre_familia, estado_baja


def preparar_foto(codigo: str) -> str | bool:
    """
    Localiza la ruta de la fotografía usando el código del producto.

    :param codigo: str. Código del producto (usado como nombre de archivo).
    :return: str o bool. Imagen en base64 o False si no existe.
    """
    ruta_foto = os.path.join(CARPETA_FOTOS, f"{codigo}.jpg")
    foto_64 = preparar_imagen_base64(ruta_foto)
    return foto_64


def preparar_imagen_base64(ruta_imagen: str) -> str | bool:
    """
    Lee un archivo físico del disco y lo convierte al string en Base64.

    :param ruta_imagen: str. Ruta completa del archivo de imagen.
    :return: str o bool. Cadena en base64 o False si el archivo no se encuentra.
    """
    if os.path.exists(ruta_imagen):
        with open(ruta_imagen, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return False


def estructura(codigo: str, nombre: str, id_categoria: int | bool, foto_64: str | bool) -> dict:
    """
    Construye el diccionario de datos con la nomenclatura exacta de Odoo.

    :param codigo: str. Código de referencia del producto.
    :param nombre: str. Nombre descriptivo del producto.
    :param id_categoria: int o bool. ID de la categoría asociada.
    :param foto_64: str o bool. Imagen en formato base64.
    :return: dict. Diccionario estructurado.
    """
    datos_producto = {
        'name': nombre,
        'default_code': codigo,
        'list_price': 0.0,
        'type': 'product',
    }

    if id_categoria:
        datos_producto['categ_id'] = id_categoria

    if foto_64:
        datos_producto['image_1920'] = foto_64

    return datos_producto


# ==========================================
# EJECUCIÓN DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    subir_catalogo()
