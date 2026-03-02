"""
Módulo optimizado de actualización de Precios Base y Tarifas B2C para Odoo.

Realiza una doble inyección de precios mediante XML-RPC:
1. Extrae precio sin IVA para la ficha contable principal ('list_price').
2. Extrae precio final para una regla visual en tarifa B2C ('pricelist.item').

@author: BenjaminDTS
"""

import csv
import xmlrpc.client

# ==========================================
# CONFIGURACIÓN DE ODOO
# ==========================================
URL = 'http://localhost:8069'
DB = 'nombre_de_tu_base_de_datos'
USERNAME = 'tu_usuario'
PASSWORD = 'tu_contraseña'

ARCHIVO_TARIFAS = 'nombre_del_archivo.csv'
COLUMNA_SIN_IVA = 'nombre_del_campo_sin_iva'
COLUMNA_CON_IVA = 'nombre_del_campo_con_iva'
NOMBRE_TARIFA_ODOO = 'Tarifa PVP (Con IVA)'

# ==========================================
# 1. ORQUESTACIÓN PRINCIPAL
# ==========================================

def ejecutar_actualizacion_doble():
    """
    Controlador principal del módulo.
    
    Orquesta el flujo de ejecución: valida la conexión, carga las estructuras
    de datos en memoria caché y lanza el procesamiento del archivo CSV.
    
    :return: None
    """
    uid = conectar_odoo()
    if not uid: return
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    print("\n[1/3] Descargando mapa de productos a la memoria caché...")
    cache_productos = pre_cargar_productos(uid, models)
    
    print("\n[2/3] Preparando entorno de Tarifas Visuales...")
    tarifa_id = obtener_o_crear_tarifa_b2c(uid, models)
    cache_reglas = pre_cargar_reglas(uid, models, tarifa_id)

    print(f"\n[3/3] Procesando archivo de Excel ({ARCHIVO_TARIFAS})...")
    procesar_csv_doble(uid, models, cache_productos, tarifa_id, cache_reglas)
    print("\n[OK] Actualización Híbrida de Precios finalizada con éxito.")

# ==========================================
# 2. LÓGICA DE ACTUALIZACIÓN
# ==========================================

def procesar_csv_doble(uid, models, cache_productos, tarifa_id, cache_reglas):
    """
    Abre y recorre el archivo CSV, delegando la actualización línea por línea.
    
    :param uid: int. Identificador del usuario de Odoo autenticado.
    :param models: xmlrpc.client.ServerProxy. Instancia de conexión a los modelos.
    :param cache_productos: dict. Mapa en memoria {codigo_producto: id_producto}.
    :param tarifa_id: int. Identificador de la lista de precios B2C en Odoo.
    :param cache_reglas: dict. Mapa de reglas {(tarifa_id, producto_id): regla_id}.
    :return: None
    """
    stats = {'base': 0, 'reglas_c': 0, 'reglas_u': 0, 'no_encontrados': 0, 'lineas': 0}

    try:
        with open(ARCHIVO_TARIFAS, mode='r', encoding='utf-8-sig', errors='ignore') as f:
            reader = inicializar_lector_csv(f)
            
            for fila in reader:
                stats['lineas'] += 1
                if stats['lineas'] % 100 == 0:
                    print(f"  ... Leyendo línea {stats['lineas']} ...")
                
                procesar_fila(uid, models, fila, cache_productos, tarifa_id, cache_reglas, stats)

    except FileNotFoundError:
        print(f"[!] Archivo no encontrado: {ARCHIVO_TARIFAS}")
    
    imprimir_resumen(stats)

def procesar_fila(uid, models, fila, cache_productos, tarifa_id, cache_reglas, stats):
    """
    Analiza una fila individual del CSV y ejecuta las inyecciones de precio.
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a los modelos de Odoo.
    :param fila: dict. Diccionario con los datos de la fila actual del CSV.
    :param cache_productos: dict. Mapa de productos pre-cargado.
    :param tarifa_id: int. ID de la tarifa destino.
    :param cache_reglas: dict. Mapa de reglas pre-cargado.
    :param stats: dict. Diccionario contador de estadísticas.
    :return: None
    """
    codigo = fila.get('Artículo', '').strip()
    if not codigo: return

    if codigo not in cache_productos:
        stats['no_encontrados'] += 1
        return
    
    prod_id = cache_productos[codigo]
    actualizar_precio_base(uid, models, fila, prod_id, stats)
    actualizar_regla_tarifa(uid, models, fila, prod_id, tarifa_id, cache_reglas, stats)

def actualizar_precio_base(uid, models, fila, prod_id, stats):
    """
    Inyecta el precio sin IVA en la ficha contable del producto ('list_price').
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a modelos de Odoo.
    :param fila: dict. Fila actual del archivo CSV.
    :param prod_id: int. ID del producto en la base de datos de Odoo.
    :param stats: dict. Diccionario para incrementar el contador de éxitos.
    :return: None
    """
    precio = limpiar_precio(fila.get(COLUMNA_SIN_IVA, 0))
    if precio > 0:
        models.execute_kw(DB, uid, PASSWORD, 'product.template', 'write', [[prod_id], {'list_price': precio}])
        stats['base'] += 1

