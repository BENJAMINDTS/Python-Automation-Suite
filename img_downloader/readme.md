# 🤖 Image Scraper Automation (Bulk Downloader Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la búsqueda y descarga masiva de imágenes de productos usando Selenium, Undetected Chromedriver y el motor de búsqueda Bing Images.

## 📋 Descripción

Diseñado para departamentos de e-commerce o gestión de inventarios que necesitan poblar sus bases de datos con imágenes reales. El sistema usa el patrón **Productor/Consumidor**: el navegador extrae URLs (productor) mientras un pool de hilos descarga en paralelo (consumidores), logrando una velocidad 3-5x superior a la descarga secuencial.

* **Limpieza de ruido:** Elimina caracteres especiales de exportaciones ERP (códigos internos, paréntesis, porcentajes).
* **Contexto SEO configurable:** Añade palabras clave por categoría para evitar resultados irrelevantes. Totalmente editable desde el bloque de configuración.
* **Optimización de imagen:** Redimensiona a 1600px máximo y comprime en JPEG para uso directo en web.
* **Tolerancia a fallos y reanudación:** Si una imagen ya existe en disco, se salta automáticamente. Los fallos se registran en `productos_sin_imagen.txt`.

## 🛠️ Requisitos e Instalación

Instala todas las dependencias con el archivo incluido:

```bash
pip install -r requeriments.txt
```

O manualmente solo las de ejecución:

```bash
pip install undetected-chromedriver selenium requests Pillow
```

*(Opcional)* Solo documentación MkDocs:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## 📄 Especificaciones del CSV

### Formato Técnico

* **Nombre por defecto:** `tu_inventario.csv` (configurable en `ARCHIVO_CSV`).
* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** Coma (`,`).
* **Codificación:** `UTF-8 con BOM` (recomendado si exportas desde Excel).

### Estructura de Columnas

Los nombres de columna son totalmente configurables mediante las constantes `COL_*` al inicio del script:

| Constante | Valor por defecto | Función |
| --- | --- | --- |
| `COL_REFERENCIA` | `REF` | Identificador único. Se usa como nombre del archivo `.jpg`. |
| `COL_NOMBRE` | `LABEL` | Nombre del producto para la búsqueda en Bing. |
| `COL_MARCA` | `MARCA` | (Opcional) Marca del producto. |
| `COL_CATEGORIA` | `CATEGORIA` | (Opcional) Categoría para enriquecer la búsqueda. |

## ⚙️ Guía de Configuración

Todas las opciones se encuentran en el bloque `# ─── CONFIGURACIÓN ───` al inicio del archivo `.py`. No es necesario editar funciones.

### 1. Navegador

El script lee la ruta del ejecutable desde la variable de entorno `BROWSER_BINARY_PATH`. Si no está definida, intenta autodetectar Opera GX en Windows como fallback.

Para configurarla en Windows:

1. Busca **"Editar las variables de entorno del sistema"** en el menú Inicio.
2. En **Variables de entorno**, crea una nueva variable:
   * **Nombre:** `BROWSER_BINARY_PATH`
   * **Valor:** ruta al ejecutable de tu navegador.
     * Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe`
     * Opera GX: `C:\Users\TU_USUARIO\AppData\Local\Programs\Opera GX\opera.exe`
3. Reinicia tu terminal o IDE para que aplique los cambios.

### 2. Archivos y Carpetas

```python
ARCHIVO_CSV       = "tu_inventario.csv"     # Nombre del CSV de entrada
DIRECTORIO_SALIDA = "imagenes_descargadas"  # Carpeta de salida
```

### 3. Columnas del CSV

```python
COL_REFERENCIA = "REF"       # Ajusta al nombre real de tu columna ID
COL_NOMBRE     = "LABEL"     # Ajusta al nombre real de tu columna de producto
COL_MARCA      = "MARCA"     # Ajusta o deja como está si no aplica
COL_CATEGORIA  = "CATEGORIA" # Ajusta o deja como está si no aplica
```

### 4. Contexto SEO por Categoría

Edita el diccionario `CONTEXTOS_CATEGORIA` para afinar las búsquedas en Bing según tu sector. La clave es el valor de la columna `CATEGORIA` en mayúsculas:

```python
# Ejemplo para tienda de mascotas
CONTEXTOS_CATEGORIA = {
    'PERROS': 'producto perro mascota',
    'GATOS':  'producto gato mascota',
}

