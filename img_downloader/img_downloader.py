"""
Módulo de automatización para la extracción y descarga de imágenes de productos.
Autor: BenjaminDTS
"""

import os
import time
import csv
import re
import json
import requests
from PIL import Image
from io import BytesIO

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
except ImportError as err:
    # Por qué: Evita fallos silenciosos si faltan dependencias clave en el entorno de ejecución.
    print(f"[!] Error de importación: {err}. Asegúrate de instalar undetected-chromedriver y selenium.")


# ==============================================================================
# NIVEL 1: ORQUESTADORES PRINCIPALES (Criticidad Alta)
# Define el flujo de ejecución. Su responsabilidad es delegar tareas.
# ==============================================================================

def main(input_csv='input_products.csv', output_dir='output_images', log_file='download_errors.log'): #Aqui se pueden modificar los nombres de los archivos de entrada y salida
    """
    Punto de entrada principal del motor de scraping.
    Por qué: Orquesta la creación del entorno, inicialización del navegador y el ciclo de búsqueda de forma modular.
    """
    prepare_directory(output_dir)
    prepare_log(log_file)

    print("--- INICIANDO ROBOT DE DESCARGA (SISTEMA ANTI-403 + LOG) [BenjaminDTS] ---")
    browser_options = configure_browser()
    driver = None
    
    try:
        validated_path = resolve_file_path(input_csv)
        driver = initialize_browser(browser_options)
        process_catalog(validated_path, output_dir, log_file, driver)
    except Exception as e:
        # Por qué: Centralización de errores críticos del proceso global para evitar cierres abruptos.
        print(f"\n[!] Error crítico del sistema: {type(e).__name__} - {e}")
    finally:
        close_browser_safely(driver)


def process_catalog(csv_file, output_dir, log_file, driver):
    """
    Maneja la lectura del dataset y la validación de sus cabeceras.
    Por qué: Aísla la capa de manipulación de datos (I/O) de las acciones del navegador web.
    """
    with open(csv_file, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=',')
        
        if not reader.fieldnames:
            raise ValueError("El archivo CSV está vacío o sus cabeceras son ilegibles.")
            
        headers = [c.strip().upper() for c in reader.fieldnames]
        reader.fieldnames = headers
        
        if len(headers) < 2:
            raise ValueError(f"El CSV requiere al menos 2 columnas. Cabeceras detectadas: {headers}")
        
        iterate_and_search(output_dir, log_file, driver, reader)


def iterate_and_search(output_dir, log_file, driver, reader):
    """
    Iterador principal de filas extraídas con orquestación de búsqueda.
    Por qué: Transforma los datos crudos en variables de búsqueda inyectables y omite los ya procesados.
    """
    for row in reader:
        item_id = normalize_numeric_id(row.get('REF', ''))
        raw_name = row.get('LABEL', '').strip()
        brand = filter_generic_brands(row.get('MARCA', '').strip())
        category = row.get('CATEGORIA', '').strip()
                
        if not item_id or not raw_name: 
            continue
                
        safe_id = sanitize_filename(item_id)
        img_path = os.path.join(output_dir, f"{safe_id}.jpg")
        
        if os.path.exists(img_path): 
            continue 
                
        clean_name = normalize_product_name(raw_name)
        search_query = re.sub(r'\s+', ' ', f"{clean_name} {brand} {category}".strip())
                
        print(f"[*] Buscando [{item_id}]: {search_query[:40]}...", end=" ", flush=True)
        download_search_engine_image(driver, img_path, search_query, item_id, log_file)


# ==============================================================================
# NIVEL 2: CAPA DE INFRAESTRUCTURA WEB (Criticidad Media-Alta)
# Maneja la comunicación externa (Red, Selenium, DOM, HTTP).
# ==============================================================================

def download_search_engine_image(driver, img_path, query, item_id, log_file):
    """
    Controla el flujo de navegación HTTP y la interacción con los selectores del DOM.
    Por qué: Encapsula la lógica de red para no abortar el ciclo completo si una página falla.
    """
    try:
        navigate_to_search(driver, query)
        dom_elements = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
        hd_url, thumb_url = extract_image_urls(dom_elements)
        manage_download_strategy(img_path, hd_url, thumb_url, item_id, log_file)
    except Exception as e:
        # Por qué: Se captura a nivel de componente para registrar la caída temporal del DOM.
        print(f"Error procesando DOM: {e}")
    time.sleep(1)


def navigate_to_search(driver, query):
    """
    Formatea la URL y acciona la petición GET del driver web.
    Por qué: Aísla la carga principal para facilitar futuras migraciones de motor de búsqueda.
    """
    search_url = f"https://www.bing.com/images/search?q={query}+producto"
    driver.get(search_url)
    time.sleep(2)


