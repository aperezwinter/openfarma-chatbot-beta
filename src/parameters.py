import re
import streamlit as st

# Log file paths
LOG_PATH_LOCAL      = "/logs/app_local.log"         # local log file path
LOG_PATH_REMOTE     = "/logs/app_remote.log"        # remote log file path
LOG_GENERAL_PATH    = "/logs/main.log"              # general log file path
LOG_EMAIL_PATH      = "/logs/email.log"             # email log file path
LOG_CHAT_PATH       = "/logs/chat.log"              # chat log file path
LOG_CHAT2EMAIL_PATH = "/logs/chat_to_email.log"     # chat to email log file path

# Figure paths
USER_AVATAR = "figures/avatar_user.png"     # user avatar figure
BOT_AVATAR  = "figures/avatar_bot.png"      # assistant avatar figure
IMAGE_LOGO  = "figures/header_logo.png"     # logo image

# Email parameters
TIMEOUT     = 600                               # send email timeout in seconds
FROM_EMAIL  = "quantitopenfarma@gmail.com"      # email sender
TO_EMAIL    = "quantitopenfarma@gmail.com"      # email receiver
PASSWORD    = "hrci tkoc sdky jepc"             # email password

# OpenAI API parameters
MODEL           = "gpt-4o"                      # "gpt-4o", "gpt-3.5-turbo" set the model to use
OPENAI_API_KEY  = st.secrets["OPENAI_API_KEY"]
ASSISTANT_ID    = st.secrets["ASSISTANT_ID"]

# Database parameters
CSV_PATH            = "database/csv/"                # csv database path
PERSIST_DIRECTORY   = "database/DB_Chroma"          # embedding database directory
CHROMA_DB_PATH      = "database/chroma/byProduct"   # Chroma database path


# Chatbot parameters
HEADER_CAPTION = re.sub(pattern=' +', repl=' ', 
                        string="""Soy un asistente virtual especializado en dermocosmética. \
                                  Podré brindarte información sobre productos, modo de uso, sus beneficios \
                                  e ingredientes.""")
INITIAL_MESSAGE = "Hola, ¿en qué puedo ayudarte hoy?"
ASKING_PROMPT = "Hacé tu pregunta"
LOADING_MESSAGE = "Estoy buscando la información que necesitás..."
INSTRUCTIONS = re.sub(pattern=' +', 
                      repl=' ', 
                      string="""Por favor responder la pregunta del usuario siguiendo la conversación \
                                en el Thread. Además, utilizar la información dada en los archivos. De \
                                ser necesario, repreguntar al usuario para obtener más información.""")

# Streamlit configuration
USER_CHAT_COLUMNS   = [0.5, 0.5]
BOT_CHAT_COLUMNS    = [0.8, 0.2]


# HTML color codes
GRAY      = "#F1F1F1"
GREEN     = "#8EA749"
ORANGE    = "#FF5733"
BLACK     = "#000000"
WHITE     = "#FFFFFF"
RED       = "#FF0000"
OLIVE     = "#8EA749"
BOT_BOX   = "#F0F0F5"
USER_BOX  = "#E6FFE6"