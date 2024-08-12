# import packages
import openai, os, shutil
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.docstore.document import Document

# Load environment variables
_ = load_dotenv(".env")

# Define some global variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"] # openAI api key
PERSIST_DIRECTORY = "database/DB_Chroma" # embedding database directory

filenames = ["cepage_all", "cetaphil_all", "eucerin_all", 
             "eximia_all", "isdin_all", "loreal_all", 
             "la roche-posay_all", "revlon_all", "vichy_all"]
brands = ["Cepage", "Cetaphil", "Eucerin", "Eximia", "Isdin", 
          "Loreal", "La Roche-Posay", "Revlon", "Vichy"]


# Check if the directory exists and remove it
if os.path.exists(PERSIST_DIRECTORY):
    shutil.rmtree(PERSIST_DIRECTORY)

# Build documents
documents = []
for brand, filename in zip(brands, filenames):
    with open(f"./database/txt/{filename}.txt", 'r', encoding='utf-8') as file:
        lines = file.read()
        for line in lines.split("\n"):
            # pre-format documents to then pass them to the vector database
            documents.append(Document(metadata={"metadato": f'{brand}'}, page_content=line))

# Build the vectordatabase
embedding = OpenAIEmbeddings()
smalldb = Chroma.from_documents(documents=documents, embedding=embedding, persist_directory=PERSIST_DIRECTORY)

# plot some information
size = len(smalldb.get()["ids"])
print(f"Embeddings done. Chroma database ready with {size} documents.")