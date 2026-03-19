# Importador Avanzado de Contactos para Odoo

**Autor:** BenjaminDTS

Módulo en Python diseñado para la migración masiva, inteligente y segura de datos desde archivos Excel/CSV (Clientes y Proveedores) hacia el ERP Odoo mediante su API XML-RPC.

## 🚀 Características Principales

* **Fusión Inteligente de Roles:** No duplica registros. Si un Contacto existe como Cliente y se vuelve a procesar como Proveedor, el script fusiona ambos perfiles (`customer_rank` y `supplier_rank`) en la misma ficha.
* **Auto-Gestión de Plazos de Pago:** Lee el texto del Excel (ej. "GIRO 60") y crea/asigna automáticamente la regla contable en Odoo (`account.payment.term`). Incluye un filtro de seguridad que ignora números anómalos o IBANs erróneos.
* **Archivado Automático:** Detecta si la celda `FECHA DE BAJA` contiene datos y archiva automáticamente al contacto (`active = False`).
* **Codificación Regional:** Preparado con codificación `latin-1` para procesar sin errores caracteres españoles (ñ, acentos) procedentes de exportaciones antiguas de Excel.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/`.

## 🛠️ Requisitos e Instalación

```bash
pip install -r requirements.txt
```

Dependencias:

* `xmlrpc.client` (Nativa)
* `csv`, `re` (Nativas)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 Estructura de Archivos

```text
/upload_customers_suppliers_odoo
 ├── proveedor_cliente.py
 ├── .env.example
 ├── .env              ← crear desde .env.example (no versionar)
 ├── requirements.txt
 ├── Clientes.csv      (delimitado por ';')
 ├── PROVEEDORES.csv   (delimitado por ',')
 └── README.md
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar las credenciales de Odoo. Nunca edites las credenciales directamente en el código fuente.

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores:

   ```env
   ODOO_URL=https://tu-dominio.odoo.com
   ODOO_DB=nombre_de_tu_base_de_datos
   ODOO_USERNAME=tu_usuario@empresa.com
   ODOO_PASSWORD=tu_contraseña_segura

   # Opcionales
   ARCHIVO_CLIENTES=Clientes.csv
   ARCHIVO_PROVEEDORES=PROVEEDORES.csv
   ENCODING_CSV=latin-1
   ```

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `ODOO_URL` | SÍ | — | URL de tu instancia de Odoo |
| `ODOO_DB` | SÍ | — | Nombre de la base de datos |
| `ODOO_USERNAME` | SÍ | — | Usuario de Odoo |
| `ODOO_PASSWORD` | SÍ | — | Contraseña del usuario |
| `ARCHIVO_CLIENTES` | NO | `Clientes.csv` | CSV de clientes (delimitador `;`) |
| `ARCHIVO_PROVEEDORES` | NO | `PROVEEDORES.csv` | CSV de proveedores (delimitador `,`) |
| `ENCODING_CSV` | NO | `latin-1` | Codificación de los archivos CSV |

## 💻 Uso

```bash
python proveedor_cliente.py
```

El script registra en tiempo real cada acción mediante `loguru`. Los logs estructurados (JSON) se guardan en `logs/clientes_proveedores_YYYY-MM-DD.log`.

## 📊 Sistema de Logging

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/clientes_proveedores_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

## 📝 Notas Técnicas

* El campo contable inyectado para los días de pago utiliza el parámetro técnico `nb_days` y el valor `percent` al 100%, garantizando la compatibilidad con Odoo 15, 16 y 17.
* Los registros se documentan automáticamente en el campo `comment` (Notas Internas) con las fechas de alta originales para preservar el histórico de la empresa.
* Si las variables de entorno requeridas no están presentes, el script termina con `sys.exit(1)` y un mensaje de error crítico.

---

# Advanced Contact Importer for Odoo

**Author:** BenjaminDTS

Python module designed for the bulk, intelligent, and secure migration of data from Excel/CSV files (Customers and Suppliers) to the Odoo ERP system using its XML-RPC API.

## 🚀 Main Features

* **Intelligent Role Merging:** Prevents duplicate records. If a Contact exists as a Customer and is processed again as a Supplier, the script merges both profiles (`customer_rank` and `supplier_rank`) into the same record.
* **Automatic Payment Term Management:** Reads the text from the Excel file (e.g., "GIRO 60") and automatically creates/assigns the accounting rule in Odoo (`account.payment.term`). Includes a security filter that ignores anomalous numbers or incorrect IBANs.
* **Automatic Archiving:** Detects if the `DATE OF TERMINATION` cell contains data and automatically archives the contact (`active = False`).
* **Regional Encoding:** Prepared with `latin-1` encoding to process Spanish characters (ñ, accents) from older Excel exports without errors.
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/`.

## 🛠️ Requirements and Installation

```bash
pip install -r requirements.txt
```

Dependencies:

* `xmlrpc.client` (Native)
* `csv`, `re` (Native)
* `loguru>=0.7.0`
* `python-dotenv>=1.0.0`

## 📂 File Structure

```text
/upload_customers_suppliers_odoo
 ├── proveedor_cliente.py
 ├── .env.example
 ├── .env              ← create from .env.example (do not commit)
 ├── requirements.txt
 ├── Clientes.csv      (semicolon-delimited)
 ├── PROVEEDORES.csv   (comma-delimited)
 └── README.md
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage Odoo credentials. Never edit credentials directly in the source code.

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the values:

   ```env
   ODOO_URL=https://your-domain.odoo.com
   ODOO_DB=your_database_name
   ODOO_USERNAME=your_user@company.com
   ODOO_PASSWORD=your_secure_password

   # Optional
   ARCHIVO_CLIENTES=Clientes.csv
   ARCHIVO_PROVEEDORES=PROVEEDORES.csv
   ENCODING_CSV=latin-1
   ```

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `ODOO_URL` | YES | — | URL of your Odoo instance |
| `ODOO_DB` | YES | — | Database name |
| `ODOO_USERNAME` | YES | — | Odoo user |
| `ODOO_PASSWORD` | YES | — | User password |
| `ARCHIVO_CLIENTES` | NO | `Clientes.csv` | Customer CSV (`;` delimiter) |
| `ARCHIVO_PROVEEDORES` | NO | `PROVEEDORES.csv` | Supplier CSV (`,` delimiter) |
| `ENCODING_CSV` | NO | `latin-1` | CSV file encoding |

## 💻 Usage

```bash
python proveedor_cliente.py
```

The script logs every action in real time via `loguru`. Structured logs (JSON) are saved to `logs/clientes_proveedores_YYYY-MM-DD.log`.

## 📊 Logging System

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/clientes_proveedores_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Technical Notes

* The injected accounting field for payment days uses the technical parameter `nb_days` and the value `percent` at 100%, ensuring compatibility with Odoo 15, 16, and 17.
* Records are automatically documented in the `comment` field (Internal Notes) with the original creation dates to preserve the company's historical data.
* If required environment variables are missing, the script exits with `sys.exit(1)` and a critical error message.
