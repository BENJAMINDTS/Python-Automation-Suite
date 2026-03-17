"""
Módulo de Procesamiento Masivo IA con Rotación Automática y Tolerancia a Fallos.

Procesa catálogos de productos de tienda de animales conectándose a la API de Groq.
Genera descripciones corta y larga para cada producto usando:
  - Label     → nombre comercial del producto
  - Categoria → contexto de especie/segmento (Perros, Gatos, Aves, etc.)
  - Marca     → incluida en el prompt solo si NO es "Generica"

El identificador único de cada producto es la columna 'Id'.
Los resultados se persisten de forma incremental para permitir reanudación.

:author: BenjaminDTS
:version: 1.2.0
"""

import os
import sys
import json
import time

import pandas as pd
from groq import Groq
from tqdm import tqdm
from loguru import logger
from pydantic import BaseModel, field_validator, ValidationError
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Logger estructurado (§13)
# ---------------------------------------------------------------------------
logger.remove()

logger.add(
    sys.stderr,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {message}",
    level="DEBUG",
    colorize=True,
)
logger.add(
    "logs/proceso_{time:YYYY-MM-DD}.log",
    format="{time} | {level} | {message}",
    level="INFO",
    rotation="10 MB",
    serialize=True,  # JSON estructurado para Datadog/Loki/CloudWatch
)

# ---------------------------------------------------------------------------
# Modelos disponibles en Groq (en orden de preferencia y cuota)
# ---------------------------------------------------------------------------
MODELOS_DISPONIBLES: list[str] = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "deepseek-r1-distill-llama-70b",
]

MARCA_GENERICA = "generica"  # Valor normalizado para comparación insensible a mayúsculas


# ---------------------------------------------------------------------------
# Excepciones de dominio (§3 — SRP)
# ---------------------------------------------------------------------------

class ModelosAgotadosError(Exception):
    """
    Se lanza cuando todos los modelos de Groq han agotado su cuota diaria (TPD).

    :param message: Descripción del fallo.
    :type message: str
    """


class ArchivoInventarioError(Exception):
    """
    Se lanza cuando el archivo de catálogo no puede leerse o tiene formato no soportado.

    :param message: Descripción del fallo.
    :type message: str
    """


# ---------------------------------------------------------------------------
# Validación de entorno al arranque (§16)
# ---------------------------------------------------------------------------

class ConfiguracionEntorno(BaseSettings):
    """
    Modelo de validación de variables de entorno requeridas.

    Hereda de ``BaseSettings`` (pydantic-settings) para leer automáticamente
    desde variables de entorno y archivo ``.env``.

    :param groq_api_key: Clave de autenticación para la API de Groq.
    :type groq_api_key: str
    :param batch_size: Número de productos por lote enviado a la IA (por defecto 10).
    :type batch_size: int
    :param archivo_salida: Nombre del CSV de salida con los resultados generados.
    :type archivo_salida: str
    """

    groq_api_key: str
    batch_size: int = 10
    archivo_salida: str = "catalogo_con_descripciones.csv"

    @field_validator("groq_api_key")
    @classmethod
    def api_key_no_vacia(cls, valor: str) -> str:
        """
        Valida que la clave API no sea una cadena vacía.

        :param valor: Valor recibido de la variable de entorno.
        :type valor: str
        :raises ValueError: Si la clave está vacía o solo contiene espacios.
        :return: La clave validada y sin espacios externos.
        :rtype: str
        """
        if not valor.strip():
            raise ValueError("GROQ_API_KEY no puede estar vacía.")
        return valor

    @field_validator("batch_size")
    @classmethod
    def batch_size_positivo(cls, valor: int) -> int:
        """
        Valida que el tamaño de lote sea un entero positivo.

        :param valor: Tamaño de lote propuesto.
        :type valor: int
        :raises ValueError: Si el valor es menor o igual a cero.
        :return: El tamaño de lote validado.
        :rtype: int
        """
        if valor <= 0:
            raise ValueError("BATCH_SIZE debe ser mayor que 0.")
        return valor

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


