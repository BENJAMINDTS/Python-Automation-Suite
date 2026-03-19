# 🐍 Python Automation Suite - BenjaminDTS

Bienvenido a mi repositorio centralizado de automatizaciones. Aquí comparto una colección de scripts diseñados para optimizar flujos de trabajo, procesamiento de datos y tareas de web scraping, enfocados en la eficiencia y la legibilidad del código.

## 🛠️ Filosofía del Repositorio

Todos los scripts incluidos en este suite siguen un estándar de calidad estricto:

* **Documentación:** Código comentado siguiendo los estándares de **pydoc** para su integración con MkDocs.
* **Modularidad:** Cada carpeta es un proyecto independiente con su propio entorno, dependencias y configuración.
* **Seguridad:** Las credenciales y parámetros sensibles se gestionan exclusivamente mediante variables de entorno (`.env`). Nunca se hardcodean en el código.
* **Logging estructurado:** Todos los módulos usan `loguru` con salida coloreada en consola y archivos JSON rotativos en `logs/` para integración con Datadog, Loki o CloudWatch.
* **Tipado fuerte:** Todas las funciones incluyen type hints (Python 3.10+).

## 📦 Módulos Disponibles

| Módulo | Descripción |
| --- | --- |
| [`ia_description_products_generate`](ia_description_products_generate/) | Generación masiva de descripciones SEO para productos usando la API de Groq (LLMs). Incluye rotación de modelos, control de rate-limits y reanudación automática. |
| [`img_downloader`](img_downloader/) | Descarga masiva de imágenes de productos desde Bing Images. Patrón Productor/Consumidor con hilos paralelos y validación de resolución. |
| [`upload_products_odoo`](upload_products_odoo/) | Importación masiva de productos a Odoo vía XML-RPC con gestión de categorías, imágenes y reanudación automática. |
| [`upload_customers_suppliers_odoo`](upload_customers_suppliers_odoo/) | Importación masiva de clientes y proveedores a Odoo con validación de duplicados y generación automática de formas de pago. |
| [`upload_prices_odoo`](upload_prices_odoo/) | Actualización masiva de precios base y listas de precios B2C en Odoo con doble inyección y Turbo-Caché. |
| [`upload_tax_odoo`](upload_tax_odoo/) | Importación de múltiples tarifas de precios a Odoo. Eager Loading, creación automática de productos y salida REST-Ready (JSON). |

## 📂 Estructura del Proyecto

Cada módulo es un proyecto **autocontenido**:

```text
Python-Automation-Suite/
├── ia_description_products_generate/
│   ├── descripcion.py
│   ├── .env.example       ← plantilla de variables de entorno
│   ├── requirements.txt
│   └── readme.md
├── img_downloader/
│   ├── img_downloader.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_customers_suppliers_odoo/
│   ├── proveedor_cliente.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_prices_odoo/
│   ├── precios.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_products_odoo/
│   ├── subida.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
└── upload_tax_odoo/
    ├── importador_tarifas.py
    ├── .env.example
    ├── requirements.txt
    └── readme.md
```

## 🚀 Instalación Rápida (por módulo)

Cada módulo se instala y configura de forma independiente:

```bash
# 1. Clonar el repositorio
git clone https://github.com/BenjaminDTS/Python-Automation-Suite.git
cd Python-Automation-Suite

# 2. Acceder al módulo que necesitas
cd nombre_del_modulo

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus credenciales y parámetros reales

# 5. Ejecutar
python nombre_del_script.py
```

## 🔐 Gestión de Credenciales

Todos los módulos que se conectan a APIs externas (Groq, Odoo) leen sus credenciales desde un archivo `.env` local que **nunca se versiona**. Cada módulo incluye un archivo `.env.example` como plantilla documentada.

> **Regla de oro:** Si ves credenciales hardcodeadas en el código, es un error. Repórtalas.

## 📊 Sistema de Logging Unificado