# Ejemplo para moda
CONTEXTOS_CATEGORIA = {
    'CAMISETAS':  'camiseta ropa moda fotografía catálogo',
    'PANTALONES': 'pantalón ropa moda fotografía catálogo',
}
```

Si una categoría no está en el diccionario, se usa `CONTEXTO_DEFECTO = "producto"`.

### 5. Marcas a ignorar

```python
MARCAS_IGNORADAS = {"SIN MARCA", "GENERICA", "GENÉRICA", "MARCAS VARIAS"}
```

Las marcas de esta lista no se incluyen en la query de búsqueda. Añade las que no aporten contexto en tu caso.

## 🚀 Cómo ponerlo en marcha

1. Coloca tu CSV de inventario en el mismo directorio que el script.
2. Configura las constantes del bloque `CONFIGURACIÓN` según tu caso.
3. Ejecuta el script:

```bash
python img_downloader.py
```

**Resultado:** Se creará la carpeta `imagenes_descargadas/` con las imágenes nombradas por su referencia (ej: `12345.jpg`). Los productos sin imagen quedan registrados en `productos_sin_imagen.txt`. Si relanzas el script, los productos con imagen ya descargada se saltan automáticamente.

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

## 🛠️ Requirements and Installation

Install all dependencies using the included file:

```bash
pip install -r requeriments.txt
```

Or manually, only the runtime ones:

```bash
pip install undetected-chromedriver selenium requests Pillow
```

*(Optional)* Only for MkDocs documentation:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## 📄 CSV Specifications

### Technical Format

* **Default name:** `tu_inventario.csv` (configurable via `ARCHIVO_CSV`).
* **Location:** Same folder as the script.
* **Delimiter:** Comma (`,`).
* **Encoding:** `UTF-8 with BOM` (recommended when exporting from Excel).

### Column Structure

Column names are fully configurable via the `COL_*` constants at the top of the script:

| Constant | Default value | Function |
| --- | --- | --- |
| `COL_REFERENCIA` | `REF` | Unique identifier. Used as the `.jpg` filename. |
| `COL_NOMBRE` | `LABEL` | Product name used for the Bing search. |
| `COL_MARCA` | `MARCA` | (Optional) Product brand. |
| `COL_CATEGORIA` | `CATEGORIA` | (Optional) Category to enrich the search query. |

## ⚙️ Configuration Guide

All options are in the `# ─── CONFIGURACIÓN ───` block at the top of the `.py` file. No need to edit any functions.

### 1. Browser

The script reads the browser executable path from the `BROWSER_BINARY_PATH` environment variable. If not set, it falls back to auto-detecting Opera GX on Windows.

To configure it on Windows:

1. Search for **"Edit the system environment variables"** in the Start menu.
2. Under **Environment Variables**, create a new variable:
   * **Name:** `BROWSER_BINARY_PATH`
   * **Value:** path to your browser executable.
     * Chrome: `C:\Program Files\Google\Chrome\Application\chrome.exe`
     * Opera GX: `C:\Users\YOUR_USER\AppData\Local\Programs\Opera GX\opera.exe`
3. Restart your terminal or IDE to apply the changes.

### 2. Files and Folders

```python
ARCHIVO_CSV       = "tu_inventario.csv"     # Input CSV filename
DIRECTORIO_SALIDA = "imagenes_descargadas"  # Output folder
```

### 3. CSV Columns

```python
COL_REFERENCIA = "REF"       # Adjust to your actual ID column name
COL_NOMBRE     = "LABEL"     # Adjust to your actual product name column
COL_MARCA      = "MARCA"     # Adjust or leave as-is if not applicable
COL_CATEGORIA  = "CATEGORIA" # Adjust or leave as-is if not applicable
```

### 4. SEO Context by Category

Edit the `CONTEXTOS_CATEGORIA` dictionary to refine Bing searches for your industry. The key is the `CATEGORIA` column value in uppercase:

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

### 5. Ignored Brands

```python
MARCAS_IGNORADAS = {"SIN MARCA", "GENERICA", "GENÉRICA", "MARCAS VARIAS"}
```

Brands in this set are excluded from the search query. Add any that don't provide useful context for your case.

## 🚀 How to get it up and running

1. Place your inventory CSV in the same directory as the script.
2. Configure the constants in the `CONFIGURACIÓN` block for your use case.
3. Run the script:

```bash
python img_downloader.py
```

**Result:** An `imagenes_descargadas/` folder will be created with images named by their reference (e.g., `12345.jpg`). Products without an image are logged in `productos_sin_imagen.txt`. If you rerun the script, products with already-downloaded images are automatically skipped.

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** Code written under the *Clean Code* philosophy. Isolated modules documented under `pydoc` standards for automatic web rendering with MkDocs.
