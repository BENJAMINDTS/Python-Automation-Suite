"""
Descargador Masivo de Imágenes — Patrón Productor/Consumidor.

Busca imágenes de productos en Bing Images y las descarga en paralelo
usando un pool de hilos. El navegador (productor) extrae URLs; los workers
HTTP (consumidores) descargan y validan cada imagen sin bloquear la búsqueda.
Resultado esperado: 3-5x más rápido que una versión secuencial.

Configura las constantes del bloque CONFIGURACIÓN antes de ejecutar.

:author: BenjaminDTS
:version: 1.2.0
"""

import os
import sys
import csv
import re
import json
import time
import getpass
import requests
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from PIL import Image
from io import BytesIO

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError as err:
    print(f"[!] Dependencia faltante: {err}")
    sys.exit(1)


# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────

# Parámetros de descarga
WORKERS_DESCARGA  = 6      # Hilos paralelos de descarga (sube si tienes buena conexión)
RESOLUCION_MINIMA = 200    # Píxeles mínimos (ancho y alto) para aceptar una imagen
DELAY_NAVEGADOR   = 1.2    # Segundos entre búsquedas en Bing (no bajar de 1.0)
TIMEOUT_IMAGEN    = 12     # Segundos máximos por request HTTP de imagen
MAX_INTENTOS_URL  = 5      # Resultados de Bing a probar por producto
COLA_MAX          = 50     # Tamaño máximo de la cola entre productor y consumidores

# Archivos
ARCHIVO_CSV       = "tu_inventario.csv"      # Nombre del CSV de entrada
DIRECTORIO_SALIDA = "imagenes_descargadas"   # Carpeta donde se guardan las imágenes
LOG_MINIATURAS    = "registro_miniaturas.txt"
LOG_ERRORES       = "productos_sin_imagen.txt"

# Columnas del CSV — ajusta a los nombres reales de tu archivo
COL_REFERENCIA = "REF"        # Identificador único (se usará como nombre del archivo .jpg)
COL_NOMBRE     = "LABEL"      # Nombre del producto para la búsqueda en Bing
COL_MARCA      = "MARCA"      # (Opcional) Marca del producto
COL_CATEGORIA  = "CATEGORIA"  # (Opcional) Categoría para enriquecer la búsqueda

# Contexto SEO por categoría
# Clave : valor de COL_CATEGORIA en MAYÚSCULAS
# Valor : palabras clave que se añaden a la búsqueda en Bing
#
# Ejemplo para tienda de mascotas:
#   CONTEXTOS_CATEGORIA = {
#       'PERROS': 'producto perro mascota',
#       'GATOS':  'producto gato mascota',
#       'AVES':   'producto pájaro ave mascota',
#   }
#
# Ejemplo para moda:
#   CONTEXTOS_CATEGORIA = {
#       'CAMISETAS': 'camiseta ropa moda fotografía catálogo',
#       'PANTALONES': 'pantalón ropa moda fotografía catálogo',
#   }
CONTEXTOS_CATEGORIA: dict = {}
CONTEXTO_DEFECTO = "producto"  # Fallback cuando la categoría no está en el diccionario

# Marcas que se ignoran al construir la query (no aportan contexto útil a Bing)
MARCAS_IGNORADAS = {
    "SIN MARCA", "GENERICA", "GENÉRICA", "MARCAS VARIAS",
}

# ─── SEÑAL DE FIN DE COLA ─────────────────────────────────────────────────────
_FIN = object()


