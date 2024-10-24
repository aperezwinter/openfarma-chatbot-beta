import os, sys
import logging
import openai
from typing import List
from src.parameters import *

def get_file_paths(directory: str, extension: str = ".pdf") -> List[str]:
    """
    Obtiene todas las rutas de archivos con la extensión especificada en el directorio dado.
    
    Args:
        directory (str): Ruta al directorio donde se encuentran los archivos.
        extension (str, optional): Extensión de archivo a buscar. El valor predeterminado es ".pdf".
        
    Returns:
        List[str]: Una lista con las rutas de archivos que coinciden con la extensión especificada.
    """
    try:
        file_paths = []
        if os.path.exists(directory):
            for file in os.listdir(directory):
                if file.endswith(extension):
                    file_path = os.path.join(directory, file)
                    file_paths.append(file_path)
                    logging.info(f"Archivo añadido: {file_path}")
        else:
            print(os.getcwd())
            logging.warning(f"El directorio no existe: {directory}")
        return file_paths
    except Exception as e:
        logging.error(f"Error al obtener archivos desde {directory}: {str(e)}")
        return []

def process_files(
    client: openai.OpenAI, 
    vector_store, 
    file_path_batches: List[List[str]], 
    name: str = "VectorStore"
) -> None:
    """
    Sube lotes de archivos a la tienda de vectores de OpenAI.
    
    Args:
        client (openai.OpenAI): Cliente de OpenAI inicializado con la clave API.
        vector_store (openai.VectorStore): Objeto de la tienda de vectores donde se subirán los archivos.
        file_path_batches (List[List[str]]): Lista de lotes de archivos, donde cada lote es una lista de rutas de archivos.
        name (str, opcional): El nombre de la tienda de vectores. El valor predeterminado es "VectorStore".
    """
    for file_paths in file_path_batches:
        try:
            file_streams = [open(path, "rb") for path in file_paths]
            # Subir y esperar el estado del lote de archivos.
            file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            status = file_batch.status
            num_files_completed = file_batch.file_counts.completed
            num_files = file_batch.file_counts.total
            logging.info(f"Estado de subida: {status}. {num_files_completed}/{num_files} archivos a la base vectorizada {name}.")
        except Exception as e:
            logging.error(f"Error al subir archivos a la base vectorizada: {str(e)}")

def main() -> None:
    """
    Función principal que coordina la obtención de rutas de archivos, la inicialización del cliente de OpenAI,
    la creación de la base vectorizada y la subida de archivos.

    Args:
        *args: Argumentos posicionales opcionales.
        **kwargs: Argumentos clave-valor opcionales, como 'pdf_folder', 'txt_folder', 'nombre'.

    Ejemplos de uso desde la terminal:
    
    1. Usando valores por defecto:
        ```bash
        python script.py
        ```
    
    2. Especificando una carpeta personalizada para los PDFs:
        ```bash
        python script.py pdf_folder=path_to_pdf
        ```
    
    3. Especificando una carpeta personalizada para los TXTs:
        ```bash
        python script.py txt_folder=path_to_txt
        ```
    
    4. Cambiando el nombre de la base de datos vectorial:
        ```bash
        python script.py nombre=MiNuevaBaseDeDatos
        ```
    
    5. Usando múltiples argumentos:
        ```bash
        python script.py pdf_folder=path_to_pdf txt_folder=path_to_txt nombre=MiNuevaBaseDeDatos
        ```

    6. Definiendo la carpeta raíz desde donde se encuentran las subcarpetas `pdf` y `txt`:
        ```bash
        python script.py folder=/ruta/alternativa/
        ```
    """
    # Start logging
    logging.info("Iniciando el proceso de creación de la base de datos vectorial...")
    
    # Obtener argumentos opcionales desde kwargs o usar valores por defecto
    folder = kwargs.get('folder', os.getcwd() + "/database/rag/")
    pdf_folder = kwargs.get('pdf_folder', os.path.join(folder, "pdf/"))
    txt_folder = kwargs.get('txt_folder', os.path.join(folder, "txt/"))
    name_vd = kwargs.get('nombre', 'Vademecum_rag')

    # Get all pdf and csv files from respective folders.
    pdf_files = get_file_paths(pdf_folder, '.pdf')
    txt_files = get_file_paths(txt_folder, '.txt')
    file_paths = pdf_files + txt_files

    # Split file paths into batches of n.
    n = 5
    file_path_batches = [file_paths[i: i + n] for i in range(0, len(file_paths), n)]

    # Initialize OpenAI client
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        logging.info("Cliente de OpenAI inicializado.")
    except Exception as e:
        logging.error(f"Error al inicializar el cliente de OpenAI: {str(e)}")
        return

    # Create a new vector store
    try:
        vector_store = client.beta.vector_stores.create(name=name_vd)
        logging.info(f"Base de datos vectorial '{name_vd}' creada.")
    except Exception as e:
        logging.error(f"Error al crear la base de datos vectorial : {str(e)}")
        return

    # Upload files to vector store
    process_files(client, vector_store, file_path_batches, name_vd)

    # Finish logging
    logging.info("Proceso de creación de la base de datos vectorial finalizado.")

if __name__ == "__main__":
    # Global logging configuration (main log file)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("./logs/main.log"),
        ]
    )
    
    kwargs = {}
    for arg in sys.argv[1:]:
        key, value = arg.split('=')
        kwargs[key] = value
    main(**kwargs)