"""
Módulo avanzado de importación masiva de Contactos (Clientes y Proveedores) para Odoo.

Este script gestiona la creación de registros en el modelo 'res.partner', validando duplicados
mediante NIF/CIF o coincidencia exacta de nombre. Soluciona errores de codificación regional 
(uso de latin-1) y asegura la compatibilidad de campos técnicos (nb_days y percent) para 
versiones modernas de Odoo. Incorpora archivado automático de bajas y generación dinámica e 
inteligente de Formas de Pago ('account.payment.term') analizando el texto mediante 
expresiones regulares, incluyendo filtros de seguridad contra valores numéricos anómalos.

@author BenjaminDTS
"""

import csv
import xmlrpc.client
import re

# ==========================================
# CONFIGURACIÓN DE ODOO
# ==========================================
URL = 'url_de_tu_odoo'  # Reemplaza con la URL de tu instancia de Odoo
DB = 'nombre_de_tu_base_de_datos'  # Reemplaza con el nombre de tu base de datos
USERNAME = 'tu_usuario'  # Reemplaza con tu usuario de Odoo
PASSWORD = 'tu_contraseña'  # Reemplaza con tu contraseña de Odoo

# Nombres de archivos (ajusta si tienen mayúsculas o minúsculas distintas en tu carpeta)
ARCHIVO_CLIENTES = 'Clientes.csv'
ARCHIVO_PROVEEDORES = 'PROVEEDORES.csv'

# Codificación 'latin-1' para procesar tildes y la Ñ correctamente
ENCODING_CSV = 'latin-1' 

# Memoria caché para optimizar las peticiones al servidor
CACHE_PAGOS = {}


# ==========================================
# 1. ORQUESTACIÓN PRINCIPAL
# ==========================================

def ejecutar_migracion_contactos():
    """
    Punto de entrada principal para la migración.
    Establece la conexión con Odoo vía XML-RPC y lanza los procesos de 
    importación secuencial para clientes y luego para proveedores, 
    ajustando los delimitadores según el formato de cada archivo.
    """
    uid = conectar_odoo()
    if not uid: 
        return

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    # IMPORTANTE: Clientes.csv suele usar ';' y Proveedores suele usar ','
    procesar_csv_contactos(uid, models, ARCHIVO_CLIENTES, es_proveedor=False, delimitador=';')
    procesar_csv_contactos(uid, models, ARCHIVO_PROVEEDORES, es_proveedor=True, delimitador=',')
    
    print("\n[OK] Migración de contactos finalizada con éxito.")


# ==========================================
# 2. LÓGICA DE PROCESADO
# ==========================================