# ═══════════════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════════════════
def ejecutor_rapido(archivo_csv: str = ARCHIVO_CSV) -> None:
    """
    Orquesta el proceso completo: carga el CSV, lanza los workers de descarga
    y el productor de URLs (navegador), y muestra el resumen final.

    Args:
        archivo_csv: Ruta o nombre del archivo CSV con el inventario de productos.
    """
    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)
    _escribir_log(
        LOG_MINIATURAS,
        f"\n--- NUEVA EJECUCIÓN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n",
    )

    print("=" * 65)
    print("  DESCARGADOR MASIVO DE IMÁGENES — PRODUCTOR/CONSUMIDOR")
    print(f"  Hilos de descarga paralela : {WORKERS_DESCARGA}")
    print(f"  Carpeta de salida          : {DIRECTORIO_SALIDA}/")
    print("=" * 65)

    ruta_csv  = _resolver_csv(archivo_csv)
    productos = _cargar_productos(ruta_csv, DIRECTORIO_SALIDA)
    print(f"[i] Productos a procesar: {len(productos)}")

    if not productos:
        print("[i] Todas las imágenes ya existen. Nada que hacer.")
        return

    cola    = Queue(maxsize=COLA_MAX)
    stats   = {"ok": 0, "error": 0}
    lock    = threading.Lock()
    futures = []
    t_inicio = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS_DESCARGA, thread_name_prefix="descarga") as pool:

        for _ in range(WORKERS_DESCARGA):
            futures.append(pool.submit(
                _consumidor, cola, stats, lock, LOG_MINIATURAS, LOG_ERRORES
            ))

        driver = None
        try:
            driver = _iniciar_navegador()
            total  = len(productos)

            for i, producto in enumerate(productos, 1):
                pct = i / total * 100
                codigo, nombre, marca, categoria = producto

                print(f"[{i}/{total} {pct:.0f}%] Buscando: {nombre[:45]}...", end=" ", flush=True)

                urls = _extraer_urls_bing(driver, nombre, marca, categoria)

                if urls:
                    print(f"-> {len(urls)} URLs en cola")
                    cola.put({
                        "codigo":     codigo,
                        "nombre":     nombre,
                        "urls":       urls,
                        "output_dir": os.path.join(DIRECTORIO_SALIDA, f"{sanitizar(codigo)}.jpg"),
                    })
                else:
                    print("Sin URLs")
                    with lock:
                        stats["error"] += 1
                    _escribir_log(LOG_ERRORES, f"{codigo}\t{nombre}\n")

                time.sleep(DELAY_NAVEGADOR)

        finally:
            cerrar_navegador(driver)
            for _ in range(WORKERS_DESCARGA):
                cola.put(_FIN)

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"[!] Worker error: {e}")

    _imprimir_resumen(stats, time.time() - t_inicio)


# ═══════════════════════════════════════════════════════════════════════════════
#  PRODUCTOR — extrae URLs desde Bing Images
# ═══════════════════════════════════════════════════════════════════════════════
def _extraer_urls_bing(driver, nombre: str, marca: str, categoria: str) -> list:
    """
    Navega a Bing Images y extrae hasta MAX_INTENTOS_URL candidatos.

    Args:
        driver:    Instancia de undetected_chromedriver.
        nombre:    Nombre del producto.
        marca:     Marca del producto (puede ser cadena vacía).
        categoria: Categoría del producto para el contexto SEO.

    Returns:
        Lista de tuplas (url_hd, url_miniatura).
    """
    query = _construir_query(nombre, marca, categoria)
    try:
        url_busqueda = f"https://www.bing.com/images/search?q={requests.utils.quote(query)}"
        driver.get(url_busqueda)

        try:
            WebDriverWait(driver, 4).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.iusc"))
            )
        except Exception:
            pass

        elementos = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
        urls = []

        for el in elementos[:MAX_INTENTOS_URL]:
            meta = el.get_attribute("m")
            if not meta:
                continue
            try:
                datos = json.loads(meta)
                hd    = datos.get("murl", "")
                mini  = datos.get("turl", "")
                if hd.startswith("http"):
                    urls.append((hd, mini))
            except json.JSONDecodeError:
                continue

        return urls

    except Exception as e:
        print(f"[!] Error Bing: {e}", end=" ")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSUMIDOR — descarga imágenes en paralelo
