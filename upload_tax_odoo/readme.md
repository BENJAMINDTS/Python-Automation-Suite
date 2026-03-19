# 🛒 Odoo Pricelist & Product Importer (Turbo Caché Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la importación masiva de productos y actualización dinámica de múltiples listas de precios (Tarifas) en Odoo, utilizando su API XML-RPC y técnicas de Eager Loading.

## 📋 Descripción

Este script está diseñado para gestores de inventario e integradores de ERP que necesitan actualizar miles de precios a Odoo de forma rápida y sin colapsar el servidor. El sistema no solo inserta datos, sino que implementa:

* **Turbo Caché (Eager Loading):** Descarga el mapa de productos y reglas de precios a la memoria RAM antes de iterar el Excel. Esto previene el letal problema de consultas N+1, evitando bloqueos por exceso de peticiones.
* **Gestión de Tarifas al vuelo:** Detecta las columnas de tarifas del CSV y crea las listas de precios automáticamente en Odoo si no existen.
* **Creación Automática de Productos:** Si un artículo del Excel no existe en el ERP, lo da de alta con su precio base antes de aplicarle las tarifas específicas.
* **Salida REST-Ready:** El script devuelve una respuesta estándar en JSON (`{success, data, message}`) para facilitar su integración con APIs, Cron Jobs o webhooks.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/`.

## 🛠️ Requisitos e Instalación

```bash
pip install -r requirements.txt
```

Dependencias:

* `xmlrpc.client`, `csv`, `json` (Nativas)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 Estructura de Archivos

```text
/upload_tax_odoo
 ├── importador_tarifas.py
 ├── .env.example
 ├── .env              ← crear desde .env.example (no versionar)
 ├── requirements.txt
 ├── tarifas_ejemplo.csv
 └── README.md
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar las credenciales de Odoo y la configuración del CSV. Nunca edites las credenciales directamente en el código fuente.

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores:

   ```env
   ODOO_URL=https://tu-dominio-odoo.com
   ODOO_DB=nombre_base_datos
   ODOO_USERNAME=tu_usuario@email.com
   ODOO_PASSWORD=tu_contraseña_segura

   ARCHIVO_TARIFAS=tarifas_ejemplo.csv

   # Opcional: columnas de tarifa separadas por coma
   # COLUMNAS_TARIFAS=Tarifa PVP 2,Tarifa PVP,Tarifa PVP sin Iva,Nuevos cliente,Tarifa 15,Cliente fidelizado
   ```

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ODOO_URL` | SÍ | — | URL de tu instancia de Odoo |
| `ODOO_DB` | SÍ | — | Nombre de la base de datos |
| `ODOO_USERNAME` | SÍ | — | Usuario de Odoo |
| `ODOO_PASSWORD` | SÍ | — | Contraseña del usuario |
| `ARCHIVO_TARIFAS` | SÍ | `tarifas_ejemplo.csv` | Nombre del CSV con las tarifas |
| `COLUMNAS_TARIFAS` | NO | 6 tarifas estándar | Columnas de tarifa a procesar (separadas por coma) |

### Columnas de tarifa por defecto

Si no se define `COLUMNAS_TARIFAS`, el script procesa estas 6 columnas:

```text
Tarifa PVP 2, Tarifa PVP, Tarifa PVP sin Iva, Nuevos cliente, Tarifa 15, Cliente fidelizado
```

## 📄 Especificaciones del CSV

### Formato Técnico

* **Delimitador:** Coma (`,`).
* **Codificación:** UTF-8-sig (maneja correctamente los BOM de Excel).

### Estructura de Columnas

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **Artículo** | SÍ | Referencia interna en Odoo (`default_code`). Clave principal de búsqueda. |
| **Nombre artículo** | SÍ | Título comercial. Usado para crear el producto si no existe. |
| **Tarifa PVP 2**, etc. | NO | Columnas de tarifa (configurables). Si la celda tiene valor > 0, se actualiza la regla. |

## 🚀 Cómo ponerlo en marcha

1. Prepara tu archivo `.csv` en el mismo directorio.
2. Configura el archivo `.env` con las credenciales y el nombre del CSV.
3. Ejecuta el script:

```bash
python importador_tarifas.py
```

**Resultado:** Al finalizar, el script imprime por consola un objeto JSON confirmando el éxito de la operación o detallando cualquier error crítico.

## 📊 Sistema de Logging

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/tarifas_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** El código está íntegramente comentado y modularizado siguiendo los estándares *SOLID* y *Clean Code* de Python. Incluye firmas `pydoc` preparadas para ser exportadas a un portal de documentación estática mediante MkDocs.

---

# 🛒 Odoo Pricelist & Product Importer (Turbo Caché Edition)

Advanced automation module developed by **BenjaminDTS** for massive product importing and dynamic updating of multiple pricelists in Odoo, using its XML-RPC API and Eager Loading techniques.

## 📋 Description

This script is designed for inventory managers and ERP integrators who need to update thousands of prices to Odoo quickly and without crashing the server. The system not only inserts data but implements:

* **Turbo Caché (Eager Loading):** Downloads the product and pricing rules map to RAM before iterating through the Excel file. This prevents the lethal N+1 query problem, avoiding blocks due to excessive requests.
* **On-the-fly Pricelist Management:** Detects the pricelist columns from the CSV and automatically creates the pricelists in Odoo if they do not exist.
* **Automatic Product Creation:** If an item from the Excel file does not exist in the ERP, it is created with its base price before applying specific pricelists.
* **REST-Ready Output:** The script returns a standard JSON response (`{success, data, message}`) to facilitate integration with APIs, Cron Jobs, or webhooks.
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/`.

