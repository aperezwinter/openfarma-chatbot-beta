import os, csv, shutil, logging
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from src.parameters import CHROMA_DB_PATH, CSV_PATH, LOG_GENERAL_PATH

# Some logging general configuration
logger = logging.getLogger(name=__name__)
logger.propagate = False
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
handler = logging.FileHandler(os.getcwd() + LOG_GENERAL_PATH)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Define some global variables
file_names = ["cepage.csv", "cetaphil.csv", "eucerin.csv", 
              "eximia.csv", "isdin.csv", "loreal.csv", 
              "lrp.csv", "revlon.csv", "vichy.csv"]
brands = ["Cepage", "Cetaphil", "Eucerin", "Eximia", "Isdin",
          "Loreal", "La Roche-Posay", "Revlon", "Vichy"]

# Load environment variables
_ = load_dotenv(".env")

# Check if the directory exists and remove it
if os.path.exists(CHROMA_DB_PATH):
    shutil.rmtree(CHROMA_DB_PATH)

# Build documents
documents = []
for brand, file_name in zip(brands, file_names):
    try:
        with open(CSV_PATH + file_name, 'r', encoding='utf-8') as file_csv:
            read_csv = csv.reader(file_csv)
            next(read_csv)  # skip header
            for row in read_csv:
                ean = row[0].strip() if row[0] else ''
                documents.append(Document(metadata={'Marca': brand, 'EAN': ean}, page_content=row[1]))
        logger.info(f"Documentos para la marca '{brand}' añadidos desde el archivo {file_name}.")
    except Exception as e:
        logger.error(f"Error procesando el archivo {file_name} para la marca {brand}: {e}")

# Build the vector database
embedding = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
smalldb = Chroma.from_documents(documents=documents, embedding=embedding, persist_directory=CHROMA_DB_PATH)
size = len(smalldb.get()["ids"])
logger.info(f"Embeddings completados. Base de datos Chroma lista con {size} documentos.")