# ═══════════════════════════════════════════════════════════════════════════════
def _consumidor(cola, stats, lock, log_miniaturas: str, log_errores: str) -> None:
    """
    Worker de descarga. Coge tareas de la cola y descarga imágenes via requests.
    No usa Selenium — es puro I/O de red, paralelizable sin problema.
    """
    while True:
        try:
            tarea = cola.get(timeout=30)
        except Empty:
            break

        if tarea is _FIN:
            break

        codigo   = tarea["codigo"]
        nombre   = tarea["nombre"]
        urls     = tarea["urls"]
        ruta_img = tarea["output_dir"]

        exito = False
        for url_hd, url_mini in urls:
            if _descargar_y_guardar(ruta_img, url_hd):
                exito = True
                break
            if url_mini and _descargar_y_guardar(ruta_img, url_mini):
                _escribir_log(log_miniaturas, f"{codigo}\n")
                exito = True
                break

        with lock:
            if exito:
                stats["ok"] += 1
                print(f"    OK: {os.path.basename(ruta_img)}")
            else:
                stats["error"] += 1
                _escribir_log(log_errores, f"{codigo}\t{nombre}\n")
                print(f"    Sin imagen: {codigo}")

        cola.task_done()


# ═══════════════════════════════════════════════════════════════════════════════
#  DESCARGA HTTP
# ═══════════════════════════════════════════════════════════════════════════════
_CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept":     "image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer":    "https://www.bing.com/",
}


def _descargar_y_guardar(ruta_img: str, url: str) -> bool:
    """Descarga una URL y delega el guardado. Devuelve True si tuvo éxito."""
    try:
        resp = requests.get(url, headers=_CABECERAS, timeout=TIMEOUT_IMAGEN)
        if resp.status_code != 200:
            return False
        return _guardar_imagen(ruta_img, resp.content)
    except Exception:
        return False


def _guardar_imagen(ruta_img: str, contenido: bytes) -> bool:
    """
    Valida resolución mínima, redimensiona a 1600px máx. y guarda como JPEG.

    Args:
        ruta_img:  Ruta completa del archivo de salida.
        contenido: Bytes crudos de la imagen descargada.

    Returns:
        True si la imagen superó el filtro de resolución y se guardó correctamente.
    """
    try:
        img = Image.open(BytesIO(contenido)).convert("RGB")
        w, h = img.size
        if w < RESOLUCION_MINIMA or h < RESOLUCION_MINIMA:
            return False
        img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        img.save(ruta_img, "JPEG", optimize=True, quality=95)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  QUERY
