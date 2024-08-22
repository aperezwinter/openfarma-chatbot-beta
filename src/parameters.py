import re, os
import streamlit as st

LOG_PATH_LOCAL      = "/logs/app_local.log"   # local log file path
LOG_PATH_REMOTE     = "/logs/app_remote.log"  # remote log file path
GIF_PATH            = "/figures/loading.gif"  # loading gif path
TIMEOUT             = 1800                                # send email timeout in seconds
USER_AVATAR         = "figures/avatar_usuario.png"        # user avatar figure
BOT_AVATAR          = "figures/avatar_bot_tight.png"      # assistant avatar figure
IMAGE_LOGO          = "figures/header_logo_tight.png"     # logo image
FROM_EMAIL          = "quantitopenfarma@gmail.com"        # email sender
TO_EMAIL            = "quantitopenfarma@gmail.com"        # email receiver
PASSWORD            = "hrci tkoc sdky jepc"               # email password
PERSIST_DIRECTORY   = "database/DB_Chroma"                # embedding database directory
MODEL               = "gpt-4o"                            # "gpt-4o", "gpt-3.5-turbo" set the model to use
OPENAI_API_KEY      = st.secrets["OPENAI_API_KEY"]
USER_CHAT_COLUMNS   = [0.5, 0.5]
BOT_CHAT_COLUMNS    = [0.8, 0.2]

HEADER_CAPTION = re.sub(pattern=' +', repl=' ', 
                        string="""Soy un asistente virtual especializado en dermocosmética. \
                          Podré brindarte información sobre productos, modo de uso, sus beneficios \
                            e ingredientes.""")

# Define some global variables
PERSIST_DIRECTORY   = "database/DB_Chroma"          # embedding database directory
MODEL               = "gpt-4o"                      # "gpt-4o", "gpt-3.5-turbo" set the model to use
OPENAI_API_KEY      = st.secrets["OPENAI_API_KEY"]  # OpenAI API key

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

