# 🤖 Image Scraper Automation (Bulk Downloader Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la búsqueda y descarga masiva de imágenes de productos usando Selenium, Undetected Chromedriver y el motor de búsqueda Bing Images.

## 📋 Descripción

Diseñado para departamentos de e-commerce o gestión de inventarios que necesitan poblar sus bases de datos con imágenes reales. El sistema usa el patrón **Productor/Consumidor**: el navegador extrae URLs (productor) mientras un pool de hilos descarga en paralelo (consumidores), logrando una velocidad 3-5x superior a la descarga secuencial.

* **Limpieza de ruido:** Elimina caracteres especiales de exportaciones ERP (códigos internos, paréntesis, porcentajes).
* **Contexto SEO configurable:** Añade palabras clave por categoría para evitar resultados irrelevantes. Totalmente editable desde el bloque de configuración.
* **Optimización de imagen:** Redimensiona a 1600px máximo y comprime en JPEG para uso directo en web.
* **Tolerancia a fallos y reanudación:** Si una imagen ya existe en disco, se salta automáticamente. Los fallos se registran en `productos_sin_imagen.txt`.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/`.

## 🛠️ Requisitos e Instalación

Instala todas las dependencias con el archivo incluido:

```bash
pip install -r requirements.txt
```

O manualmente solo las de ejecución:

```bash
pip install undetected-chromedriver selenium requests Pillow loguru
```

*(Opcional)* Solo documentación MkDocs:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar los parámetros operativos. Los valores de configuración hardcodeados como `CONTEXTOS_CATEGORIA`, `MARCAS_IGNORADAS` y `COL_*` siguen editándose directamente en el código (son específicos de cada proyecto).

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores relevantes:

   ```env
   # Ruta al ejecutable del navegador (opcional si tienes Opera GX en Windows)
   BROWSER_BINARY_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

   # Nombre del CSV de entrada
   ARCHIVO_CSV=tu_inventario.csv

   # Carpeta donde se guardan las imágenes
   DIRECTORIO_SALIDA=imagenes_descargadas
   ```

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `BROWSER_BINARY_PATH` | NO | Auto Opera GX | Ruta al ejecutable del navegador |
| `WORKERS_DESCARGA` | NO | `6` | Hilos paralelos de descarga |
| `RESOLUCION_MINIMA` | NO | `200` | Píxeles mínimos para aceptar imagen |
| `DELAY_NAVEGADOR` | NO | `1.2` | Segundos entre búsquedas en Bing |
| `TIMEOUT_IMAGEN` | NO | `12` | Timeout HTTP por imagen (segundos) |
| `MAX_INTENTOS_URL` | NO | `5` | URLs de Bing a probar por producto |
| `ARCHIVO_CSV` | NO | `tu_inventario.csv` | Nombre del CSV de entrada |
| `DIRECTORIO_SALIDA` | NO | `imagenes_descargadas` | Carpeta de salida de imágenes |

## 📄 Especificaciones del CSV

### Formato Técnico

* **Nombre por defecto:** `tu_inventario.csv` (configurable via `ARCHIVO_CSV` en `.env`).
* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** Coma (`,`).
* **Codificación:** `UTF-8 con BOM` (recomendado si exportas desde Excel).

### Estructura de Columnas

Los nombres de columna son configurables mediante las constantes `COL_*` al inicio del script:

| Constante | Valor por defecto | Función |
| --- | --- | --- |
| `COL_REFERENCIA` | `REF` | Identificador único. Se usa como nombre del archivo `.jpg`. |
| `COL_NOMBRE` | `LABEL` | Nombre del producto para la búsqueda en Bing. |
| `COL_MARCA` | `MARCA` | (Opcional) Marca del producto. |
| `COL_CATEGORIA` | `CATEGORIA` | (Opcional) Categoría para enriquecer la búsqueda. |

## 🔧 Configuración avanzada (en el código)

### Contexto SEO por Categoría

Edita el diccionario `CONTEXTOS_CATEGORIA` en el script para afinar las búsquedas según tu sector:

```python
# Ejemplo para tienda de mascotas
CONTEXTOS_CATEGORIA = {
    'PERROS': 'producto perro mascota',
    'GATOS':  'producto gato mascota',
}

