# 🏷️ Odoo Dual Price Updater (XML-RPC Edition)

Módulo avanzado de automatización desarrollado por **BenjaminDTS** para la actualización masiva de precios base y listas de precios (Pricelists) en Odoo utilizando su API XML-RPC.

## 📋 Descripción

Este script está diseñado para actualizar miles de tarifas en segundos sin saturar el servidor del ERP. Implementa un sistema de inyección dual ("Híbrido") y un modo "Turbo-Caché" en memoria RAM:

* **Doble Inyección de Precios:** Actualiza el precio contable oficial (Base Imponible / Sin IVA) en el núcleo del producto y, simultáneamente, crea una regla visual con el precio final (Con IVA) en una Tarifa B2C dedicada.
* **Turbo-Caché (Anti-Timeouts):** Descarga el mapa del catálogo completo de Odoo a la memoria RAM en 2 segundos, evitando realizar decenas de miles de peticiones de lectura por internet.
* **Auto-Detección de Formatos:** Detecta automáticamente si el CSV usa comas (`,`) o puntos y comas (`;`), y elimina los caracteres invisibles (BOM) generados por Excel.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/`.

## 🛠️ Requisitos e Instalación

```bash
pip install -r requirements.txt
```

Dependencias:

* `xmlrpc.client`, `csv` (Nativas)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 Estructura de Archivos

```text
/upload_prices_odoo
 ├── precios.py
 ├── .env.example
 ├── .env              ← crear desde .env.example (no versionar)
 ├── requirements.txt
 ├── tu_archivo.csv
 └── README.md
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar las credenciales de Odoo y el mapeo de columnas. Nunca edites las credenciales directamente en el código fuente.

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores:

   ```env
   ODOO_URL=http://localhost:8069
   ODOO_DB=nombre_de_tu_base_de_datos
   ODOO_USERNAME=tu_usuario
   ODOO_PASSWORD=tu_contraseña

   # Mapeo del CSV
   ARCHIVO_TARIFAS=nombre_del_archivo.csv
   COLUMNA_SIN_IVA=nombre_del_campo_sin_iva
   COLUMNA_CON_IVA=nombre_del_campo_con_iva

   # Opcional
   NOMBRE_TARIFA_ODOO=Tarifa PVP (Con IVA)
   ```

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ODOO_URL` | SÍ | — | URL de tu instancia de Odoo |
| `ODOO_DB` | SÍ | — | Nombre de la base de datos |
| `ODOO_USERNAME` | SÍ | — | Usuario de Odoo |
| `ODOO_PASSWORD` | SÍ | — | Contraseña del usuario |
| `ARCHIVO_TARIFAS` | SÍ | — | Nombre del CSV con los precios |
| `COLUMNA_SIN_IVA` | SÍ | — | Columna del CSV con precio sin IVA → `list_price` |
| `COLUMNA_CON_IVA` | SÍ | — | Columna del CSV con precio con IVA → regla B2C |
| `NOMBRE_TARIFA_ODOO` | NO | `Tarifa PVP (Con IVA)` | Nombre de la lista de precios B2C en Odoo |

## 📄 Especificaciones del CSV

### Formato Técnico

* **Ubicación:** Misma carpeta que el script.
* **Delimitador:** `,` o `;` (detectado automáticamente).
* **Codificación:** UTF-8 o UTF-8-BOM.

### Estructura de Columnas

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **Artículo** | SÍ | Referencia interna en Odoo (`default_code`) para localizar el producto. |
| **(COLUMNA_SIN_IVA)** | SÍ | Se inyecta como `list_price` en la pestaña Información General del producto. |
| **(COLUMNA_CON_IVA)** | SÍ | Se inyecta como `fixed_price` dentro de la Lista de Precios B2C. |

## 🚀 Cómo ponerlo en marcha

1. Coloca tu archivo CSV en el mismo directorio que el script.
2. Configura el archivo `.env` con las credenciales y el mapeo de columnas.
3. Ejecuta el script:

```bash
python precios.py
```

**Resultado:** El sistema carga la caché y comienza a procesar el archivo. Al terminar, el log muestra un resumen con los precios base actualizados, las reglas B2C inyectadas y los productos omitidos.

## 📊 Sistema de Logging

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/precios_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** Código escrito bajo la filosofía *Clean Code*. Las funciones están aisladas para cumplir un único propósito (Single Responsibility) y documentadas bajo los estándares de `pydoc` para su renderizado web con MkDocs.

---

# 🏷️ Odoo Dual Price Updater (XML-RPC Edition)

Advanced automation module developed by **BenjaminDTS** for the massive update of base prices and Pricelists in Odoo using its XML-RPC API.

## 📋 Description

This script is designed to update thousands of rates in seconds without overwhelming the ERP server. It implements a dual injection system ("Hybrid") and a RAM "Turbo-Cache" mode:

* **Dual Price Injection:** Updates the official accounting price (Tax Excluded) in the product core and simultaneously creates a visual rule with the final price (Tax Included) in a dedicated B2C Pricelist.
* **Turbo-Cache (Anti-Timeouts):** Downloads the entire Odoo catalog map to RAM in 2 seconds, avoiding tens of thousands of read requests over the internet.
* **Auto-Format Detection:** Automatically detects whether the CSV uses commas (`,`) or semicolons (`;`), and strips invisible BOM characters generated by Excel.
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/`.

