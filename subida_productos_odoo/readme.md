# 🛒 Odoo Mass Importer Automation (XML-RPC Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la importación masiva, categorización dinámica y sincronización de imágenes de catálogos en Odoo utilizando su API XML-RPC.

## 📋 Descripción

Este script está diseñado para gestores de inventario e integradores de ERP que necesitan migrar catálogos enormes a Odoo de forma segura. El sistema no solo inserta datos, sino que:
* **Gestión de Familias al vuelo:** Detecta categorías en el Excel y las crea automáticamente en Odoo si no existen.
* **Imágenes Integradas:** Convierte las fotos locales a Base64 y las inyecta directamente en la ficha del producto.
* **Filtro de Descatalogados:** Ignora automáticamente los artículos marcados como "BAJA".
* **Sistema de Reanudación Inteligente (Anti-Cortes):** Si la red falla, al reiniciar el script omitirá los productos ya subidos para evitar duplicados y ahorrar horas de proceso.

## 🛠️ Requisitos e Instalación

El núcleo del script está escrito en **Python puro**, utilizando exclusivamente librerías de la biblioteca estándar (`xmlrpc.client`, `csv`, `base64`, `os`). 

**No es necesario instalar dependencias externas para ejecutar la importación.**

*(Opcional)* Si deseas compilar la documentación técnica incluida en el código fuente, instala las dependencias de MkDocs:
```bash
pip install -r requirements.txt

```

## 📄 Especificaciones del CSV

Para que el robot procese los datos sin errores, el archivo de entrada debe seguir estas reglas:

**Formato Técnico**

* **Nombre:** `ARTÍCULOS.csv`
* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** Punto y coma (`;`).
* **Codificación:** UTF-8 con BOM (recomendado al exportar desde Excel).

**Estructura de Columnas**
El script realiza una detección inteligente de cabeceras. Las principales son:

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **CÓDIGO** | SÍ | Referencia interna en Odoo y nombre exacto de la foto (ej: `27000075.jpg`). |
| **NOMBRE** | SÍ | El título comercial del producto. |
| **NOMBRE FAMILIA** | NO | Genera la jerarquía de categorías (`product.category`). |
| **BAJA** | NO | Si contiene `TRUE`, el script ignorará la fila por completo. |

## ⚙️ Guía de Configuración y Adaptación

Antes de ejecutar el script en un nuevo entorno, debes rellenar el bloque de configuración en la cabecera del archivo `.py`:

1. **Credenciales:**

* `URL`: La dirección de tu instancia (ej: *<https://www.google.com/search?q=https://tu-empresa.odoo.com>*).
* `DB`: El nombre interno de la base de datos.
* `USERNAME` / `PASSWORD`: Correo de administrador y su contraseña (o API Key).

1. **Modo Limpieza Extrema:**
Si cambias la variable `LIMPIAR_CATALOGO = True`, el script borrará (o archivará) todo el catálogo existente en Odoo antes de importar el nuevo CSV. **Úsalo con precaución.**

## 🚀 Cómo ponerlo en marcha

1. Prepara tu archivo `ARTÍCULOS.csv` y asegúrate de tener las imágenes en la carpeta `PRODUCTOS_WEB/`.
2. Ejecuta el script:

```bash
python subir_catalogo.py

```

**Resultado:** Verás por consola cómo el sistema autentica, verifica existencias y sube los productos uno a uno asociándolos a su familia y fotografía.

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** El código está íntegramente comentado y modularizado siguiendo los estándares *Top-Down* y *Clean Code* de Python, preparado para ser exportado a manuales técnicos mediante MkDocs.

---

# 🛒 Odoo Mass Importer Automation (XML-RPC Edition)

Advanced automation module developed by **BenjaminDTS** for massive importing, dynamic categorization, and image synchronization of catalogs in Odoo using its XML-RPC API.

## 📋 Description

This script is designed for inventory managers and ERP integrators who need to migrate huge catalogs to Odoo securely. The system not only inserts data but also:

* **On-the-fly Category Management:** Detects categories in the Excel file and creates them automatically in Odoo if they do not exist.
* **Integrated Images:** Converts local photos to Base64 and injects them directly into the product record.
* **Discontinued Items Filter:** Automatically ignores items marked as "BAJA" (Discontinued).
* **Smart Resume System (Anti-Crash):** If the network fails, restarting the script will skip already uploaded products to prevent duplicates and save processing hours.

## 🛠️ Requirements and Installation

The core of the script is written in **pure Python**, using exclusively standard library modules (`xmlrpc.client`, `csv`, `base64`, `os`).

**No external dependencies need to be installed to run the import.**

*(Optional)* If you want to compile the technical documentation included in the source code, install the MkDocs dependencies:

```bash
pip install -r requirements.txt

```

## 📄 CSV Specifications

For the bot to process the data without errors, the input file must follow these rules:

**Technical Format**

* **Name:** `ARTÍCULOS.csv`
* **Location:** Same folder as the script.
* **Delimiter:** Semicolon (`;`).
* **Encoding:** UTF-8 with BOM (recommended when exporting from Excel).

**Column Structure**
The script performs intelligent header detection. The main ones are:

| Header | Required | Function |
| --- | --- | --- |
| **CODE** (CÓDIGO) | YES | Internal reference in Odoo and exact photo name (e.g., `27000075.jpg`). |
| **NAME** (NOMBRE) | YES | The commercial title of the product. |
| **CATEGORY** (NOMBRE FAMILIA) | NO | Generates the category hierarchy (`product.category`). |
| **DISCONTINUED** (BAJA) | NO | If it contains `TRUE`, the script will skip the row completely. |

## ⚙️ Configuration and Adaptation Guide

Before running the script in a new environment, you must fill in the configuration block at the top of the `.py` file:

1. **Credentials:**

* `URL`: The address of your instance (e.g., *<https://www.google.com/search?q=https://your-company.odoo.com>*).
* `DB`: The internal database name.
* `USERNAME` / `PASSWORD`: Administrator email and password (or API Key).

1. **Extreme Cleaning Mode:**
If you change the variable `LIMPIAR_CATALOGO = True`, the script will delete (or archive) the entire existing catalog in Odoo before importing the new CSV. **Use with caution.**

## 🚀 How to get it up and running

1. Prepare your `ARTÍCULOS.csv` file and make sure your images are in the `PRODUCTOS_WEB/` folder.
2. Run the script:

```bash
python subir_catalogo.py

```

**Result:** You will see in the console how the system authenticates, verifies stock, and uploads the products one by one, linking them to their category and photograph.

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** The code is fully commented and modularized following Python's Top-Down and Clean Code standards, ready to be exported to technical manuals via MkDocs.