def procesar_csv_contactos(uid, models, ruta_csv, es_proveedor, delimitador=';'):
    """
    Lee el archivo CSV e inserta los contactos en Odoo.
    Utiliza search_read para comprobar los roles existentes y solo actualiza
    la base de datos si el contacto necesita ser convertido al nuevo rol.
    
    :param uid: ID del usuario autenticado.
    :param models: Objeto de conexión a modelos.
    :param ruta_csv: Nombre del archivo CSV.
    :param es_proveedor: Booleano para el rol.
    :param delimitador: Delimitador del CSV.
    """
    tipo = "PROVEEDOR" if es_proveedor else "CLIENTE"
    print(f"\n--- INICIANDO IMPORTACIÓN DE {tipo}S DESDE {ruta_csv} ---")

    try:
        with open(ruta_csv, mode='r', encoding=ENCODING_CSV) as f:
            reader = csv.DictReader(f, delimiter=delimitador)
            reader.fieldnames = [c.strip().upper() for c in reader.fieldnames if c]
            
            for fila in reader:
                nombre = fila.get('NOMBRE', '').strip()
                if not nombre: continue

                try:
                    nif = fila.get('C.I.F.', fila.get('CIF', '')).strip()
                    
                    domain = [('name', '=', nombre)]
                    if nif:
                        domain = ['|', ('vat', '=', nif), ('name', '=', nombre)]
                    
                    # CAMBIO CLAVE: search_read nos permite ver cómo está configurado en Odoo
                    existente = models.execute_kw(DB, uid, PASSWORD, 'res.partner', 'search_read', 
                                                 [domain], 
                                                 {'fields': ['id', 'customer_rank', 'supplier_rank'], 'limit': 1})
                    
                    id_pago = gestionar_pago(uid, models, fila)

                    if existente:
                        partner_id = existente[0]['id']
                        c_rank = existente[0].get('customer_rank', 0)
                        s_rank = existente[0].get('supplier_rank', 0)

                        datos_actualizar = {}
                        
                        # Solo actualizamos si es proveedor y su rango de proveedor es 0
                        if es_proveedor and s_rank == 0:
                            datos_actualizar['supplier_rank'] = 1
                            if id_pago: datos_actualizar['property_supplier_payment_term_id'] = id_pago
                                
                        # Solo actualizamos si es cliente y su rango de cliente es 0
                        elif not es_proveedor and c_rank == 0:
                            datos_actualizar['customer_rank'] = 1
                            if id_pago: datos_actualizar['property_payment_term_id'] = id_pago

                        # Ejecutamos la actualización solo si hay cambios reales que hacer
                        if datos_actualizar:
                            models.execute_kw(DB, uid, PASSWORD, 'res.partner', 'write', [[partner_id], datos_actualizar])
                            print(f"  [UPDT] {nombre} (ID: {partner_id}) convertido también en {tipo}.")
                        else:
                            # Si ya estaba bien, lo ignoramos en silencio (para no ensuciar la consola)
                            pass 
                        
                        continue

                    # Si no existía de ninguna forma, lo creamos
                    crear(uid, models, es_proveedor, tipo, fila, nombre, id_pago)

                except Exception as error_contacto:
                    print(f"[-] Error en el contacto '{nombre}': {error_contacto}")
                    continue 

    except FileNotFoundError:
        print(f"[!] Archivo no encontrado: {ruta_csv}")
    except Exception as e:
        print(f"[!] Error crítico en el archivo {ruta_csv}: {e}")


# ==========================================
# 3. FUNCIONES DE NEGOCIO Y API (CREACIÓN)
# ==========================================

def gestionar_pago(uid, models, fila):
    """
    Extrae la forma de pago de la fila del Excel y gestiona su obtención 
    o creación dinámica en la contabilidad de Odoo.

    :param uid: int. ID de usuario autenticado.
    :param models: ServerProxy. Objeto de conexión.
    :param fila: dict. Diccionario con los datos de la fila actual.
    :return: int o bool. ID de la forma de pago en Odoo, o False si no aplica.
    """
    nombre_pago = fila.get('FORMA DE PAGO', '').strip()
    return obtener_o_crear_forma_pago(uid, models, nombre_pago)

def crear(uid, models, es_proveedor, tipo, fila, nombre, id_pago):
    """
    Prepara el diccionario final de datos y lanza la llamada XML-RPC para
    crear el registro en el modelo 'res.partner'.

    :param uid: int. ID de usuario autenticado.
    :param models: ServerProxy. Objeto de conexión.
    :param es_proveedor: bool. Determina la clasificación comercial.
    :param tipo: str. Etiqueta para la consola (CLIENTE/PROVEEDOR).
    :param fila: dict. Datos extraídos del CSV.
    :param nombre: str. Nombre limpio del contacto.
    :param id_pago: int o bool. ID relacional del plazo de pago.
    """
    datos = preparar_datos_contacto(fila, es_proveedor, id_pago)
    nuevo_id = models.execute_kw(DB, uid, PASSWORD, 'res.partner', 'create', [datos])
    print(f"[+] {tipo} Creado: {nombre[:30]}... (ID Odoo: {nuevo_id})")

