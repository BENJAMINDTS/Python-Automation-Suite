---

# 🤖 Image Scraper Automation (Clean Code Edition)

Módulo avanzado de automatización desarrollado por BenjaminDTS para la extracción, limpieza y descarga masiva de imágenes de productos utilizando Selenium, Undetected Chromedriver y el motor de búsqueda Bing.

## 📋 Descripción

Este script está diseñado para departamentos de e-commerce o gestión de inventarios que necesitan poblar sus bases de datos con imágenes reales. El sistema no solo busca el término, sino que:

* **Limpia el ruido:** Elimina caracteres extraños de exportaciones corruptas de ERP.
* **Añade contexto:** Inyecta palabras clave comerciales para evitar resultados irrelevantes (como PDFs o fotos de coches).
* **Optimiza:** Redimensiona y comprime las imágenes para su uso directo en web.
* **Tolerancia a fallos:** Sistema integrado Anti-403 con descargas de respaldo (miniaturas) y registro de errores.

## 🛠️ Requisitos e Instalación

### 1. Navegador

El script utiliza las variables de entorno de tu sistema operativo para localizar el ejecutable de tu navegador (Opera GX, Chrome, Brave, etc.) de forma segura, sin exponer rutas en el código.

### 2. Dependencias de Python

Instala las librerías necesarias ejecutando:

```bash
pip install undetected-chromedriver selenium requests Pillow

```

## 📄 Especificaciones del CSV

Para que el robot procese los datos sin errores, el archivo de entrada debe seguir estas reglas:

### Formato Técnico

* **Nombre por defecto:** `input_products.csv` (configurable en el código).
* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** Coma (`,`).
* **Codificación:** `UTF-8 con BOM` (recomendado si exportas desde Excel).

### Estructura de Columnas

El script realiza una validación de cabeceras. Las columnas esperadas por defecto son:

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **REF** | **SÍ** | Se usa como identificador y nombre del archivo final (ej: `12345.jpg`). |
| **LABEL** | **SÍ** | La descripción principal del producto para la búsqueda. |
| **MARCA** | No | Ayuda a filtrar la búsqueda ignorando marcas genéricas. |
| **CATEGORIA** | No | Añade peso contextual al motor de búsqueda. |

Ejemplo visual de los datos:

## ⚙️ Guía de Adaptación (Uso en otros casos)

Si necesitas mover este script a otro entorno o usarlo para productos distintos, ajusta lo siguiente:

### 1. Configurar la Variable de Entorno del Navegador (Windows)

Para no exponer tu usuario local en el código fuente, el script usa la variable `BROWSER_BINARY_PATH`. Sigue estos pasos para configurarla:

1. Presiona la tecla `Windows` y busca **"Editar las variables de entorno del sistema"**.
2. En la ventana que se abre, haz clic en el botón **Variables de entorno...** (abajo a la derecha).
3. En la sección **Variables del sistema** (o Variables de usuario), haz clic en **Nueva...**.
4. **Nombre de la variable:** `BROWSER_BINARY_PATH`
5. **Valor de la variable:** La ruta exacta al ejecutable de tu navegador.

* *Ejemplo Chrome:* `C:\Program Files\Google\Chrome\Application\chrome.exe`
* *Ejemplo Opera GX:* `C:\Users\TU_USUARIO\AppData\Local\Programs\Opera GX\opera.exe`

1. Haz clic en **Aceptar** en todas las ventanas y **reinicia tu terminal o IDE** (VS Code, PyCharm) para que aplique los cambios.

### 2. Adaptar el Contexto Comercial

Si tu sector no es industrial/ferretero, edita la función `generate_seo_context(text)` en el código. Por ejemplo, para una tienda de moda:

```python
def generate_seo_context(text):
    if "PANTALON" in text: 
        return "ropa moda fotografia catalogo"
    return "comprar"

```

## 🚀 Cómo ponerlo en marcha

1. Prepara tu `input_products.csv` con los productos deseados.
2. Ejecuta el script:

```bash
python scraper.py

```