def actualizar_regla_tarifa(uid, models, fila, prod_id, tarifa_id, cache_reglas, stats):
    """
    Crea o actualiza la regla de precio con IVA dentro de la tarifa B2C.
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a modelos de Odoo.
    :param fila: dict. Fila actual del archivo CSV.
    :param prod_id: int. ID del producto.
    :param tarifa_id: int. ID de la lista de precios.
    :param cache_reglas: dict. Mapa para verificar si la regla ya existe.
    :param stats: dict. Contadores de estadísticas (actualizaciones o creaciones).
    :return: None
    """
    precio = limpiar_precio(fila.get(COLUMNA_CON_IVA, 0))
    if precio <= 0: return

    clave_regla = (tarifa_id, prod_id)
    try:
        if clave_regla in cache_reglas:
            regla_id = cache_reglas[clave_regla]
            models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'write', [[regla_id], {'fixed_price': precio}])
            stats['reglas_u'] += 1
        else:
            nueva_id = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'create', [{
                'pricelist_id': tarifa_id, 'product_tmpl_id': prod_id, 'applied_on': '1_product',
                'compute_price': 'fixed', 'fixed_price': precio
            }])
            cache_reglas[clave_regla] = nueva_id
            stats['reglas_c'] += 1
    except Exception as e:
        print(f"[-] Error en tarifa (Regla {prod_id}): {e}")

# ==========================================
# 3. FUNCIONES AUXILIARES Y CACHÉ
# ==========================================

def inicializar_lector_csv(f):
    """
    Detecta automáticamente el delimitador del archivo y limpia las cabeceras.
    
    :param f: TextIOWrapper. Archivo CSV abierto.
    :return: csv.DictReader. Lector iterador configurado.
    """
    primera_linea = f.readline()
    delimitador = ';' if ';' in primera_linea else ','
    f.seek(0)
    reader = csv.DictReader(f, delimiter=delimitador)
    reader.fieldnames = [str(c).strip() for c in reader.fieldnames if c]
    return reader

def pre_cargar_productos(uid, models):
    """
    Descarga un mapa en RAM de todos los productos de Odoo.
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a modelos de Odoo.
    :return: dict. Formato {default_code (str): id_producto (int)}.
    """
    prods = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read', [[]], {'fields': ['id', 'default_code']})
    return {p['default_code']: p['id'] for p in prods if p.get('default_code')}

def obtener_o_crear_tarifa_b2c(uid, models):
    """
    Localiza la lista de precios definida; si no existe, la crea.
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a modelos de Odoo.
    :return: int. ID de la lista de precios (tarifa) en Odoo.
    """
    existe = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'search', [[('name', '=', NOMBRE_TARIFA_ODOO)]])
    if existe: return existe[0]
    return models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'create', [{'name': NOMBRE_TARIFA_ODOO}])

def pre_cargar_reglas(uid, models, tarifa_id):
    """
    Descarga un mapa en RAM de todas las reglas de precio existentes en una tarifa.
    
    :param uid: int. Identificador del usuario.
    :param models: xmlrpc.client.ServerProxy. Conexión a modelos de Odoo.
    :param tarifa_id: int. ID de la tarifa a consultar.
    :return: dict. Formato {(tarifa_id, producto_id): regla_id}.
    """
    reglas = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist.item', 'search_read', 
                               [[('pricelist_id', '=', tarifa_id)]], {'fields': ['id', 'pricelist_id', 'product_tmpl_id']})
    cache = {}
    for r in reglas:
        if r.get('product_tmpl_id'):
            t_id = r['product_tmpl_id'][0] if isinstance(r['product_tmpl_id'], list) else r['product_tmpl_id']
            cache[(tarifa_id, t_id)] = r['id']
    return cache

def limpiar_precio(valor):
    """
    Convierte el formato de texto extraído del CSV a un flotante apto para Odoo.
    
    :param valor: str o float. Celda de precio en el CSV.
    :return: float. Precio validado y limpio (0.0 si es inválido o nulo).
    """
    try:
        if not valor or str(valor).lower() in ['nan', '']: return 0.0
        return float(str(valor).replace(',', '.').strip())
    except ValueError:
        return 0.0

def imprimir_resumen(stats):
    """
    Muestra en consola las métricas recolectadas durante la ejecución.
    
    :param stats: dict. Diccionario conteniendo los recuentos del proceso.
    :return: None
    """
    print(f"\n--- RESUMEN DE LA ACTUALIZACIÓN ---")
    print(f"Líneas procesadas: {stats['lineas']}")
    print(f"Precios Base (Sin IVA) actualizados: {stats['base']}")
    print(f"Reglas visuales (Con IVA) creadas: {stats['reglas_c']}")
    print(f"Reglas visuales (Con IVA) actualizadas: {stats['reglas_u']}")
    print(f"Productos omitidos (No encontrados): {stats['no_encontrados']}")

def conectar_odoo():
    """
    Establece la conexión inicial con el servidor vía XML-RPC.
    
    :return: int o bool. UID del usuario autenticado o False si ocurre un error.
    """
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if uid: return uid
    except Exception:
        pass
    print("[!] Error de conexión o credenciales.")
    return False

if __name__ == "__main__":
    ejecutar_actualizacion_doble()