def obtener_o_crear_forma_pago(uid, models, nombre_pago):
    """
    Busca una forma de pago existente por nombre, o la crea automáticamente 
    extrayendo el número de días del texto mediante expresiones regulares.
    Incluye protección contra sobrecargas (días > 365) y adapta los campos
    técnicos (nb_days, percent) a los requisitos de Odoo moderno.

    :param uid: int. ID del usuario autenticado.
    :param models: ServerProxy. Objeto de conexión.
    :param nombre_pago: str. Texto de la forma de pago.
    :return: int o bool. ID relacional del registro contable creado o encontrado.
    """
    if not nombre_pago or nombre_pago.lower() in ['nan', '']: 
        return False
        
    if nombre_pago in CACHE_PAGOS: 
        return CACHE_PAGOS[nombre_pago]

    # Buscar si ya existe
    term_ids = models.execute_kw(DB, uid, PASSWORD, 'account.payment.term', 'search', [[('name', '=', nombre_pago)]])
    if term_ids:
        CACHE_PAGOS[nombre_pago] = term_ids[0]
        return term_ids[0]

    # Extraer días (con filtro de seguridad para IBANs/Errores)
    numeros = re.findall(r'\d+', nombre_pago)
    dias = int(numeros[0]) if numeros and int(numeros[0]) <= 365 else 0

    try:
        # Crear cabecera y línea de pago
        nuevo_term_id = models.execute_kw(DB, uid, PASSWORD, 'account.payment.term', 'create', [{'name': nombre_pago}])
        
        # Inyectamos la regla matemática: 'nb_days' y 'percent'
        models.execute_kw(DB, uid, PASSWORD, 'account.payment.term.line', 'create', [{
            'payment_id': nuevo_term_id,
            'value': 'percent',
            'nb_days': dias,
            'value_amount': 100.0
        }])
        
        print(f"  [*] Creada Forma de Pago en contabilidad: '{nombre_pago}' ({dias} días)")
        CACHE_PAGOS[nombre_pago] = nuevo_term_id
        return nuevo_term_id
    except Exception as e:
        print(f"  [!] Error automatizando la forma de pago '{nombre_pago}': {e}")
        return False


# ==========================================
# 4. FUNCIONES AUXILIARES Y MAPEADO
# ==========================================

def preparar_datos_contacto(fila, es_proveedor, id_pago):
    """
    Mapea las columnas del CSV al diccionario de campos nativos de Odoo.
    Gestiona el archivado mediante la Fecha de Baja y el registro de históricos
    en la libreta de notas internas.

    :param fila: dict. Fila extraída del documento.
    :param es_proveedor: bool. Determina el rank comercial del contacto.
    :param id_pago: int o bool. Referencia del modelo de pago.
    :return: dict. Objeto listo para su inserción por la API.
    """
    ref = fila.get('CLIENTE', fila.get('PROVEEDOR', ''))
    f_alta = fila.get('FECHA DE ALTA', '').strip()
    f_baja = fila.get('FECHA DE BAJA', '').strip()

    datos = {
        'name': fila.get('NOMBRE', ''),
        'street': fila.get('DIRECCIÓN', ''),
        'zip': fila.get('C. POSTAL', ''),
        'city': fila.get('POBLACIÓN', ''),
        'vat': fila.get('C.I.F.', ''),
        'phone': fila.get('TELÉFONO', ''),
        'email': fila.get('EMAIL', ''),
        'customer_rank': 0 if es_proveedor else 1,
        'supplier_rank': 1 if es_proveedor else 0,
        'is_company': True,
        'ref': ref,
        'active': False if f_baja else True, # Archiva si hay fecha de baja
        'comment': f"Importado por script de automatización. Ref original: {ref}\nFecha Alta Original: {f_alta}"
    }
    
    # Enlace de plazos de pago (campos técnicos de Odoo)
    if id_pago:
        campo = 'property_supplier_payment_term_id' if es_proveedor else 'property_payment_term_id'
        datos[campo] = id_pago
            
    return datos

def conectar_odoo():
    """
    Gestiona el proceso de autenticación XML-RPC contra la base de datos de Odoo.

    :return: int o bool. UID del usuario autenticado o False si hubo un error.
    """
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})
        if uid:
            print(f"[Conexión OK] Autenticado de forma segura con UID: {uid}")
            return uid
        print("[!] Error: Credenciales incorrectas.")
        return False
    except Exception as e:
        print(f"[!] Error de conexión de red: {e}")
        return False


# ==========================================
# EJECUCIÓN DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    ejecutar_migracion_contactos()