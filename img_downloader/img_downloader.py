"""
Módulo de automatización para la extracción y descarga de imágenes de productos.
Autor: BenjaminDTS
"""

import os
import time
import csv
import re
import getpass
import requests
from PIL import Image
from io import BytesIO

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
except ImportError:
    print("[!] Error: Asegúrate de tener instalado undetected-chromedriver y selenium")


def ejecutor_imagenes_opera(archivo_csv='ARTÍCULOS.csv'):
    """
    Motor principal de scrapeo con detección exacta de NOMBRE MARCA.
    Prepara el directorio, configura Opera GX, lee el CSV y arranca el ciclo de búsqueda.

    Args:
        archivo_csv (str): Ruta del archivo CSV a procesar. Por defecto 'ARTÍCULOS.csv'.
    """
    output_dir = 'PRODUCTOS_WEB'
    if not os.path.exists(output_dir): 
        os.makedirs(output_dir)

    print("--- INICIANDO ROBOT OPERA GX v143 [BenjaminDTS] ---")
    
    opciones = configuracion_opera_benjamin()
    
    try:
        driver = especificar_version(opciones)
        
        # Usamos utf-8-sig para leer a la perfección los CSV de Excel
        with open(archivo_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            cabeceras = [c.strip().upper() for c in reader.fieldnames]
            reader.fieldnames = cabeceras
            
            # Determinamos las columnas correctas para NOMBRE, CÓDIGO y MARCA
            col_nombre = 'NOMBRE' if 'NOMBRE' in cabeceras else cabeceras[1]
            col_codigo = cabeceras[0]      
            col_marca = determinar_columna_marca(cabeceras)
            
            recorrer_csv(output_dir, driver, reader, col_nombre, col_codigo, col_marca)

    except Exception as e:
        print(f"\n[!] Error crítico del sistema: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass
        print("--- NAVEGADOR CERRADO AUTOMÁTICAMENTE ---")


def configuracion_opera_benjamin():
    """
    Configura el navegador con la ruta exacta de Opera GX.

    Returns:
        uc.ChromeOptions: Objeto con las opciones de inicialización del navegador.
    """
    usuario = getpass.getuser()
    ruta_gx = rf"C:\Users\{usuario}\AppData\Local\Programs\Opera GX\opera.exe"
    
    options = uc.ChromeOptions()
    options.binary_location = ruta_gx
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-notifications')
    return options
  

def determinar_columna_marca(cabeceras):
    """
    Detección inteligente de la columna de marca, buscando coincidencias comunes 
    y priorizando nombres claros para mejorar la precisión de la búsqueda.

    Args:
        cabeceras (list): Lista con los nombres de las columnas del CSV.

    Returns:
        str | None: El nombre de la columna de marca encontrada o None.
    """
    col_marca = None
    if 'NOMBRE MARCA' in cabeceras:
        col_marca = 'NOMBRE MARCA'
    else:
        for c in cabeceras:
            if 'MARCA' in c or 'FABRICANTE' in c:
                col_marca = c
                if 'NOMBRE' in c: break
    return col_marca
        

def especificar_version(opciones):
    """
    Inicializa el navegador especificando la versión principal de Chrome.

    Args:
        opciones (uc.ChromeOptions): Opciones configuradas previamente.

    Returns:
        uc.Chrome: Instancia del navegador controlable.
    """
    driver = uc.Chrome(options=opciones, version_main=143)
    driver.set_page_load_timeout(30)
    return driver
        

def recorrer_csv(output_dir, driver, reader, col_nombre, col_codigo, col_marca):
    """
    Itera sobre cada fila del CSV extrayendo los datos y lanzando la descarga.

    Args:
        output_dir (str): Directorio donde se guardarán las imágenes.
        driver (uc.Chrome): Instancia del navegador.
        reader (csv.DictReader): Lector del archivo CSV.
        col_nombre (str): Nombre de la columna del artículo.
        col_codigo (str): Nombre de la columna del código.
        col_marca (str | None): Nombre de la columna de la marca.
    """
    for fila in reader:
        codigo = fila.get(col_codigo, '').strip()
        nombre_raw = fila.get(col_nombre, '').strip()
        marca_raw = fila.get(col_marca, '').strip() if col_marca else ''
        marca_raw = filtrar_marcas(marca_raw) 
                
        # Filtro de filas sin código o nombre, que no tienen sentido para la búsqueda
        if not codigo or not nombre_raw: 
            continue
                
        # Verificamos si la imagen ya existe para evitar búsquedas innecesarias
        ruta_img = os.path.join(output_dir, f"{codigo}.jpg")
        if os.path.exists(ruta_img): 
            continue 
                
        # Limpiamos el nombre y construimos la búsqueda con contexto comercial
        nombre_con_contexto = limpiar_nombre_erp(nombre_raw)
        busqueda = f"{nombre_con_contexto} {marca_raw}".strip()
                
        print(f"[*] Buscando [{codigo}]: {busqueda}...", end=" ", flush=True)
                
        decargar_imagen_bing(driver, ruta_img, busqueda)


def filtrar_marcas(marca_raw):
    """
    Filtro de Marcas Genéricas que no aportan valor a la búsqueda y pueden 
    generar ruido o bloqueos en Selenium por parte de la web.

    Args:
        marca_raw (str): Nombre de la marca sin procesar.

    Returns:
        str: Nombre de la marca válido o cadena vacía si es genérica.
    """
    marcas_ignoradas = ['MARCAS VARIAS', 'MARCA VARIA', 'GENERICO', 'SIN MARCA', 'AFT']
    if marca_raw.upper() in marcas_ignoradas:
        marca_raw = ''
    return marca_raw


def limpiar_nombre_erp(texto):
    """
    Limpia el nombre, repara el rombo corrupto de Excel e inyecta contexto.

    Args:
        texto (str): Nombre en crudo extraído del ERP.

    Returns:
        str: Texto estructurado y optimizado para la búsqueda.
    """
    texto = str(texto).upper().split('..')[0]
    
    # 1. Limpieza de acentos raros del ERP
    texto = remplazo(texto)
        
    # 2. CONTEXTO COMERCIAL EXTREMO (Anti-PDFs y Anti-Coches)
    contexto = contexto_comercial(texto)
        
    # 3. Limpieza de símbolos y palabras basura
    return limpieza(texto, contexto)


def remplazo(texto):
    """
    Reemplaza caracteres extraños y acentos comunes originados por mala codificación.

    Args:
        texto (str): Texto a limpiar.

    Returns:
        str: Texto con los caracteres reemplazados.
    """
    reemplazos = {'Ì': 'I', 'Ï': 'I', 'Ö': 'O', 'Ä': 'A', '—': '-', 'Í': 'I', 'Ã': 'A', '±': '-', 'Â': 'A', 'Ç': 'C', 'Ñ': 'Ñ', 'Ó': 'O', 'Ú': 'U', 'É': 'E', 'Ü': 'U', 'À': 'A'}
    for k, v in reemplazos.items():
        texto = texto.replace(k, v)
    return texto


def contexto_comercial(texto):
    """
    Asigna un bloque de texto contextual para enfocar mejor la búsqueda 
    y evitar falsos positivos en los motores de búsqueda de imágenes.

    Args:
        texto (str): Nombre del artículo.

    Returns:
        str: Palabras clave de contexto comercial.
    """
    contexto = "comprar" 
    
    if "SIERRA" in texto or "MOTOSIERRA" in texto:
        contexto = "herramienta motosierra comprar"
    elif "MOTOAZADA" in texto or "MOTOCULTOR" in texto:
        contexto = "maquinaria agricola comprar"
    elif "BOMBA" in texto:
        contexto = "agua fontaneria comprar"
    elif "LITIO" in texto or "GRASA" in texto:
        contexto = "bote grasa lubricante comprar"
    elif "ADBLUE" in texto:
        contexto = "garrafa adblue comprar"
    elif "REFRIG" in texto or "ANTICONGELANTE" in texto or "B2000" in texto:
        contexto = "garrafa anticongelante refrigerante motor comprar"
    return contexto


def limpieza(texto, contexto):
    """
    Filtra palabras que no aportan valor y adjunta el contexto comercial al final.

    Args:
        texto (str): Texto base a filtrar.
        contexto (str): Texto de contexto comercial a añadir.

    Returns:
        str: Cadena final lista para ser buscada en Bing.
    """
    texto = re.sub(r'[%.\(\)]', ' ', texto)
    basura = {'LTS', 'GR', 'REFRIG', 'INCLUIDA', 'SI', 'APORTACIO', 'APORTACION', 'CON', 'X', 'KGS', 'CC', 'ML'}
    palabras = [p for p in texto.split() if p not in basura and len(p) > 1]
    
    resultado = " ".join(palabras).strip()
    return f"{resultado} {contexto}".strip()


def decargar_imagen_bing(driver, ruta_img, busqueda):
    """
    Intenta cargar la página de resultados de Bing Images y descargar 
    la primera imagen válida encontrada.

    Args:
        driver (uc.Chrome): Instancia del navegador.
        ruta_img (str): Ruta local donde se almacenará el archivo.
        busqueda (str): Cadena de texto enviada al buscador.
    """
    try:
        build_url(driver, busqueda) 
        imagenes = driver.find_elements(By.CSS_SELECTOR, "img.mimg")
        src_valido = buscar_http(imagenes)
        comprobar_src(ruta_img, src_valido)

    except Exception:
        print(f"Error cargando la página.")
                
    time.sleep(1)


def build_url(driver, busqueda):
    """
    Construye la URL de búsqueda en Bing Images con el contexto comercial incluido y navega.

    Args:
        driver (uc.Chrome): Instancia del navegador.
        busqueda (str): Cadena de texto a buscar.
    """
    url_busqueda = f"https://www.bing.com/images/search?q={busqueda}+producto"
    driver.get(url_busqueda)
    time.sleep(2)
        

def buscar_http(imagenes):
    """
    Busca la primera imagen que tenga un src válido (http) para evitar bloqueos.

    Args:
        imagenes (list): Lista de WebElements que contienen las etiquetas img.

    Returns:
        str | None: Enlace HTTP válido o None si no se encuentra.
    """
    src_valido = None
    for img_el in imagenes:
        enlace = img_el.get_attribute('src') or img_el.get_attribute('data-src')
        if enlace and enlace.startswith('http'):
            src_valido = enlace
            break
    return src_valido


def comprobar_src(ruta_img, src_valido):
    """
    Comprueba si se encontró un src válido antes de intentar descargar la imagen.

    Args:
        ruta_img (str): Ruta destino del archivo.
        src_valido (str | None): Enlace detectado de la imagen.
    """
    if src_valido:
        respuesta = requests.get(src_valido, timeout=5)
        procesar_imagen(ruta_img, respuesta)
    else:
        print("Sin resultados.")


def procesar_imagen(ruta_img, respuesta):
    """
    Procesa la imagen con PIL para asegurar calidad y formato correcto, 
    además de manejar posibles bloqueos de descarga.

    Args:
        ruta_img (str): Ruta donde guardar la imagen.
        respuesta (requests.Response): Objeto de respuesta HTTP.
    """
    if respuesta.status_code == 200:
        img = Image.open(BytesIO(respuesta.content)).convert("RGB")
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        img.save(ruta_img, "JPEG", optimize=True, quality=85)
        print("OK!")
    else:
        print("Descarga bloqueada por la web.")


if __name__ == "__main__":
    ejecutor_imagenes_opera()