# 🤖 AI Mass Copywriter & Inventory Processor (Groq Edition)

Módulo avanzado de procesamiento de lenguaje natural desarrollado por **BenjaminDTS** para la generación masiva de descripciones comerciales de productos (SEO) utilizando la API de Groq y modelos LLM de código abierto.

## 📋 Descripción

Este script está diseñado para procesar inventarios enormes (miles de filas) de forma autónoma, inyectando descripciones atractivas para e-commerce. Cuenta con un sistema de arquitectura resiliente:

* **Rotación de Modelos (Fallback):** Si un modelo agota su cuota de *Tokens Per Day* (TPD) o es retirado por Groq, el script salta automáticamente al siguiente modelo de la lista sin detener el proceso.
* **Control de Rate Limits:** Detecta errores 429 (Límite de peticiones por minuto) y aplica pausas estratégicas de 20 segundos para enfriar la API.
* **Tolerancia a Fallos y Reanudación:** Guarda el progreso en disco lote por lote. Si el proceso se interrumpe, al reiniciarlo detectará qué productos ya están listos y continuará exactamente donde se quedó.
* **Marcado de Errores:** Ninguna fila se pierde. Si la IA falla repetidamente con un producto, se etiqueta como `ERROR_IA` para su revisión manual.
* **Logging Estructurado:** Usa `loguru` con doble salida — consola coloreada y archivo JSON rotativo en `logs/` compatible con Datadog/Loki/CloudWatch.

## 🛠️ Requisitos e Instalación

Instala todas las dependencias con el archivo incluido:

```bash
pip install -r requirements.txt
```

O manualmente solo las de ejecución:

```bash
pip install pandas groq tqdm loguru pydantic pydantic-settings
```

*(Opcional)* Solo documentación MkDocs:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## ⚙️ Configuración mediante `.env`

Este módulo usa **variables de entorno** para gestionar credenciales y parámetros. Nunca edites las credenciales directamente en el código fuente.

### Pasos

1. Copia el archivo de plantilla:

   ```bash
   cp .env.example .env
   ```

2. Abre `.env` y rellena los valores:

   ```env
   # [REQUERIDO] Clave de autenticación para la API de Groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

   # [OPCIONAL] Productos por lote enviado a la IA (por defecto: 10)
   BATCH_SIZE=10

   # [OPCIONAL] Nombre del archivo CSV de salida
   ARCHIVO_SALIDA=catalogo_con_descripciones.csv
   ```

3. Asegúrate de que `.env` está en `.gitignore` (ya está incluido por defecto).

> **Nunca subas el archivo `.env` al control de versiones.**

### Variables disponibles

