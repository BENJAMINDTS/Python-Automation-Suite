"""
Módulo de Procesamiento Masivo IA con Rotación Automática y Tolerancia a Fallos.

Se conecta a la API de Groq para generar descripciones de productos.
Implementa rotación automática de modelos (Fallback) si un modelo se queda
sin cuota o está retirado. Los fallos se registran como 'ERROR_IA' para no
perder el hilo del inventario.

@author: BenjaminDTS
"""

import pandas as pd
from groq import Groq
import os
import time
import json
import sys
from tqdm import tqdm

# ==========================================
# CONFIGURACIÓN DE MODELOS
# ==========================================
MODELOS_DISPONIBLES = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
    "deepseek-r1-distill-llama-70b"
]

ARCHIVO_SALIDA = "inventario_con_descripciones.csv"

# ==========================================
# 1. COMUNICACIÓN CON LA IA (GROQ)
# ==========================================

def generar_lote_ia(client, lote_df, idx_modelo):
    """
    Prepara los datos y orquesta la llamada a la IA con tolerancia a fallos.
    
    :param client: Groq. Cliente autenticado.
    :param lote_df: DataFrame. Subconjunto de productos.
    :param idx_modelo: int. Índice del modelo actual.
    :return: tuple (list, int). Lista de resultados JSON y el índice del modelo.
    """
    productos_input = preparar_datos_entrada(lote_df)
    if not productos_input:
        return [], idx_modelo

    prompt = construir_prompt(productos_input)
    return ejecutar_con_rotacion(client, prompt, idx_modelo)

def ejecutar_con_rotacion(client, prompt, idx_modelo):
    """
    Intenta llamar a la API rotando de modelo automáticamente si hay errores.
    
    :param client: Groq. Cliente de conexión.
    :param prompt: str. Instrucciones para la IA.
    :param idx_modelo: int. Índice del modelo en uso.
    :return: tuple. (Resultados, Nuevo Índice del Modelo).
    """
    intentos = 0
    while intentos < 3:
        try:
            modelo = MODELOS_DISPONIBLES[idx_modelo]
            datos = invocar_modelo(client, prompt, modelo)
            return datos.get("productos", []), idx_modelo
        except Exception as e:
            idx_modelo, intentos, continuar = analizar_error(e, idx_modelo, intentos)
            if not continuar: break
    return [], idx_modelo

def invocar_modelo(client, prompt, modelo):
    """
    Realiza la petición HTTP a la API de Groq y extrae el JSON limpio.
    
    :param client: Groq. Cliente API.
    :param prompt: str. Texto a procesar.
    :param modelo: str. Nombre del modelo (ej. 'llama-3.3-70b-versatile').
    :return: dict. Respuesta parseada desde formato JSON.
    """
    print(f"\n[DEBUG] Consultando {modelo}...")
    res = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=modelo, response_format={"type": "json_object"}, temperature=0.3
    )
    texto = res.choices[0].message.content.replace('```json', '').replace('```', '').strip()
    return json.loads(texto)

def analizar_error(error, idx, intentos):
    """
    Evalúa el error para decidir si rotar de modelo, esperar o abortar.
    
    :param error: Exception. Error capturado.
    :param idx: int. Índice del modelo actual.
    :param intentos: int. Número de intentos gastados.
    :return: tuple (int, int, bool). (Nuevo idx, Nuevos intentos, ¿Continuar bucle?).
    """
    msg = str(error).lower()
    print(f"[!] ERROR: {msg}")
    
    if any(x in msg for x in ["tpd", "tokens per day", "decommissioned", "400", "404"]):
        idx += 1
        if idx >= len(MODELOS_DISPONIBLES):
            sys.exit("[!!!] Cuota de TODOS los modelos agotada por hoy. Abortando.")
        return idx, intentos, True  # Rotar modelo no gasta intento
        
    if "429" in msg or "rate_limit" in msg:
        print("[DEBUG] Límite por minuto. Esperando 15s...")
        time.sleep(15)
        return idx, intentos + 1, True
        
    return idx, 3, False  # Error desconocido, forzar salida del bucle

# ==========================================
# 2. PREPARACIÓN DE DATOS (MAPPING)
# ==========================================

def preparar_datos_entrada(lote_df):
    """
    Filtra y formatea los productos válidos de un DataFrame para el Prompt.
    
    :param lote_df: DataFrame. Lote de filas de Excel.
    :return: list. Lista de diccionarios con id, nombre y categoría.
    """
    validos = lote_df.dropna(subset=['Producto'])
    validos = validos[validos['Producto'].str.strip() != '']
    return [
        {"id_interno": str(f.get('Código', '')).strip(),
         "nombre": str(f.get('Producto', '')).strip(),
         "categoria": str(f.get('Departamento', '')).strip()}
        for _, f in validos.iterrows()
    ]