## 🛠️ Requirements and Installation

```bash
pip install -r requirements.txt
```

Dependencies:

* `xmlrpc.client`, `csv`, `json` (Native)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 File Structure

```text
/upload_tax_odoo
 ├── importador_tarifas.py
 ├── .env.example
 ├── .env              ← create from .env.example (do not commit)
 ├── requirements.txt
 ├── tarifas_ejemplo.csv
 └── README.md
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage Odoo credentials and CSV configuration. Never edit credentials directly in the source code.

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the values:

   ```env
   ODOO_URL=https://your-odoo-domain.com
   ODOO_DB=database_name
   ODOO_USERNAME=your_user@email.com
   ODOO_PASSWORD=your_secure_password

   ARCHIVO_TARIFAS=tarifas_ejemplo.csv

   # Optional: pricelist columns separated by comma
   # COLUMNAS_TARIFAS=Tarifa PVP 2,Tarifa PVP,Tarifa PVP sin Iva,Nuevos cliente,Tarifa 15,Cliente fidelizado
   ```

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ODOO_URL` | YES | — | URL of your Odoo instance |
| `ODOO_DB` | YES | — | Database name |
| `ODOO_USERNAME` | YES | — | Odoo user |
| `ODOO_PASSWORD` | YES | — | User password |
| `ARCHIVO_TARIFAS` | YES | `tarifas_ejemplo.csv` | CSV filename with the pricelists |
| `COLUMNAS_TARIFAS` | NO | 6 standard pricelists | Pricelist columns to process (comma-separated) |

### Default pricelist columns

If `COLUMNAS_TARIFAS` is not defined, the script processes these 6 columns:

```text
Tarifa PVP 2, Tarifa PVP, Tarifa PVP sin Iva, Nuevos cliente, Tarifa 15, Cliente fidelizado
```

## 📄 CSV Specifications

### Technical Format

* **Delimiter:** Comma (`,`).
* **Encoding:** UTF-8-sig (properly handles Excel BOMs).

### Column Structure

| Header | Required | Function |
| --- | --- | --- |
| **Artículo** (Item) | YES | Internal reference in Odoo (`default_code`). Main search key. |
| **Nombre artículo** (Name) | YES | Commercial title. Used to create the product if it doesn't exist. |
| **Tarifa PVP 2**, etc. | NO | Pricelist columns (configurable). If the cell has a value > 0, the rule is updated. |

## 🚀 How to get it up and running

1. Prepare your `.csv` file in the same directory.
2. Configure the `.env` file with credentials and CSV filename.
3. Run the script:

```bash
python importador_tarifas.py
```

**Result:** Upon completion, the script prints a JSON object to the console confirming the success of the operation or detailing any critical error caught by the global handler.

## 📊 Logging System

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/tarifas_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** The code is fully commented and modularized following Python's *SOLID* and *Clean Code* standards. It includes `pydoc` signatures ready to be exported to a static documentation portal via MkDocs.