Todos los módulos usan `loguru` con el mismo patrón:

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/<modulo>_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación 10 MB) |

## 📖 Documentación Técnica

Cada módulo incluye configuración de **MkDocs Material** para generar una web de referencia técnica:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
cd nombre_del_modulo
python -m mkdocs serve
# Navega a: http://127.0.0.1:8000
```

---

# 🐍 Python Automation Suite - BenjaminDTS

Welcome to my centralized automation repository. Here I share a collection of scripts designed to optimize workflows, data processing, and web scraping tasks, focusing on efficiency and code readability.

## 🛠️ Repository Philosophy

All scripts included in this suite adhere to a strict quality standard:

* **Documentation:** Commented code following **pydoc** standards for integration with MkDocs.
* **Modularity:** Each folder is an independent project with its own environment, dependencies, and configuration.
* **Security:** Credentials and sensitive parameters are managed exclusively via environment variables (`.env`). Never hardcoded in the source.
* **Structured logging:** All modules use `loguru` with colored console output and rotating JSON files in `logs/` for integration with Datadog, Loki, or CloudWatch.
* **Strong typing:** All functions include type hints (Python 3.10+).

## 📦 Available Modules

| Module | Description |
| --- | --- |
| [`ia_description_products_generate`](ia_description_products_generate/) | Bulk SEO product description generation using the Groq API (LLMs). Includes model rotation, rate-limit control, and automatic resumption. |
| [`img_downloader`](img_downloader/) | Bulk product image download from Bing Images. Producer/Consumer pattern with parallel threads and resolution validation. |
| [`upload_products_odoo`](upload_products_odoo/) | Bulk product import to Odoo via XML-RPC with category management, images, and automatic resumption. |
| [`upload_customers_suppliers_odoo`](upload_customers_suppliers_odoo/) | Bulk customer and supplier import to Odoo with duplicate validation and automatic payment term generation. |
| [`upload_prices_odoo`](upload_prices_odoo/) | Bulk base price and B2C pricelist update in Odoo with dual injection and Turbo-Cache. |
| [`upload_tax_odoo`](upload_tax_odoo/) | Multiple pricelist import to Odoo. Eager Loading, automatic product creation, and REST-Ready output (JSON). |

## 📂 Project Structure

Each module is a **self-contained** project:

```text
Python-Automation-Suite/
├── ia_description_products_generate/
│   ├── descripcion.py
│   ├── .env.example       ← environment variable template
│   ├── requirements.txt
│   └── readme.md
├── img_downloader/
│   ├── img_downloader.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_customers_suppliers_odoo/
│   ├── proveedor_cliente.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_prices_odoo/
│   ├── precios.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
├── upload_products_odoo/
│   ├── subida.py
│   ├── .env.example
│   ├── requirements.txt
│   └── readme.md
└── upload_tax_odoo/
    ├── importador_tarifas.py
    ├── .env.example
    ├── requirements.txt
    └── readme.md
```

## 🚀 Quick Installation (per module)

Each module is installed and configured independently:

```bash
# 1. Clone the repository
git clone https://github.com/BenjaminDTS/Python-Automation-Suite.git
cd Python-Automation-Suite

# 2. Go to the module you need
cd module_name

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your real credentials and parameters

# 5. Run
python script_name.py
```

## 🔐 Credential Management

All modules that connect to external APIs (Groq, Odoo) read their credentials from a local `.env` file that is **never committed**. Each module includes an `.env.example` file as a documented template.

> **Golden rule:** If you see hardcoded credentials in the code, it's a bug. Report it.

## 📊 Unified Logging System

All modules use `loguru` with the same pattern:

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/<module>_YYYY-MM-DD.log` | INFO | Structured JSON (10 MB rotation) |

## 📖 Technical Documentation

Each module includes **MkDocs Material** configuration to generate a technical reference web:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
cd module_name
python -m mkdocs serve
# Navigate to: http://127.0.0.1:8000
```
