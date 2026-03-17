# 🤖 AI Mass Copywriter & Inventory Processor (Groq Edition)

Módulo avanzado de procesamiento de lenguaje natural desarrollado por **BenjaminDTS** para la generación masiva de descripciones comerciales de productos (SEO) utilizando la API de Groq y modelos LLM de código abierto.

## 📋 Descripción

Este script está diseñado para procesar inventarios enormes (miles de filas) de forma autónoma, inyectando descripciones atractivas para e-commerce. Cuenta con un sistema de arquitectura resiliente:
* **Rotación de Modelos (Fallback):** Si un modelo agota su cuota de *Tokens Per Day* (TPD) o es retirado por Groq, el script salta automáticamente al siguiente modelo de la lista sin detener el proceso.
* **Control de Rate Limits:** Detecta errores 429 (Límite de peticiones por minuto) y aplica pausas estratégicas de 15 segundos para enfriar la API.
* **Tolerancia a Fallos y Reanudación:** Guarda el progreso en disco lote por lote. Si el proceso se interrumpe, al reiniciarlo detectará qué productos ya están listos y continuará exactamente donde se quedó.
* **Marcado de Errores:** Ninguna fila se pierde. Si la IA falla repetidamente con un producto, se etiqueta como `ERROR_IA` para su revisión manual.

## 🛠️ Requisitos e Instalación

Este script requiere librerías externas para la manipulación de datos y la conexión con la API.

Instala todas las dependencias con el archivo incluido:
```bash
pip install -r requeriments.txt
```

O manualmente solo las de ejecución:

```bash
pip install pandas groq tqdm loguru pydantic pydantic-settings
```

*(Opcional)* Solo documentación MkDocs:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## 📄 Especificaciones del Archivo de Entrada

El archivo origen (Excel o CSV) debe contener obligatoriamente las siguientes columnas:

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **Código** | SÍ | Identificador único del producto (ID interno). |
| **Producto** | SÍ | Nombre del artículo para darle contexto a la IA. |
| **Departamento** | NO | Categoría (ej: "Perros", "Gatos"). Vital para mejorar la precisión del Copywriter. |

## ⚙️ Guía de Configuración

Antes de ejecutar el script, edita el bloque principal al final del archivo `.py`:

1. **API Key:** Sustituye `"TU_API_KEY_AQUI"` por tu clave real generada en la consola de Groq.
2. **Archivo Origen:**
Asegúrate de que la variable `ARCHIVO` coincide con el nombre de tu archivo (ej: `inventario.xlsx` o `datos.csv`).
3. **Modelos Preferidos (Opcional):**
La variable global `MODELOS_DISPONIBLES` contiene la jerarquía de rotación. El script siempre intentará usar el primero de la lista y bajará posiciones en caso de error.

## 🚀 Cómo ponerlo en marcha

1. Coloca tu archivo de inventario en el mismo directorio que el script.
2. Ejecuta el script desde tu terminal:

```bash
python descripcion.py

```

**Resultado:** Verás una barra de progreso (`tqdm`) indicando el avance. Al finalizar, se generará un archivo llamado `inventario_con_descripciones.csv` con dos nuevas columnas: `Desc_Corta` (gancho comercial) y `Desc_Larga` (beneficios SEO).

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** Código escrito bajo la filosofía *Clean Code*. Módulos aislados y documentados bajo los estándares de `pydoc` para su renderizado web automático con MkDocs.

---

# 🤖 AI Mass Copywriter & Inventory Processor (Groq Edition)

Advanced natural language processing module developed by **BenjaminDTS** for the massive generation of commercial product descriptions (SEO) using the Groq API and open-source LLM models.

## 📋 Description

This script is designed to process huge inventories (thousands of rows) autonomously, injecting attractive descriptions for e-commerce. It features a resilient architecture system:

* **Model Rotation (Fallback):** If a model exhausts its *Tokens Per Day* (TPD) quota or is decommissioned by Groq, the script automatically jumps to the next model on the list without stopping the process.
* **Rate Limits Control:** Detects 429 errors (Requests per minute limit) and applies strategic 15-second pauses to cool down the API.
* **Fault Tolerance and Resumption:** Saves progress to disk batch by batch. If the process is interrupted, restarting it will detect which products are already finished and continue exactly where it left off.
* **Error Tagging:** No row is lost. If the AI repeatedly fails with a product, it is tagged as `ERROR_IA` for manual review.

## 🛠️ Requirements and Installation

This script requires external libraries for data manipulation and API connection.

Install all dependencies using the included file:

```bash
pip install -r requeriments.txt
```

Or manually, only the runtime ones:

```bash
pip install pandas groq tqdm loguru pydantic pydantic-settings
```

*(Optional)* Only for MkDocs documentation:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## 📄 Input File Specifications

The source file (Excel or CSV) must contain the following columns:

| Header | Required | Function |
| --- | --- | --- |
| **Código** (Code) | YES | Unique product identifier (Internal ID). |
| **Producto** (Product) | YES | Item name to provide context to the AI. |
| **Departamento** (Category) | NO | Category (e.g., "Dogs", "Cats"). Vital to improve Copywriter accuracy. |

## ⚙️ Configuration Guide

Before running the script, edit the main block at the bottom of the `.py` file:

1. **API Key:** Replace `"TU_API_KEY_AQUI"` with your real key generated in the Groq console.
2. **Source File:**
Ensure the `ARCHIVO` variable matches the name of your file (e.g., `inventory.xlsx` or `data.csv`).
3. **Preferred Models (Optional):**
The global variable `MODELOS_DISPONIBLES` contains the rotation hierarchy. The script will always try to use the first one on the list and move down in case of error.

## 🚀 How to get it up and running

1. Place your inventory file in the same directory as the script.
2. Run the script from your terminal:

```bash
python descripcion.py

```

**Result:** You will see a progress bar (`tqdm`) indicating the advance. Upon completion, a file named `inventario_con_descripciones.csv` will be generated with two new columns: `Desc_Corta` (commercial hook) and `Desc_Larga` (SEO benefits).

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** Code written under the *Clean Code* philosophy. Isolated modules documented under `pydoc` standards for automatic web rendering with MkDocs.