def cargar_configuracion() -> ConfiguracionEntorno:
    """
    Carga y valida la configuración del entorno desde variables de entorno o .env.

    Termina el proceso con código 1 y un mensaje descriptivo si la validación falla,
    evitando que el script continúe con una configuración incompleta.

    :raises SystemExit: Si la validación de entorno falla.
    :return: Instancia de configuración completamente validada.
    :rtype: ConfiguracionEntorno
    """
    try:
        return ConfiguracionEntorno()
    except ValidationError as error:
        logger.error(
            "Configuración de entorno inválida. Revisa el archivo .env.",
            errores=error.errors(),
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Construcción del payload de producto para el prompt
# ---------------------------------------------------------------------------

def _construir_payload_producto(fila: pd.Series) -> dict | None:
    """
    Construye el diccionario de contexto de un producto para el prompt de la IA.

    Incluye la marca únicamente si su valor normalizado no coincide con
    ``MARCA_GENERICA``, evitando enviar información irrelevante al modelo.

    :param fila: Fila del DataFrame con los datos del producto.
    :type fila: pandas.Series
    :return: Diccionario con los campos ``id_interno``, ``nombre``, ``categoria``
        y opcionalmente ``marca``, o ``None`` si el Label está vacío o es inválido.
    :rtype: dict | None
    """
    id_producto = str(fila.get("Id", "")).strip()
    label = str(fila.get("Label", "")).strip()
    categoria = str(fila.get("Categoria", "")).strip()
    marca = str(fila.get("Marca", "")).strip()

    # Ignorar productos sin nombre válido
    if not label or label.lower() == "nan":
        logger.debug("Producto ignorado por Label vacío.", id=id_producto)
        return None

    payload: dict = {
        "id_interno": id_producto,
        "nombre": label,
        "categoria": categoria,
    }

    # Incluir marca solo si es una marca real (no genérica)
    if marca and marca.lower() != MARCA_GENERICA:
        payload["marca"] = marca

    return payload


# ---------------------------------------------------------------------------
# Lógica de negocio: generación de descripciones por lote
# ---------------------------------------------------------------------------

def generar_lote_ia(
    client: Groq,
    lote_df: pd.DataFrame,
    indice_modelo_actual: int,
) -> tuple[list[dict], int]:
    """
    Solicita a Groq la generación de descripciones para un lote de productos.

    El prompt incluye para cada producto:
      - ``nombre``: extraído de la columna ``Label``.
      - ``categoria``: extraída de la columna ``Categoria``.
      - ``marca``: extraída de ``Marca`` **solo** si no es "Generica".

    Implementa rotación automática de modelos ante errores de cuota (TPD/404)
    y reintentos con espera ante rate-limit (429).

    :param client: Instancia autenticada del cliente de la API de Groq.
    :type client: groq.Groq
    :param lote_df: DataFrame con las columnas ``Id``, ``Label``, ``Categoria``
        y ``Marca`` para el lote a procesar.
    :type lote_df: pandas.DataFrame
    :param indice_modelo_actual: Índice del modelo activo en ``MODELOS_DISPONIBLES``.
    :type indice_modelo_actual: int
    :raises ModelosAgotadosError: Si todos los modelos han agotado su cuota diaria.
    :return: Tupla (lista de resultados IA, índice del modelo usado finalmente).
    :rtype: tuple[list[dict], int]
    """
    productos_input: list[dict] = []

    for _, fila in lote_df.iterrows():
        payload = _construir_payload_producto(fila)
        if payload:
            productos_input.append(payload)

    if not productos_input:
        logger.warning("Lote vacío tras filtrar filas inválidas. Se omite la llamada a la IA.")
        return [], indice_modelo_actual

    prompt = (
        "Eres un copywriter experto en productos para mascotas (tienda de animales). "
        "Genera descripciones para los siguientes productos. "
        "Usa la 'categoria' para orientar el tono (especie objetivo) "
        "y la 'marca' (si aparece) para reforzar la calidad o el fabricante.\n\n"
        f"{json.dumps(productos_input, indent=2, ensure_ascii=False)}\n\n"
        "REGLAS ESTRICTAS:\n"
        "1. corta: Frase comercial directa y atractiva (máx 10 palabras).\n"
        "2. larga: Texto persuasivo enfocado en beneficios para la mascota y el dueño "
        "(mínimo 45 palabras). Si la marca aparece, menciónala de forma natural.\n"
        "3. Idioma: español. Sin exclamaciones excesivas. Tono profesional y cercano.\n\n"
        "RESPONDE EXCLUSIVAMENTE EN JSON con esta estructura exacta:\n"
        '{"productos": [{"id_interno": "...", "corta": "...", "larga": "..."}]}'
    )

    MAX_INTENTOS = 3
    intentos = 0

    while intentos < MAX_INTENTOS:
        modelo_actual = MODELOS_DISPONIBLES[indice_modelo_actual]
        logger.debug(
            "Enviando lote a Groq.",
            modelo=modelo_actual,
            n_productos=len(productos_input),
        )

        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=modelo_actual,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            datos = json.loads(response.choices[0].message.content.strip())
            logger.info(
                "Lote procesado con éxito.",
                modelo=modelo_actual,
                resultados=len(datos.get("productos", [])),
            )
            return datos.get("productos", []), indice_modelo_actual

        except Exception as error:
            error_msg = str(error).lower()

            # Rotación de modelo por cuota agotada o modelo deprecado
            if any(x in error_msg for x in ["tpd", "tokens per day", "400", "404", "decommissioned"]):
                logger.warning(
                    "Modelo no disponible. Rotando al siguiente.",
                    modelo_fallido=modelo_actual,
                    razon=str(error),
                )
                indice_modelo_actual += 1
                if indice_modelo_actual >= len(MODELOS_DISPONIBLES):
                    raise ModelosAgotadosError(
                        "Todos los modelos de Groq han agotado su cuota TPD."
                    )
                continue

            # Reintento por rate-limit (429)
            elif "429" in error_msg or "rate_limit" in error_msg:
                intentos += 1
                logger.warning(
                    "Rate-limit alcanzado. Esperando 20 s antes de reintentar.",
                    intento=intentos,
                    max_intentos=MAX_INTENTOS,
                )
                time.sleep(20)

            else:
                # Error no recuperable para este lote; se devuelve vacío y continúa
                logger.error(
                    "Error inesperado al llamar a Groq. Lote marcado como ERROR_IA.",
                    modelo=modelo_actual,
                    error=str(error),
                )
                return [], indice_modelo_actual

    logger.error(
        "Reintentos agotados por rate-limit para este lote.",
        modelo=modelo_actual,
    )
    return [], indice_modelo_actual


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def procesar_catalogo(archivo_entrada: str, config: ConfiguracionEntorno) -> None:
    """
    Orquesta el procesamiento completo del catálogo de productos:
    carga el archivo, determina los registros pendientes, los procesa en lotes
    y persiste los resultados de forma incremental para permitir reanudación.

    Las columnas de salida escritas en el CSV son ``Descripción corta`` y ``Description``,
    que coinciden con las cabeceras existentes en el fichero original.
    Productos sin descripción generada quedan marcados con el valor ``ERROR_IA``.

    :param archivo_entrada: Ruta al archivo de catálogo (.csv, .xlsx o .xls).
    :type archivo_entrada: str
    :param config: Configuración validada del entorno de ejecución.
    :type config: ConfiguracionEntorno
    :raises ArchivoInventarioError: Si el archivo de entrada no puede leerse.
    :raises ModelosAgotadosError: Si todos los modelos de Groq agotan su cuota.
    :return: None
    """
    client = Groq(api_key=config.groq_api_key)
    archivo_salida = config.archivo_salida
    batch_size = config.batch_size
    indice_modelo_activo = 0

    # --- Carga del catálogo ---
    try:
        if archivo_entrada.lower().endswith((".xlsx", ".xls")):
            df_original = pd.read_excel(archivo_entrada, dtype=str)
        else:
            df_original = pd.read_csv(
                archivo_entrada,
                sep=None,
                engine="python",
                dtype=str,
                encoding="utf-8-sig",
            )
        logger.info(
            "Catálogo cargado.",
            archivo=archivo_entrada,
            total_productos=len(df_original),
        )
    except Exception as error:
        raise ArchivoInventarioError(
            f"No se pudo leer el archivo '{archivo_entrada}': {error}"
        ) from error

    # --- Reanudación: omite productos ya procesados correctamente ---
    if os.path.exists(archivo_salida):
        df_existente = pd.read_csv(archivo_salida, sep=";", dtype=str, encoding="utf-8-sig")
        procesados = df_existente[df_existente["Descripción corta"] != "ERROR_IA"]["Id"].unique()
        df_pendiente = df_original[~df_original["Id"].isin(procesados)].copy()
        logger.info(
            "Reanudando proceso.",
            ya_procesados=len(procesados),
            pendientes=len(df_pendiente),
        )
    else:
        df_pendiente = df_original.copy()

    if df_pendiente.empty:
        logger.info("Catálogo completado. No hay productos pendientes.")
        return

    # --- Procesamiento por lotes ---
    total_lotes = (len(df_pendiente) + batch_size - 1) // batch_size

    for i in tqdm(range(0, len(df_pendiente), batch_size), total=total_lotes, desc="Generando descripciones"):
        lote = df_pendiente.iloc[i: i + batch_size]

        # ModelosAgotadosError se propaga al __main__ para cierre limpio
        res_ia, indice_modelo_activo = generar_lote_ia(client, lote, indice_modelo_activo)

        res_df = lote.copy()

        # Mapeo por id_interno para asignar resultados al lote correcto
        mapeo = {str(item.get("id_interno", "")): item for item in res_ia}

        res_df["Descripción corta"] = res_df["Id"].apply(
            lambda x: mapeo.get(str(x), {}).get("corta", "ERROR_IA")
        )
        res_df["Description"] = res_df["Id"].apply(
            lambda x: mapeo.get(str(x), {}).get("larga", "ERROR_IA")
        )

        es_primero = not os.path.exists(archivo_salida)
        res_df.to_csv(
            archivo_salida,
            mode="a",
            index=False,
            sep=";",
            header=es_primero,
            encoding="utf-8-sig",
        )
        time.sleep(2)

    logger.info("Procesamiento completado.", archivo_salida=archivo_salida)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    MI_API_KEY = "TU_GROQ_API_KEY_AQUI"
    ARCHIVO = "tu_inventario.csv"

    # La clave debe estar en el entorno ANTES de instanciar ConfiguracionEntorno,
    # ya que BaseSettings lee las variables en el momento de la construcción.
    os.environ["GROQ_API_KEY"] = MI_API_KEY

    config = cargar_configuracion()

    try:
        procesar_catalogo(ARCHIVO, config)
    except ArchivoInventarioError as error:
        logger.error("Error al cargar el catálogo.", detalle=str(error))
        sys.exit(1)
    except ModelosAgotadosError as error:
        logger.critical("Proceso detenido: todos los modelos agotados.", detalle=str(error))
        sys.exit(0)
    except Exception as error:
        logger.critical("Error inesperado en el proceso principal.", detalle=str(error))
        sys.exit(1)