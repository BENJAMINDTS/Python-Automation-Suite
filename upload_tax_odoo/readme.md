# 🛒 Odoo Pricelist & Product Importer (Turbo Caché Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la importación masiva de productos y actualización dinámica de múltiples listas de precios (Tarifas) en Odoo, utilizando su API XML-RPC y técnicas de Eager Loading.

### 📋 Descripción

Este script está diseñado para gestores de inventario e integradores de ERP que necesitan actualizar miles de precios a Odoo de forma rápida y sin colapsar el servidor. El sistema no solo inserta datos, sino que implementa:
* **Turbo Caché (Eager Loading):** Descarga el mapa de productos y reglas de precios a la memoria RAM antes de iterar el Excel. Esto previene el letal problema de consultas N+1, evitando bloqueos por exceso de peticiones.
* **Gestión de Tarifas al vuelo:** Detecta las 6 columnas de tarifas del CSV y crea las listas de precios automáticamente en Odoo si no existen.
* **Creación Automática de Productos:** Si un artículo del Excel no existe en el ERP, lo da de alta con su precio base antes de aplicarle las tarifas específicas.
* **Salida REST-Ready:** El script devuelve una respuesta estándar en JSON (`{success, data, message}`) para facilitar su integración con APIs, Cron Jobs o webhooks.

### 🛠️ Requisitos e Instalación

El núcleo del script está escrito en **Python puro**, utilizando exclusivamente librerías estándar (`xmlrpc.client`, `csv`, `json`).
* No es necesario instalar dependencias externas para ejecutar la importación.
* *(Opcional)* Si deseas compilar la documentación técnica incluida en el código fuente, instala las dependencias de MkDocs:
  ```bash
  pip install mkdocs mkdocs-material mkdocstrings[python]
  ```

### 📄 Especificaciones del CSV

Para que el script procese los datos a máxima velocidad, el archivo de entrada debe seguir estas reglas:

**Formato Técnico**

* **Nombre:** `tarifas_ejemplo.csv` (o el que configures en el script).
* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** Coma (`,`).
* **Codificación:** UTF-8-sig (Maneja correctamente los BOM de Excel).

**Estructura de Columnas**
El script busca columnas específicas para cruzar los datos. Las principales son:

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **Artículo** | SÍ | Referencia interna en Odoo (`default_code`). Clave principal de búsqueda. |
| **Nombre artículo** | SÍ | Título comercial. Usado para crear el producto si este no existe. |
| **Tarifa PVP 2**, etc. | NO | Se esperan 6 columnas de tarifas (ver código). Si la celda tiene un valor > 0, se actualiza la regla. |

### ⚙️ Guía de Configuración y Adaptación

Antes de ejecutar el script en un nuevo entorno, debes rellenar el bloque de variables genéricas en la cabecera del archivo `.py`:

* **Credenciales:**
* `URL`: La dirección de tu instancia (ej: `https://tu-dominio-odoo.com`).
* `DB`: El nombre interno de la base de datos.
* `USERNAME` / `PASSWORD`: Correo de administrador y su contraseña (o API Key).

* **Configuración del CSV:** Modifica la lista `COLUMNAS_TARIFAS` si los nombres de las cabeceras de tu Excel cambian.

### 🚀 Cómo ponerlo en marcha

1. Prepara tu archivo `.csv` en la misma raíz del proyecto.
2. Ejecuta el script:

```bash
python importador_tarifas.py

```

1. **Resultado:** Al finalizar, el script imprimirá por consola un objeto JSON confirmando el éxito de la operación o detallando cualquier error crítico capturado por el manejador global.

### 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** El código está íntegramente comentado y modularizado siguiendo los estándares *SOLID* y *Clean Code* de Python. Incluye firmas `pydoc` preparadas para ser exportadas a un portal de documentación estática mediante MkDocs.

---

# 🛒 Odoo Pricelist & Product Importer (Turbo Caché Edition)

Advanced automation module developed by **BenjaminDTS** for massive product importing and dynamic updating of multiple pricelists in Odoo, using its XML-RPC API and Eager Loading techniques.

### 📋 Description

This script is designed for inventory managers and ERP integrators who need to update thousands of prices to Odoo quickly and without crashing the server. The system not only inserts data but implements:

* **Turbo Caché (Eager Loading):** Downloads the product and pricing rules map to RAM before iterating through the Excel file. This prevents the lethal N+1 query problem, avoiding blocks due to excessive requests.
* **On-the-fly Pricelist Management:** Detects the 6 pricelist columns from the CSV and automatically creates the pricelists in Odoo if they do not exist.
* **Automatic Product Creation:** If an item from the Excel file does not exist in the ERP, it is created with its base price before applying specific pricelists.
* **REST-Ready Output:** The script returns a standard JSON response (`{success, data, message}`) to facilitate integration with APIs, Cron Jobs, or webhooks.

### 🛠️ Requirements and Installation

The core of the script is written in **pure Python**, using exclusively standard libraries (`xmlrpc.client`, `csv`, `json`).

* No external dependencies need to be installed to run the import.
* *(Optional)* If you want to compile the technical documentation included in the source code, install the MkDocs dependencies:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]

```

### 📄 CSV Specifications

For the script to process data at maximum speed, the input file must follow these rules:

**Technical Format**

* **Name:** `tarifas_ejemplo.csv` (or the one configured in the script).
* **Location:** Same folder as the script.
* **Delimiter:** Comma (`,`).
* **Encoding:** UTF-8-sig (Properly handles Excel BOMs).

**Column Structure**
The script looks for specific columns to cross-reference data. The main ones are:

| Header | Required | Function |
| --- | --- | --- |
| **Artículo** (Item) | YES | Internal reference in Odoo (`default_code`). Main search key. |
| **Nombre artículo** (Name) | YES | Commercial title. Used to create the product if it doesn't exist. |
| **Tarifa PVP 2**, etc. | NO | Expects 6 pricelist columns (see code). If the cell has a value > 0, the rule is updated. |

### ⚙️ Configuration and Adaptation Guide

Before running the script in a new environment, you must fill in the generic variables block at the top of the `.py` file:

* **Credentials:**
* `URL`: The address of your instance (e.g., `https://your-odoo-domain.com`).
* `DB`: The internal database name.
* `USERNAME` / `PASSWORD`: Administrator email and password (or API Key).

* **CSV Configuration:** Modify the `COLUMNAS_TARIFAS` list if the header names in your Excel file change.

### 🚀 How to get it up and running

1. Prepare your `.csv` file in the same root folder of the project.
2. Run the script:

```bash
python importador_tarifas.py

```

1. **Result:** Upon completion, the script will print a JSON object to the console confirming the success of the operation or detailing any critical error caught by the global handler.

### 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** The code is fully commented and modularized following Python's *SOLID* and *Clean Code* standards. It includes `pydoc` signatures ready to be exported to a static documentation portal via MkDocs.