# ═══════════════════════════════════════════════════════════════════════════════
def _construir_query(nombre: str, marca: str, categoria: str) -> str:
    """
    Construye la query de búsqueda para Bing Images.

    Limpia el nombre del producto (caracteres especiales, códigos internos de ERP),
    añade la marca si está disponible y adjunta el contexto SEO de la categoría
    definido en CONTEXTOS_CATEGORIA.

    Args:
        nombre:    Nombre del producto (puede contener caracteres de exportación ERP).
        marca:     Marca del producto (cadena vacía si no aplica).
        categoria: Categoría del producto.

    Returns:
        Cadena de búsqueda limpia y optimizada para Bing Images.
    """
    nombre_limpio = re.sub(r'[%\(\)\[\]{}]', ' ', nombre)
    nombre_limpio = re.sub(r'\b[A-Z]\d{2,4}\b', '', nombre_limpio)
    nombre_limpio = re.sub(r'\s+', ' ', nombre_limpio).strip()

    contexto = CONTEXTOS_CATEGORIA.get(categoria.upper(), CONTEXTO_DEFECTO)
    partes = [nombre_limpio]
    if marca:
        partes.append(marca)
    partes.append(contexto)

    return re.sub(r'\s+', ' ', ' '.join(partes)).strip()


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════
def _cargar_productos(ruta_csv: str, output_dir: str) -> list:
    """
    Lee el CSV, normaliza las cabeceras a mayúsculas y filtra los productos
    que ya tienen imagen descargada (reanudación automática).

    Args:
        ruta_csv:   Ruta al archivo CSV de entrada.
        output_dir: Carpeta de salida donde buscar imágenes ya existentes.

    Returns:
        Lista de tuplas (codigo, nombre, marca, categoria) pendientes de descarga.
    """
    productos = []
    col_ref = COL_REFERENCIA.upper()
    col_nom = COL_NOMBRE.upper()
    col_mar = COL_MARCA.upper()
    col_cat = COL_CATEGORIA.upper()

    with open(ruta_csv, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [c.strip().upper() for c in reader.fieldnames]
        for fila in reader:
            codigo = _fix_exp(fila.get(col_ref, ''))
            nombre = fila.get(col_nom, '').strip()
            marca  = _filtrar_marca(fila.get(col_mar, '').strip())
            cat    = fila.get(col_cat, '').strip()
            if not codigo or not nombre:
                continue
            ruta = os.path.join(output_dir, f"{sanitizar(codigo)}.jpg")
            if not os.path.exists(ruta):
                productos.append((codigo, nombre, marca, cat))
    return productos


def _iniciar_navegador():
    """
    Inicia undetected_chromedriver usando el ejecutable configurado.

    La ruta al navegador se lee de la variable de entorno BROWSER_BINARY_PATH.
    Si no está definida, se intenta autodetectar Opera GX en Windows como
    fallback. Si tampoco existe, ChromeDriver usará el Chrome del sistema.

    Returns:
        Instancia de undetected_chromedriver lista para usar.
    """
    options = uc.ChromeOptions()
    ruta_navegador = os.environ.get("BROWSER_BINARY_PATH", "")

    if not ruta_navegador:
        # Fallback: autodetección de Opera GX en Windows
        usuario = getpass.getuser()
        ruta_navegador = rf"C:\Users\{usuario}\AppData\Local\Programs\Opera GX\opera.exe"

    if os.path.exists(ruta_navegador):
        options.binary_location = ruta_navegador

    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-notifications')
    options.add_argument('--mute-audio')
    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver


def cerrar_navegador(driver) -> None:
    """Cierra el navegador de forma segura, suprimiendo errores del destructor."""
    if driver:
        try:
            if hasattr(driver.__class__, '__del__'):
                setattr(driver.__class__, '__del__', lambda self: None)
            driver.quit()
        except Exception:
            pass


def _resolver_csv(nombre: str) -> str:
    """Busca el CSV en el directorio actual y en el directorio padre."""
    for ruta in [os.path.abspath(nombre), os.path.abspath(os.path.join(os.pardir, nombre))]:
        if os.path.exists(ruta):
            return ruta
    raise FileNotFoundError(f"No se encontró '{nombre}'")


def _fix_exp(valor: str) -> str:
    """Corrige notación científica (ej: '1.23E+4') que Excel introduce en IDs numéricos."""
    v = str(valor).strip().replace(',', '.')
    if 'E+' in v.upper():
        try:
            return str(int(float(v)))
        except ValueError:
            pass
    return v


def sanitizar(texto: str) -> str:
    """Elimina caracteres no válidos en nombres de archivo de Windows."""
    return re.sub(r'[\\/*?:"<>|]', '_', str(texto))


def _filtrar_marca(marca: str) -> str:
    """Devuelve cadena vacía si la marca está en MARCAS_IGNORADAS."""
    return '' if marca.upper() in MARCAS_IGNORADAS else marca


def _escribir_log(ruta: str, texto: str) -> None:
    """Añade texto a un archivo de log de forma segura."""
    try:
        with open(ruta, 'a', encoding='utf-8') as f:
            f.write(texto)
    except Exception:
        pass


def _imprimir_resumen(stats: dict, duracion: float) -> None:
    """Imprime el resumen final de la ejecución."""
    total = stats['ok'] + stats['error']
    mins  = int(duracion // 60)
    segs  = int(duracion % 60)
    vpm   = total / (duracion / 60) if duracion > 0 else 0
    print(f"\n{'='*65}")
    print(f"  RESUMEN")
    print(f"  Descargadas correctamente : {stats['ok']}")
    print(f"  Sin imagen                : {stats['error']}")
    print(f"  Tiempo total              : {mins}m {segs}s")
    print(f"  Velocidad media           : {vpm:.1f} productos/minuto")
    print(f"{'='*65}")


if __name__ == "__main__":
    ejecutor_rapido(archivo_csv=ARCHIVO_CSV)