def extract_image_urls(elements):
    """
    Extrae la URL original (HD) y la URL en caché del buscador (miniatura).
    Por qué: Almacena la versión de caché como fallback inmediato ante un error 403 o enlace roto.
    """
    for element in elements:
        metadata = element.get_attribute("m")
        if metadata:
            try:
                data = json.loads(metadata)
                url_hd = data.get("murl")
                url_thumb = data.get("turl")
                if url_hd and url_hd.startswith("http"):
                    return url_hd, url_thumb
            except json.JSONDecodeError as e:
                # Por qué: Previene caídas si la estructura interna del DOM del motor cambia de formato.
                print(f"Fallo decodificando metadatos: {e}")
    return None, None


def manage_download_strategy(img_path, hd_url, thumb_url, item_id, log_file):
    """
    Orquesta la cascada de intentos de descarga (Principal -> Fallback).
    Por qué: Maximiza la tasa de éxito recurriendo a resoluciones menores si el host principal bloquea el bot.
    """
    if not hd_url:
        print("Sin resultados.")
        return

    success_hd = attempt_download(img_path, hd_url, "HD")
    if not success_hd and thumb_url:
        print("-> Rescate con miniatura...", end=" ")
        success_thumb = attempt_download(img_path, thumb_url, "Miniatura")
        if success_thumb:
            log_fallback_download(item_id, log_file)