def construir_prompt(productos_input):
    """
    Genera el texto maestro de instrucciones para el Copywriter IA.
    
    :param productos_input: list. Productos limpios en diccionario.
    :return: str. Prompt estructurado con inyección de JSON.
    """
    json_str = json.dumps(productos_input, indent=2)
    return (
        "Actúa como un copywriter experto en tiendas de mascotas. Genera descripciones "
        f"atractivas, considerando la categoría de estos productos:\n\n{json_str}\n\n"
        "REGLAS: 1. Corta (máx 10 palabras). 2. Larga (+40 palabras de beneficios). "
        "Si no hay departamento, deduce el animal. "
        "RESPONDE SOLO EN JSON: {\"productos\": [{\"id_interno\": \"\", \"corta\": \"\", \"larga\": \"\"}]}"
    )

# ==========================================
# 3. ORQUESTACIÓN Y MANEJO DE ARCHIVOS
# ==========================================

def procesar_inventario_maestro(archivo_in, api_key):
    """
    Controlador principal: lee origen, gestiona reanudación y lanza el procesado.
    
    :param archivo_in: str. Ruta del archivo CSV o Excel original.
    :param api_key: str. Clave de autenticación de Groq.
    :return: None
    """
    client = Groq(api_key=api_key)
    df_pendiente = cargar_datos_pendientes(archivo_in)
    
    if df_pendiente is None or df_pendiente.empty:
        print("\n[OK] Inventario completado o sin datos que procesar.")
        return

    print(f"--- Faltan {len(df_pendiente)} productos por procesar ---")
    procesar_lotes(client, df_pendiente)

def cargar_datos_pendientes(archivo_in):
    """
    Lee el archivo de origen y descarta los registros que ya fueron procesados.
    
    :param archivo_in: str. Ruta del archivo base.
    :return: DataFrame. Los registros que aún no han sido pasados por la IA.
    """
    try:
        if archivo_in.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(archivo_in, dtype=str)
        else:
            df = pd.read_csv(archivo_in, sep=None, engine='python', dtype=str, encoding='utf-8-sig')
            
        if os.path.exists(ARCHIVO_SALIDA):
            df_listo = pd.read_csv(ARCHIVO_SALIDA, sep=';', dtype=str, encoding='utf-8-sig')
            ok_codes = df_listo[df_listo['Desc_Corta'] != 'ERROR_IA']['Código'].unique()
            return df[~df['Código'].isin(ok_codes)].copy()
        return df
    except Exception as e:
        print(f"[!] Error leyendo archivos: {e}")
        return None

def procesar_lotes(client, df_pendiente, batch_size=10):
    """
    Itera sobre el DataFrame pendiente, consulta a la IA por bloques y guarda.
    
    :param client: Groq. Cliente IA.
    :param df_pendiente: DataFrame. Datos restantes.
    :param batch_size: int. Número de productos a enviar por petición (def: 10).
    :return: None
    """
    idx_modelo = 0
    for i in tqdm(range(0, len(df_pendiente), batch_size), desc="Procesando lotes"):
        lote = df_pendiente.iloc[i : i + batch_size]
        resultados, idx_modelo = generar_lote_ia(client, lote, idx_modelo)
        
        guardar_resultados(lote, resultados)
        time.sleep(3) # Respetar límites API

def guardar_resultados(lote_df, resultados_ia):
    """
    Fusiona el JSON devuelto por la IA con el DataFrame original y lo guarda.
    
    :param lote_df: DataFrame. Las filas originales del lote.
    :param resultados_ia: list. La lista de diccionarios devuelta por Groq.
    :return: None
    """
    res_df = lote_df.copy()
    mapa = {str(item.get('id_interno', '')): item for item in resultados_ia}
    
    res_df['Desc_Corta'] = res_df['Código'].apply(lambda x: mapa.get(x, {}).get('corta', 'ERROR_IA'))
    res_df['Desc_Larga'] = res_df['Código'].apply(lambda x: mapa.get(x, {}).get('larga', 'ERROR_IA'))
    
    header = not os.path.exists(ARCHIVO_SALIDA)
    res_df.to_csv(ARCHIVO_SALIDA, mode='a', index=False, sep=';', header=header, encoding='utf-8-sig')

# ==========================================
# EJECUCIÓN DEL SCRIPT
# ==========================================
if __name__ == "__main__":
    MI_API_KEY = "TU_API_KEY_AQUI" 
    ARCHIVO = "nombre_del_archivo.xlsx" 
    procesar_inventario_maestro(ARCHIVO, MI_API_KEY)