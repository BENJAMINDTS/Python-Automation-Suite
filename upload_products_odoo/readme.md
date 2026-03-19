# 🛒 Odoo Mass Importer Automation (XML-RPC Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la importación masiva, categorización dinámica y sincronización de imágenes de catálogos en Odoo utilizando su API XML-RPC.

## 📋 Descripción

Este script está diseñado para gestores de inventario e integradores de ERP que necesitan migrar catálogos enormes a Odoo de forma segura. El sistema no solo inserta datos, sino que:

* **Gestión de Familias al vuelo:** Detecta categorías en el Excel y las crea automáticamente en Odoo si no existen.
* **Imágenes Integradas:** Convierte las fotos locales a Base64 y las inyecta directamente en la ficha del producto.
* **Filtro de Descatalogados:** Ignora automáticamente los artículos marcados como "BAJA".
* **Sistema de Reanudación Inteligente (Anti-Cortes):** Si la red falla, al reiniciar el script omitirá los productos ya subidos para evitar duplicados y ahorrar horas de proceso.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/`.

## 🛠️ Requisitos e Instalación

```bash
pip install -r requirements.txt
```

Dependencias:

* `xmlrpc.client`, `csv`, `base64`, `os` (Nativas)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 Estructura de Archivos

```text
/upload_products_odoo
 ├── subida.py
 ├── .env.example
 ├── .env              ← crear desde .env.example (no versionar)
 ├── requirements.txt
 ├── catalogo.csv
 ├── fotos/            ← carpeta con imágenes nombradas por código (ej: 27000075.jpg)
 └── README.md
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar las credenciales de Odoo y las rutas de archivos. Nunca edites las credenciales directamente en el código fuente.

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores:

   ```env
   ODOO_URL=https://tu-dominio.odoo.com
   ODOO_DB=nombre_de_tu_base_de_datos
   ODOO_USERNAME=tu_usuario
   ODOO_PASSWORD=tu_contraseña_segura

   # Rutas de archivos
   CARPETA_FOTOS=./fotos
   ARCHIVO_CSV=catalogo.csv

   # ¡PELIGRO! True vacía el catálogo antes de importar. Solo en entornos de prueba.
   LIMPIAR_CATALOGO=False
   ```

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ODOO_URL` | SÍ | — | URL de tu instancia de Odoo |
| `ODOO_DB` | SÍ | — | Nombre de la base de datos |
| `ODOO_USERNAME` | SÍ | — | Usuario de Odoo |
| `ODOO_PASSWORD` | SÍ | — | Contraseña del usuario |
| `CARPETA_FOTOS` | SÍ | `./fotos` | Ruta a la carpeta con imágenes de productos |
| `ARCHIVO_CSV` | SÍ | `catalogo.csv` | Ruta al CSV con el catálogo |
| `LIMPIAR_CATALOGO` | NO | `False` | Si `True`, vacía todos los productos antes de importar |

## 📄 Especificaciones del CSV

### Formato Técnico

* **Delimitador:** Punto y coma (`;`).
* **Codificación:** UTF-8 con BOM (recomendado al exportar desde Excel).

### Estructura de Columnas

El script realiza una detección inteligente de cabeceras (normaliza a mayúsculas):

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **CÓDIGO** (primera col.) | SÍ | Referencia interna en Odoo. Nombre exacto de la foto (ej: `27000075.jpg`). |
| **NOMBRE** (segunda col.) | SÍ | El título comercial del producto. |
| **NOMBRE FAMILIA** | NO | Genera la jerarquía de categorías (`product.category`). |
| **BAJA** | NO | Si contiene `TRUE`, el script ignorará la fila por completo. |

## 🚀 Cómo ponerlo en marcha

1. Prepara tu CSV y asegúrate de tener las imágenes en la carpeta configurada en `CARPETA_FOTOS`.
2. Configura el archivo `.env` con las credenciales y rutas correctas.
3. Ejecuta el script:

```bash
python subida.py
```

**Resultado:** El sistema autentica, verifica existencias (reanudación automática) y sube los productos uno a uno asociándolos a su familia y fotografía.

## ⚠️ Modo Limpieza

Si cambias `LIMPIAR_CATALOGO=True` en el `.env`, el script intentará **eliminar todos los productos** de Odoo antes de importar el nuevo CSV. Si algún producto está en pedidos o facturas, los archivará (`active = False`) en lugar de eliminarlos.

**Úsalo exclusivamente en entornos de prueba.**

## 📊 Sistema de Logging

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/subida_productos_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

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
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/`.

## 🛠️ Requirements and Installation

```bash
pip install -r requirements.txt
```

Dependencies:

* `xmlrpc.client`, `csv`, `base64`, `os` (Native)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 File Structure

```text
/upload_products_odoo
 ├── subida.py
 ├── .env.example
 ├── .env              ← create from .env.example (do not commit)
 ├── requirements.txt
 ├── catalogo.csv
 ├── fotos/            ← folder with images named by code (e.g.: 27000075.jpg)
 └── README.md
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage Odoo credentials and file paths. Never edit credentials directly in the source code.

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the values:

   ```env
   ODOO_URL=https://your-domain.odoo.com
   ODOO_DB=your_database_name
   ODOO_USERNAME=your_user
   ODOO_PASSWORD=your_secure_password

   # File paths
   CARPETA_FOTOS=./fotos
   ARCHIVO_CSV=catalogo.csv

   # DANGER! True wipes the catalog before import. Only use in test environments.
   LIMPIAR_CATALOGO=False
   ```

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ODOO_URL` | YES | — | URL of your Odoo instance |
| `ODOO_DB` | YES | — | Database name |
| `ODOO_USERNAME` | YES | — | Odoo user |
| `ODOO_PASSWORD` | YES | — | User password |
| `CARPETA_FOTOS` | YES | `./fotos` | Path to the folder with product images |
| `ARCHIVO_CSV` | YES | `catalogo.csv` | Path to the catalog CSV |
| `LIMPIAR_CATALOGO` | NO | `False` | If `True`, wipes all products before importing |

## 📄 CSV Specifications

### Technical Format

* **Delimiter:** Semicolon (`;`).
* **Encoding:** UTF-8 with BOM (recommended when exporting from Excel).

### Column Structure

The script performs intelligent header detection (normalizes to uppercase):

| Header | Required | Function |
| --- | --- | --- |
| **CODE** (first col.) | YES | Internal reference in Odoo. Exact photo name (e.g., `27000075.jpg`). |
| **NAME** (second col.) | YES | The commercial title of the product. |
| **NOMBRE FAMILIA** | NO | Generates the category hierarchy (`product.category`). |
| **BAJA** | NO | If it contains `TRUE`, the script will skip the row completely. |

## 🚀 How to get it up and running

1. Prepare your CSV and make sure your images are in the folder configured in `CARPETA_FOTOS`.
2. Configure the `.env` file with the correct credentials and paths.
3. Run the script:

```bash
python subida.py
```

**Result:** The system authenticates, verifies existing records (automatic resumption), and uploads products one by one, linking them to their category and photograph.

## ⚠️ Clean Mode

If you set `LIMPIAR_CATALOGO=True` in `.env`, the script will attempt to **delete all products** from Odoo before importing the new CSV. If any product is referenced in orders or invoices, it will archive them (`active = False`) instead of deleting.

**Use exclusively in test environments.**

## 📊 Logging System

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/subida_productos_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** The code is fully commented and modularized following Python's Top-Down and Clean Code standards, ready to be exported to technical manuals via MkDocs.