**Resultado:** El script creará una carpeta llamada `output_images/`. Si una imagen ya existe, el robot la saltará automáticamente para ahorrar recursos de red. Los fallos se registrarán en `download_errors.log`.

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** El código está íntegramente comentado explicando el 'por qué' de la lógica siguiendo los estándares de pydoc (Python) para su posterior exportación a manuales técnicos. La arquitectura respeta los principios SOLID y Clean Code.

---

# 🤖 Image Scraper Automation (Clean Code Edition)

Advanced automation module developed by BenjaminDTS for extracting, cleaning, and bulk downloading product images using Selenium, Undetected Chromedriver, and the Bing search engine.

## 📋 Description

This script is designed for e-commerce or inventory management departments that need to populate their databases with real images. The system not only searches for the term but also:

* **Cleans the noise:** Removes extraneous characters from corrupted ERP exports.
* **Adds context:** Injects business keywords to avoid irrelevant results (such as PDFs or photos of cars).
* **Optimizes:** Resizes and compresses images for direct use on the web.
* **Fault tolerance:** Integrated Anti-403 system with fallback downloads (thumbnails) and error logging.

## 🛠️ Requirements and Installation

### 1. Browser

The script uses your operating system's environment variables to safely locate your browser executable (Opera GX, Chrome, Brave, etc.) without exposing local paths in the source code.

### 2. Python Dependencies

Install the necessary libraries by running:

```bash
pip install undetected-chromedriver selenium requests Pillow

```

## 📄 CSV Specifications

For the bot to process the data without errors, the input file must follow these rules:

### Technical Format

* **Default Name:** `input_products.csv` (configurable in the code).
* **Location:** Same folder as the script.
* **Delimiter:** Comma (`,`).
* **Encoding:** `UTF-8 with BOM` (recommended if exporting from Excel).

### Column Structure

The script performs strict header validation. The expected columns are:

| Header | Required | Function |
| --- | --- | --- |
| **REF** | **YES** | Used as the identifier and final file name (e.g., `12345.jpg`). |
| **LABEL** | **YES** | Main product description for the search. |
| **MARCA** | No | Helps filter the search by ignoring generic brands. |
| **CATEGORIA** | No | Adds contextual weight to the search engine query. |

Visual example of the data:

## ⚙️ Adaptation Guide (Use in other cases)

If you need to move this script to another environment or use it for different products, adjust the following:

### 1. Setting up the Browser Environment Variable (Windows)

To avoid exposing your local username in the source code, the script uses the `BROWSER_BINARY_PATH` variable. Follow these steps to configure it:

1. Press the `Windows` key and search for **"Edit the system environment variables"**.
2. In the window that opens, click the **Environment Variables...** button (bottom right).
3. Under the **System variables** (or User variables) section, click **New...**.
4. **Variable name:** `BROWSER_BINARY_PATH`
5. **Variable value:** The exact path to your browser's executable.

* *Chrome example:* `C:\Program Files\Google\Chrome\Application\chrome.exe`
* *Opera GX example:* `C:\Users\YOUR_USER\AppData\Local\Programs\Opera GX\opera.exe`

1. Click **OK** on all windows and **restart your terminal or IDE** (VS Code, PyCharm) to apply the changes.

### 2. Adapt the Business Context

If your sector is not industrial/hardware, edit the `generate_seo_context(text)` function in the code. For example, for a fashion store:

```python
def generate_seo_context(text):
    if "PANTALON" in text: 
        return "clothing fashion photography catalog"
    return "comprar"

```

## 🚀 How to get it up and running

1. Prepare your `input_products.csv` file with the desired products.
2. Run the script:

```bash
python scraper.py

```

**Result:** The script will create a folder called `output_images/`. If an image already exists, the crawler will automatically skip it to save bandwidth. Any download issues will be recorded in `download_errors.log`.

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS
* **Documentation:** The code is fully commented explaining the 'why' behind the logic following pydoc standards for later export to technical manuals. The architecture respects SOLID and Clean Code principles.

---
