# Importador Avanzado de Contactos para Odoo
**Autor:** BenjaminDTS

Módulo en Python diseñado para la migración masiva, inteligente y segura de datos desde archivos Excel/CSV (Clientes y Proveedores) hacia el ERP Odoo mediante su API XML-RPC.

## 🚀 Características Principales

* **Fusión Inteligente de Roles:** No duplica registros. Si un Contacto existe como Cliente y se vuelve a procesar como Proveedor, el script fusiona ambos perfiles (`customer_rank` y `supplier_rank`) en la misma ficha.
* **Auto-Gestión de Plazos de Pago:** Lee el texto del Excel (ej. "GIRO 60") y crea/asigna automáticamente la regla contable en Odoo (`account.payment.term`). Incluye un filtro de seguridad que ignora números anómalos o IBANs erróneos.
* **Tolerancia a Fallos (Fallback):** Si Odoo rechaza un contacto porque el C.I.F. es inválido según la normativa fiscal, el script rescata el C.I.F., lo guarda en las Notas Internas y crea la ficha de todas formas para no perder el dato.
* **Archivado Automático:** Detecta si la celda `FECHA DE BAJA` contiene datos y archiva automáticamente al contacto (`active = False`).
* **Codificación Regional:** Preparado con codificación `latin-1` para procesar sin errores caracteres españoles (ñ, acentos) procedentes de exportaciones antiguas de Excel.

## ⚙️ Requisitos Previos

Asegúrate de tener Python instalado en tu sistema. El script utiliza librerías nativas, por lo que no es necesario instalar dependencias externas (`pip install`).
* `xmlrpc.client` (Nativa)
* `csv` (Nativa)
* `re` (Nativa)

## 📂 Estructura de Archivos

Para que el script funcione correctamente, los archivos deben estar en el mismo directorio:

```text
/directorio_del_proyecto
 │-- importador_contactos.py
 │-- Clientes.csv (Delimitado por ';')
 │-- PROVEEDORES.csv (Delimitado por ',' o ';')
 │-- README.md

```

## 🔧 Configuración

Antes de ejecutar, abre `importador_contactos.py` y edita las siguientes variables en la cabecera del archivo con los datos de tu entorno:

```python
URL = '[https://tudominio.com](https://tudominio.com)'
DB = 'nombre_de_la_base_de_datos'
USERNAME = 'tu_correo@ejemplo.com'
PASSWORD = 'tu_contraseña_o_api_key'

```

## 💻 Uso

Abre tu terminal o símbolo del sistema, navega hasta la carpeta del proyecto y ejecuta:

```bash
python importador_contactos.py
```

El script mostrará un registro en tiempo real por consola de cada acción: creaciones `[+]`, actualizaciones de rol `[UPDT]`, alertas de seguridad `[!]` y errores `[-]`.

## 📝 Notas Técnicas

* El campo contable inyectado para los días de pago utiliza el parámetro técnico `nb_days` y el valor `percent` al 100%, garantizando la compatibilidad con Odoo 15, 16 y 17.
* Los registros se documentan automáticamente en el campo `comment` (Notas Internas) con las fechas de alta originales para preservar el histórico de la empresa.