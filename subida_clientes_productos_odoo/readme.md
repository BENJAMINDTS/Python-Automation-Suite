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

# Advanced Contact Importer for Odoo
**Author:** BenjaminDTS

Python module designed for the bulk, intelligent, and secure migration of data from Excel/CSV files (Customers and Suppliers) to the Odoo ERP system using its XML-RPC API.

## 🚀 Main Features

* **Intelligent Role Merging:** Prevents duplicate records. If a Contact exists as a Customer and is processed again as a Supplier, the script merges both profiles (`customer_rank` and `supplier_rank`) into the same record.

* **Automatic Payment Term Management:** Reads the text from the Excel file (e.g., "GIRO 60") and automatically creates/assigns the accounting rule in Odoo (`account.payment.term`). Includes a security filter that ignores anomalous numbers or incorrect IBANs.

* **Fallback:** If Odoo rejects a contact because the VAT number is invalid according to tax regulations, the script retrieves the VAT number, saves it in Internal Notes, and creates the record anyway to avoid losing the data.

* **Automatic Archiving:** Detects if the `DATE OF TERMINATION` cell contains data and automatically archives the contact (`active = False`).

* **Regional Encoding:** Prepared with `latin-1` encoding to process Spanish characters (ñ, accents) from older Excel exports without errors.

## ⚙️ Prerequisites

Make sure you have Python installed on your system. The script uses native libraries, so it is not necessary to install external dependencies (`pip install`).

* `xmlrpc.client` (Native)
* `csv` (Native)
* `re` (Native)

## 📂 File Structure

For the script to work correctly, the files must be in the same directory:

```text
/project_directory
│-- contact_importer.py

│-- Clients.csv (Delimited by ';')

│-- SUPPLIERS.csv (Delimited by ',' or ';')

│-- README.md

```

## 🔧 Configuration

Before running, open `contact_importer.py` and edit the following variables in the file header with your environment data:

```python
URL = '[https://yourdomain.com](https://yourdomain.com)'
DB = 'database_name'
USERNAME = 'your_email@example.com'
PASSWORD = 'your_password_or_api_key'

```

## 💻 Usage

Open your terminal or command prompt, navigate to the project folder, and run:

```bash
python contact_importer.py
```

The script will display a real-time console log of each action: creations `[+]`, role updates `[UPDT]`, security alerts `[!]`, and errors `[-]`.


## 📝 Technical Notes

* The injected accounting field for paydays uses the technical parameter `nb_days` and the value `percent` at 100%, ensuring compatibility with Odoo 15, 16, and 17.
* Records are automatically documented in the `comment` field (Internal Notes) with the original creation dates to preserve the company's historical data.
