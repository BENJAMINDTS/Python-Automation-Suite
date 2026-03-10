"""
Módulo de importación masiva de Productos y Listas de Precios (Tarifas).
Implementa un sistema de 'Turbo Caché' para precargar modelos en memoria (RAM)
y evitar bloqueos o timeouts del servidor por exceso de peticiones XML-RPC.

@author BenjaminDTS
"""

import csv
import xmlrpc.client
import json

# ==========================================
# CONFIGURACIÓN Y CONSTANTES
# ==========================================
# Variables genéricas para evitar exposición de secretos en el control de versiones.
URL = 'https://tu-dominio-odoo.com'
DB = 'nombre_base_datos'
USERNAME = 'tu_usuario@email.com'
PASSWORD = 'tu_contraseña_segura'
ARCHIVO_TARIFAS = 'tarifas_ejemplo.csv'

COLUMNAS_TARIFAS = [
    'Tarifa PVP 2', 'Tarifa PVP', 'Tarifa PVP sin Iva', 
    'Nuevos cliente', 'Tarifa 15', 'Cliente fidelizado'
]

def get_odoo_proxy(endpoint):
    """
    Genera el proxy de conexión XML-RPC.
    Se encapsula para centralizar la instanciación de los clientes y evitar redundancias.
    """
    return xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/{endpoint}')

def pre_cargar_productos(uid, models):
    """
    Carga en memoria el mapeo de default_code -> id en una sola petición (Eager Loading).
    Previene consultas N+1 durante la iteración del CSV.
    """
    prods = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read', 
                              [[]], {'fields': ['id', 'default_code']})
    return {p['default_code']: p['id'] for p in prods if p.get('default_code')}

def pre_cargar_reglas(uid, models, cache_tarifas):
    """
    Obtiene las reglas de precios existentes de las tarifas objetivo (Eager Loading).
    Evita consultar la base de datos por cada celda de precio procesada.
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
    return cache

def limpiar_precio(valor):
    """
    Sanitiza strings de precios convirtiendo comas en puntos.
    Asegura que Odoo reciba un float numérico válido para evitar excepciones de tipo.
    """
    try:
        if not valor: return 0.0
        return float(str(valor).replace(',', '.').strip())
    except (ValueError, TypeError):
        return 0.0

def procesar_producto(codigo, nombre, fila, uid, models, cache):
    """
    Asegura la existencia del producto en Odoo y lo añade a la caché si es nuevo.
    Aísla la responsabilidad de creación de producto (Single Responsibility).
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
    return cache['productos'][codigo]

def procesar_reglas_tarifa(prod_id, fila, uid, models, cache):
    """
    Itera sobre las columnas configuradas y actualiza o crea las reglas de precio.
    Aísla la lógica de actualización de tarifas manteniendo la función bajo 30 líneas.
    """
    for tarifa_nombre in COLUMNAS_TARIFAS:
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

def inicializar_cache(uid, models):
    """
    Orquesta la carga inicial de datos en RAM para acelerar el procesamiento masivo.
    """
    cache = {'productos': pre_cargar_productos(uid, models), 'tarifas': {}}
    
    for n in COLUMNAS_TARIFAS:
        tarifa = models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'search', [[('name', '=', n)]])
        cache['tarifas'][n] = tarifa[0] if tarifa else models.execute_kw(DB, uid, PASSWORD, 'product.pricelist', 'create', [{'name': n}])
        
    cache['reglas'] = pre_cargar_reglas(uid, models, cache['tarifas'])
    return cache

def ejecutar_importacion():
    """
    Punto de entrada principal. Coordina autenticación, lectura y procesamiento.
    Devuelve formato JSON estándar con el resultado del proceso para integraciones REST.
    """
    try:
        common = get_odoo_proxy('common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if not uid:
            return json.dumps({"success": False, "data": None, "message": "Autenticación fallida."})

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

        return json.dumps({"success": True, "data": None, "message": "Importación procesada con éxito."})

    except Exception as e:
        return json.dumps({"success": False, "data": None, "message": f"Error crítico en ejecución: {str(e)}"})

if __name__ == "__main__":
    resultado = ejecutar_importacion()
    print(resultado)