## 🛠️ Requirements and Installation

```bash
pip install -r requirements.txt
```

Dependencies:

* `xmlrpc.client`, `csv` (Native)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 File Structure

```text
/upload_prices_odoo
 ├── precios.py
 ├── .env.example
 ├── .env              ← create from .env.example (do not commit)
 ├── requirements.txt
 ├── your_file.csv
 └── README.md
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage Odoo credentials and column mapping. Never edit credentials directly in the source code.

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the values:

   ```env
   ODOO_URL=http://localhost:8069
   ODOO_DB=your_database_name
   ODOO_USERNAME=your_user
   ODOO_PASSWORD=your_password

   # CSV mapping
   ARCHIVO_TARIFAS=your_file.csv
   COLUMNA_SIN_IVA=price_excl_vat_column
   COLUMNA_CON_IVA=price_incl_vat_column

   # Optional
   NOMBRE_TARIFA_ODOO=Tarifa PVP (Con IVA)
   ```

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ODOO_URL` | YES | — | URL of your Odoo instance |
| `ODOO_DB` | YES | — | Database name |
| `ODOO_USERNAME` | YES | — | Odoo user |
| `ODOO_PASSWORD` | YES | — | User password |
| `ARCHIVO_TARIFAS` | YES | — | CSV filename with prices |
| `COLUMNA_SIN_IVA` | YES | — | CSV column for tax-excluded price → `list_price` |
| `COLUMNA_CON_IVA` | YES | — | CSV column for tax-included price → B2C rule |
| `NOMBRE_TARIFA_ODOO` | NO | `Tarifa PVP (Con IVA)` | B2C pricelist name in Odoo |

## 📄 CSV Specifications

### Technical Format

* **Location:** Same folder as the script.
* **Delimiter:** `,` or `;` (auto-detected).
* **Encoding:** UTF-8 or UTF-8-BOM.

### Column Structure

| Header | Required | Function |
| --- | --- | --- |
| **Artículo** (Code) | YES | Internal reference in Odoo (`default_code`) to locate the product. |
| **(COLUMNA_SIN_IVA)** | YES | Injected as `list_price` in the General Information tab of the product. |
| **(COLUMNA_CON_IVA)** | YES | Injected as `fixed_price` inside the B2C Pricelist. |

## 🚀 How to get it up and running

1. Place your CSV file in the same directory as the script.
2. Configure the `.env` file with credentials and column mapping.
3. Run the script:

```bash
python precios.py
```

**Result:** The system loads the cache and begins processing the file. Upon completion, the log displays a summary of updated base prices, injected B2C rules, and skipped products.

## 📊 Logging System

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/precios_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** Code written under the *Clean Code* philosophy. Functions are isolated to fulfill a single purpose (Single Responsibility) and documented under `pydoc` standards for web rendering with MkDocs.