| Variable | Requerida | Por defecto | Descripción |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | SÍ | — | Clave API de Groq. Obtén la tuya en [console.groq.com](https://console.groq.com) |
| `BATCH_SIZE` | NO | `10` | Productos por lote enviado a la IA |
| `ARCHIVO_SALIDA` | NO | `catalogo_con_descripciones.csv` | Nombre del CSV de resultados |

## 📄 Especificaciones del Archivo de Entrada

El archivo origen (Excel o CSV) debe contener obligatoriamente las siguientes columnas:

| Cabecera | Requerido | Función |
| --- | --- | --- |
| **Id** | SÍ | Identificador único del producto. |
| **Label** | SÍ | Nombre del artículo para darle contexto a la IA. |
| **Categoria** | NO | Especie/segmento (ej: "Perros", "Gatos"). Mejora la precisión del copywriter. |
| **Marca** | NO | Marca del producto. Si es "Generica" no se incluye en el prompt. |

## 🚀 Cómo ponerlo en marcha

1. Coloca tu archivo de inventario en el mismo directorio que el script.
2. Configura el archivo `.env` con tu clave de Groq.
3. Edita la variable `ARCHIVO` en el bloque `__main__` de `descripcion.py` con el nombre de tu archivo.
4. Ejecuta el script:

```bash
python descripcion.py
```

**Resultado:** Verás una barra de progreso (`tqdm`) indicando el avance. Los logs estructurados se guardan en `logs/proceso_YYYY-MM-DD.log`. Al finalizar, se generará el CSV de salida con dos nuevas columnas: `Descripción corta` y `Description`.

## 📊 Sistema de Logging

Los logs se escriben en dos destinos simultáneamente:

| Destino | Nivel | Formato |
| --- | --- | --- |
| Consola (stderr) | DEBUG | Texto coloreado con timestamp |
| `logs/proceso_YYYY-MM-DD.log` | INFO | JSON estructurado (rotación cada 10 MB) |

## 📝 Notas de Autoría y Documentación

* **Autor:** BenjaminDTS.
* **Documentación:** Código escrito bajo la filosofía *Clean Code*. Módulos aislados y documentados bajo los estándares de `pydoc` para su renderizado web automático con MkDocs.

---

# 🤖 AI Mass Copywriter & Inventory Processor (Groq Edition)

Advanced natural language processing module developed by **BenjaminDTS** for the massive generation of commercial product descriptions (SEO) using the Groq API and open-source LLM models.

## 📋 Description

This script is designed to process huge inventories (thousands of rows) autonomously, injecting attractive descriptions for e-commerce. It features a resilient architecture system:

* **Model Rotation (Fallback):** If a model exhausts its *Tokens Per Day* (TPD) quota or is decommissioned by Groq, the script automatically jumps to the next model on the list without stopping the process.
* **Rate Limits Control:** Detects 429 errors (Requests per minute limit) and applies strategic 20-second pauses to cool down the API.
* **Fault Tolerance and Resumption:** Saves progress to disk batch by batch. If the process is interrupted, restarting it will detect which products are already finished and continue exactly where it left off.
* **Error Tagging:** No row is lost. If the AI repeatedly fails with a product, it is tagged as `ERROR_IA` for manual review.
* **Structured Logging:** Uses `loguru` with dual output — colored console and rotating JSON file in `logs/` compatible with Datadog/Loki/CloudWatch.

## 🛠️ Requirements and Installation

Install all dependencies using the included file:

```bash
pip install -r requirements.txt
```

Or manually, only the runtime ones:

```bash
pip install pandas groq tqdm loguru pydantic pydantic-settings
```

*(Optional)* Only for MkDocs documentation:

```bash
pip install mkdocs mkdocs-material mkdocstrings[python]
```

## ⚙️ Configuration via `.env`

This module uses **environment variables** to manage credentials and parameters. Never edit credentials directly in the source code.

### Steps

1. Copy the template file:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in the values:

   ```env
   # [REQUIRED] Groq API authentication key
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx

   # [OPTIONAL] Products per batch sent to the AI (default: 10)
   BATCH_SIZE=10

   # [OPTIONAL] Output CSV filename
   ARCHIVO_SALIDA=catalogo_con_descripciones.csv
   ```

3. Make sure `.env` is in `.gitignore` (already included by default).

> **Never commit the `.env` file to version control.**

### Available variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `GROQ_API_KEY` | YES | — | Groq API key. Get yours at [console.groq.com](https://console.groq.com) |
| `BATCH_SIZE` | NO | `10` | Products per batch sent to the AI |
| `ARCHIVO_SALIDA` | NO | `catalogo_con_descripciones.csv` | Output CSV filename |

## 📄 Input File Specifications

The source file (Excel or CSV) must contain the following columns:

| Header | Required | Function |
| --- | --- | --- |
| **Id** | YES | Unique product identifier. |
| **Label** | YES | Item name to provide context to the AI. |
| **Categoria** | NO | Species/segment (e.g., "Dogs", "Cats"). Improves copywriter accuracy. |
| **Marca** | NO | Product brand. If "Generica", it is excluded from the prompt. |

## 🚀 How to get it up and running

1. Place your inventory file in the same directory as the script.
2. Configure the `.env` file with your Groq API key.
3. Edit the `ARCHIVO` variable in the `__main__` block of `descripcion.py` with your filename.
4. Run the script:

```bash
python descripcion.py
```

**Result:** You will see a progress bar (`tqdm`) indicating the advance. Structured logs are saved in `logs/proceso_YYYY-MM-DD.log`. Upon completion, the output CSV will be generated with two new columns: `Descripción corta` and `Description`.

## 📊 Logging System

Logs are written to two destinations simultaneously:

| Destination | Level | Format |
| --- | --- | --- |
| Console (stderr) | DEBUG | Colored text with timestamp |
| `logs/proceso_YYYY-MM-DD.log` | INFO | Structured JSON (rotation every 10 MB) |

## 📝 Authorship and Documentation Notes

* **Author:** BenjaminDTS.
* **Documentation:** Code written under the *Clean Code* philosophy. Isolated modules documented under `pydoc` standards for automatic web rendering with MkDocs.