def attempt_download(img_path, target_url, label):
    """
    Lanza el request HTTP inyectando cabeceras y gestionando el estado binario.
    Por qué: El Referer y el User-Agent simulan navegación humana, eludiendo bloqueos por hotlink (Anti-403).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://www.bing.com/"
    }
    try:
        response = requests.get(target_url, headers=headers, timeout=12)
        if response.status_code == 200:
            return process_and_save_image(img_path, response.content, label)
        
        print(f"Bloqueo {response.status_code} ({label})", end=" ")
        return False
    except Exception as e:
        # Por qué: Captura timeouts y cortes de conexión del host remoto.
        print(f"Error de red ({label})", end=" ")
        return False


# ==============================================================================
# NIVEL 3: LÓGICA DE NEGOCIO Y TRANSFORMACIÓN (Criticidad Media)
# Reglas de dominio. Purifican los datos en bruto para convertirlos en entidades.
# ==============================================================================

def normalize_product_name(text):
    """
    Orquesta la normalización del campo de nombre principal.
    Por qué: Aplica Clean Code delegando las transformaciones específicas a subfunciones aisladas.
    """
    text = str(text).upper().split('..')[0]
    text = fix_corrupt_characters(text)
    seo_context = generate_seo_context(text)
    return clean_and_join_text(text, seo_context)


def fix_corrupt_characters(text):
    """
    Mapea y corrige codificaciones rotas provenientes de la base de datos.
    Por qué: Reconstruye caracteres esenciales para que el motor de búsqueda comprenda la palabra.
    """
    replacements = {
        'Ì': 'I', 'Ï': 'I', 'Ö': 'O', 'Ä': 'A', '—': '-', 'Í': 'I', 
        'Ã': 'A', '±': '-', 'Â': 'A', 'Ç': 'C', 'Ñ': 'Ñ', 'Ó': 'O', 
        'Ú': 'U', 'É': 'E', 'Ü': 'U', 'À': 'A'
    }
    for broken_char, valid_char in replacements.items():
        text = text.replace(broken_char, valid_char)
    return text


def generate_seo_context(text):
    """
    Calcula dinámicamente palabras clave de contexto según la familia del producto.
    Por qué: Prioriza que el motor devuelva fotografías reales de producto comercial y no diagramas.
    """
    if "SIERRA" in text or "MOTOSIERRA" in text: return "herramienta motosierra comprar"
    if "MOTOAZADA" in text or "MOTOCULTOR" in text: return "maquinaria agricola comprar"
    if "BOMBA" in text: return "agua fontaneria comprar"
    if "LITIO" in text or "GRASA" in text: return "bote grasa lubricante comprar"
    if "ADBLUE" in text: return "garrafa adblue comprar"
    if "REFRIG" in text or "ANTICONGELANTE" in text: return "garrafa anticongelante refrigerante motor comprar"
    return "comprar"


def clean_and_join_text(text, context):
    """
    Elimina caracteres especiales y unidades de medida abreviadas.
    Por qué: Limpia la 'basura' propia de inventarios ERP dejando un título orgánico e indexable.
    """
    text = re.sub(r'[%.\(\)]', ' ', text)
    noise_words = {
        'LTS', 'GR', 'REFRIG', 'INCLUIDA', 'SI', 'APORTACIO', 
        'APORTACION', 'CON', 'X', 'KGS', 'CC', 'ML'
    }
    valid_words = [word for word in text.split() if word not in noise_words and len(word) > 1]
    return f"{' '.join(valid_words).strip()} {context}".strip()


def filter_generic_brands(brand_raw):
    """
    Depura las marcas de fabricante genéricas que no aportan valor semántico.
    Por qué: Optimiza la búsqueda en el motor al eliminar ruido que empeora los resultados.
    """
    ignored_brands = {
        'MARCAS VARIAS', 'MARCA VARIA', 'GENERICO', 'GENÉRICO', 
        'GENERICA', 'GENÉRICA', 'SIN MARCA', 'AFT'
    }
    return '' if brand_raw.upper() in ignored_brands else brand_raw


def normalize_numeric_id(value):
    """
    Parsea de vuelta a texto los valores numéricos alterados por notación científica.
    Por qué: Garantiza que los identificadores de artículo (SKU/Ref) permanezcan exactos para el guardado.
    """
    value_str = str(value).strip().replace(',', '.')
    
    if 'E+' in value_str.upper():
        try:
            return str(int(float(value_str)))
        except ValueError as e:
            # Por qué: Asegura que el flujo de datos no se interrumpa si el valor no es parseable matemáticamente.
            print(f"[*] Fallo interpretando notación científica: {e}")
            return value_str
    return value_str


# ==============================================================================
# NIVEL 4: UTILIDADES DEL SISTEMA Y SOPORTE (Criticidad Baja)
# Operaciones estándar, I/O simple, configuraciones y utilidades de sistema.
# ==============================================================================

def configure_browser():
    """
    Configura los parámetros subyacentes del motor Chromium.
    Por qué: Desactiva componentes innecesarios (GPU, sandbox) para maximizar el rendimiento y estabilidad.
    """
    options = uc.ChromeOptions()
    
    # Por qué: Se utiliza variable de entorno para no exponer rutas físicas ni usuarios locales.
    binary_path = os.getenv('BROWSER_BINARY_PATH')
    if binary_path:
        options.binary_location = binary_path
        
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-notifications')
    return options


def initialize_browser(options):
    """
    Instancia el navegador vinculando la configuración establecida.
    Por qué: Fija tiempos de espera globales para evitar bloqueos infinitos en cargas de red lentas.
    """
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def close_browser_safely(driver):
    """
    Ejecuta la terminación controlada del driver mitigando excepciones del OS.
    Por qué: Previene el 'OSError: [WinError 6]' generado por el destructor asíncrono de undetected_chromedriver.
    """
    if driver is not None:
        try:
            if hasattr(driver.__class__, '__del__'):
                setattr(driver.__class__, '__del__', lambda self: None)
            driver.quit()
        except OSError as e:
            # Por qué: Se absorbe el error exclusivamente si el manejador ya fue destruido por el OS.
            print(f"[*] Limpieza completada (Descriptor cerrado): {e}")
        except Exception as e:
            # Por qué: Aplicamos manejo centralizado registrando cualquier anomalía residual.
            print(f"[!] Advertencia al cerrar el navegador: {e}")
    print("--- NAVEGADOR CERRADO AUTOMÁTICAMENTE ---")


def prepare_directory(path):
    """
    Verifica y crea el directorio de salida de imágenes.
    Por qué: Evita excepciones a nivel de sistema operativo al intentar guardar los binarios.
    """
    if not os.path.exists(path): 
        os.makedirs(path)


def prepare_log(log_path):
    """
    Inicializa el archivo de registro para las descargas fallidas o de baja resolución.
    Por qué: Separa visualmente las ejecuciones en el log temporal para facilitar la depuración.
    """
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n--- NUEVA EJECUCIÓN: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")


def log_fallback_download(item_id, log_file):
    """
    Anota el identificador de producto afectado en un archivo de texto.
    Por qué: Permite generar un reporte para control de calidad manual posterior.
    """
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{item_id}\n")
    except Exception as e:
        # Por qué: Aísla el error de I/O de disco para no romper la ejecución en curso.
        print(f"[!] Fallo escribiendo log: {e}", end=" ")


def resolve_file_path(filename):
    """
    Resuelve la ruta absoluta del archivo buscando en el directorio actual y su padre.
    Por qué: Previene errores [Errno 2] al ejecutar el script desde subdirectorios del proyecto.
    """
    current_path = os.path.abspath(filename)
    if os.path.exists(current_path):
        return current_path
        
    parent_path = os.path.abspath(os.path.join(os.pardir, filename))
    if os.path.exists(parent_path):
        return parent_path
        
    raise FileNotFoundError(f"Archivo '{filename}' no encontrado en el directorio actual ni superior.")


def sanitize_filename(text):
    """
    Elimina caracteres no válidos para el sistema de archivos del OS.
    Por qué: Evita excepciones OSError al intentar escribir el archivo .jpg en el disco.
    """
    return re.sub(r'[\\/*?:"<>|]', '_', str(text))


def process_and_save_image(img_path, raw_bytes, label):
    """
    Convierte el buffer a formato RGB estandarizado comprobando su integridad.
    Por qué: Maximiza la fidelidad visual, recorta tamaños excesivos y garantiza un binario válido.
    """
    try:
        img = Image.open(BytesIO(raw_bytes)).convert("RGB")
        img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        img.save(img_path, "JPEG", optimize=True, quality=95)
        print(f"¡OK! [{label}]")
        return True
    except Exception as e:
        # Por qué: Intercepta bytes corruptos o respuestas HTML disfrazadas de imagen.
        print(f"Error procesando binario: {type(e).__name__}", end=" ")
        return False


if __name__ == "__main__":
    main()