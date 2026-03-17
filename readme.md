# 🐍 Python Automation Suite - BenjaminDTS

Bienvenido a mi repositorio centralizado de automatizaciones. Aquí comparto una colección de scripts diseñados para optimizar flujos de trabajo, procesamiento de datos y tareas de web scraping, enfocados en la eficiencia y la legibilidad del código.

## 🛠️ Filosofía del Repositorio

Todos los scripts incluidos en este suite siguen un estándar de calidad estricto:

* **Documentación**: Código comentado siguiendo los estándares de **pydoc** para su integración con MkDocs.
* **Modularidad**: Herramientas listas para ser integradas en otros proyectos o ejecutadas de forma independiente.
* **Interfaz**: Uso de configuraciones claras y manejo de errores para entornos de producción.

## 📖 Documentación Interactiva

Este repositorio utiliza **MkDocs Material** para generar una interfaz web con la referencia técnica de cada módulo (funciones, clases y parámetros).

Para lanzar la documentación en local:

1. Instala las dependencias: `pip install -r requirements.txt`
2. Ejecuta el servidor: `python -m mkdocs serve`
3. Navega a: `http://127.0.0.1:8000`

## 📦 Módulos Disponibles

| Módulo | Descripción |
| --- | --- |
| [`ia_description_products_generate`](ia_description_products_generate/) | Generación masiva de descripciones SEO para productos usando la API de Groq (LLMs). Incluye rotación de modelos, control de rate-limits y reanudación automática. |
| [`upload_products_odoo`](upload_products_odoo/) | Importación masiva de productos a Odoo vía XML-RPC. |
| [`upload_customers_suppliers_odoo`](upload_customers_suppliers_odoo/) | Importación masiva de clientes y proveedores a Odoo con validación de duplicados y generación automática de formas de pago. |
| [`upload_prices_odoo`](upload_prices_odoo/) | Actualización masiva de tarifas de precios en Odoo. |
| [`upload_tax_odoo`](upload_tax_odoo/) | Importación de tarifas fiscales a Odoo. |
| [`img_downloader`](img_downloader/) | Descarga masiva de imágenes de productos desde URLs. |

## 📂 Estructura del Proyecto

* `/docs`: Archivos fuente de la documentación en Markdown.
* `*.py`: Scripts de automatización listos para usar.
* `mkdocs.yml`: Configuración del motor de documentación.
* `requirements.txt`: Dependencias necesarias para el entorno.

## 🚀 Instalación Rápida

```bash
# Clonar el repositorio
git clone [https://github.com/tu-usuario/nombre-del-repo.git](https://github.com/tu-usuario/nombre-del-repo.git)

# Acceder al directorio
cd nombre-del-repo

# Instalar dependencias
pip install -r requirements.txt
```

# 🐍 Python Automation Suite - BenjaminDTS

Welcome to my centralized automation repository. Here I share a collection of scripts designed to optimize workflows, data processing, and web scraping tasks, focusing on efficiency and code readability.

## 🛠️ Repository Philosophy

All scripts included in this suite adhere to a strict quality standard:

* **Documentation**: Commented code following **pydoc** standards for integration with MkDocs.

* **Modularity**: Tools ready to be integrated into other projects or run independently.

* **Interface**: Use of clear configurations and error handling for production environments.

## 📖 Interactive Documentation

This repository uses **MkDocs Material** to generate a web interface with the technical reference for each module (functions, classes, and parameters).

To launch the documentation locally:

1. Install the dependencies: `pip install -r requirements.txt`
2. Run the server: `python -m mkdocs serve`
3. Navigate to: `http://127.0.0.1:8000`

## 📦 Available Modules

| Module | Description |
| --- | --- |
| [`ia_description_products_generate`](ia_description_products_generate/) | Bulk SEO product description generation using the Groq API (LLMs). Includes model rotation, rate-limit control, and automatic resumption. |
| [`upload_products_odoo`](upload_products_odoo/) | Bulk product import to Odoo via XML-RPC. |
| [`upload_customers_suppliers_odoo`](upload_customers_suppliers_odoo/) | Bulk customer and supplier import to Odoo with duplicate validation and automatic payment term generation. |
| [`upload_prices_odoo`](upload_prices_odoo/) | Bulk price list update in Odoo. |
| [`upload_tax_odoo`](upload_tax_odoo/) | Tax schedule import to Odoo. |
| [`img_downloader`](img_downloader/) | Bulk product image download from URLs. |

## 📂 Project Structure

* `/docs`: Source files for the documentation in Markdown.
* `*.py`: Ready-to-use automation scripts.
* `mkdocs.yml`: Configuration for the documentation engine.
* `requirements.txt`: Dependencies required for the environment.

## 🚀 Quick Installation

```bash
# Clone the repository
git clone [https://github.com/your-username/repo-name.git](https://github.com/your-username/repo-name.git)

# Access the directory
cd repo-name

# Install dependencies
pip install -r requirements.txt
```