# Ejemplo para moda
CONTEXTOS_CATEGORIA = {
    'CAMISETAS': 'camiseta ropa moda fotografía catálogo',
    'PANTALONES': 'pantalón ropa moda fotografía catálogo',
}
```

Si una categoría no está en el diccionario, se usa `CONTEXTO_DEFECTO = "producto"`.

### Marcas a ignorar

```python
MARCAS_IGNORADAS = {"SIN MARCA", "GENERICA", "GENÉRICA", "MARCAS VARIAS"}
```

## 🚀 Cómo ponerlo en marcha

1. Coloca tu CSV de inventario en el mismo directorio que el script.
2. Configura el archivo `.env` con la ruta de tu navegador y nombre de CSV.
3. Ajusta `CONTEXTOS_CATEGORIA` y `COL_*` en el script según tu caso.
4. Ejecuta el script:

```bash
python img_downloader.py
```

**Resultado:** Se creará la carpeta de salida con las imágenes nombradas por su referencia (ej: `12345.jpg`). Los productos sin imagen quedan registrados en `productos_sin_imagen.txt`. Si relanzas el script, los productos con imagen ya descargada se saltan automáticamente.

## 📊 Sistema de Logging

Los logs se escriben en dos destinos simultáneamente:

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/img_downloader_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** Código escrito bajo la filosofía *Clean Code*. Módulos aislados y documentados bajo los estándares de `pydoc` para su renderizado web automático con MkDocs.

---

# 🤖 Image Scraper Automation (Bulk Downloader Edition)

Advanced automation module developed by **BenjaminDTS** for bulk searching and downloading product images using Selenium, Undetected Chromedriver, and the Bing Images search engine.

## 📋 Description

Designed for e-commerce or inventory management departments that need to populate their databases with real images. The system uses a **Producer/Consumer** pattern: the browser extracts URLs (producer) while a thread pool downloads in parallel (consumers), achieving 3-5x faster speeds than sequential downloading.

* **Noise cleaning:** Removes special characters from ERP exports (internal codes, parentheses, percentages).
* **Configurable SEO context:** Adds category-specific keywords to avoid irrelevant results. Fully editable from the configuration block.
* **Image optimization:** Resizes to 1600px maximum and compresses to JPEG for direct web use.
* **Fault tolerance and resumption:** If an image already exists on disk, it is automatically skipped. Failures are logged in `productos_sin_imagen.txt`.
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/`.

## 🛠️ Requirements and Installation

Install all dependencies using the included file:

```bash
pip install -r requirements.txt
```

Or manually, only the runtime ones:

```bash
pip install undetected-chromedriver selenium requests Pillow loguru
```

*(Optional)* Only for MkDocs documentation:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage operational parameters. Hardcoded configuration values like `CONTEXTOS_CATEGORIA`, `MARCAS_IGNORADAS`, and `COL_*` are still edited directly in the code (they are project-specific).

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the relevant values:

   ```env
   # Browser executable path (optional if you have Opera GX on Windows)
   BROWSER_BINARY_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe

   # Input CSV filename
   ARCHIVO_CSV=tu_inventario.csv

   # Output folder for downloaded images
   DIRECTORIO_SALIDA=imagenes_descargadas
   ```

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BROWSER_BINARY_PATH` | NO | Auto Opera GX | Path to the browser executable |
| `WORKERS_DESCARGA` | NO | `6` | Parallel download threads |
| `RESOLUCION_MINIMA` | NO | `200` | Minimum pixels to accept an image |
| `DELAY_NAVEGADOR` | NO | `1.2` | Seconds between Bing searches |
| `TIMEOUT_IMAGEN` | NO | `12` | HTTP timeout per image (seconds) |
| `MAX_INTENTOS_URL` | NO | `5` | Bing URLs to try per product |
| `ARCHIVO_CSV` | NO | `tu_inventario.csv` | Input CSV filename |
| `DIRECTORIO_SALIDA` | NO | `imagenes_descargadas` | Image output folder |

## 📄 CSV Specifications

### Technical Format

* **Default name:** `tu_inventario.csv` (configurable via `ARCHIVO_CSV` in `.env`).
* **Location:** Same folder as the script.
* **Delimiter:** Comma (`,`).
* **Encoding:** `UTF-8 with BOM` (recommended when exporting from Excel).

### Column Structure

Column names are configurable via the `COL_*` constants at the top of the script:

| Constant | Default value | Function |
| --- | --- | --- |
| `COL_REFERENCIA` | `REF` | Unique identifier. Used as the `.jpg` filename. |
| `COL_NOMBRE` | `LABEL` | Product name used for the Bing search. |
| `COL_MARCA` | `MARCA` | (Optional) Product brand. |
| `COL_CATEGORIA` | `CATEGORIA` | (Optional) Category to enrich the search query. |

## 🔧 Advanced configuration (in code)

### SEO Context by Category

Edit the `CONTEXTOS_CATEGORIA` dictionary in the script to refine searches for your industry:

```python
# Pet store example
CONTEXTOS_CATEGORIA = {
    'DOGS': 'dog pet product',
    'CATS': 'cat pet product',
}

# Fashion example
CONTEXTOS_CATEGORIA = {
    'T-SHIRTS': 'tshirt clothing fashion photography catalog',
    'PANTS':    'pants clothing fashion photography catalog',
}
```

If a category is not in the dictionary, `CONTEXTO_DEFECTO = "producto"` is used as a fallback.

### Ignored Brands

```python
MARCAS_IGNORADAS = {"SIN MARCA", "GENERICA", "GENÉRICA", "MARCAS VARIAS"}
```

## 🚀 How to get it up and running

1. Place your inventory CSV in the same directory as the script.
2. Configure the `.env` file with your browser path and CSV filename.
3. Adjust `CONTEXTOS_CATEGORIA` and `COL_*` in the script for your use case.
4. Run the script:

```bash
python img_downloader.py
```

**Result:** An output folder will be created with images named by their reference (e.g., `12345.jpg`). Products without an image are logged in `productos_sin_imagen.txt`. If you rerun the script, products with already-downloaded images are automatically skipped.

## 📊 Logging System

Logs are written to two destinations simultaneously:

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/img_downloader_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** Code written under the *Clean Code* philosophy. Isolated modules documented under `pydoc` standards for automatic web rendering with MkDocs.
