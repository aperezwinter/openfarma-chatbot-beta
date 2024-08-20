import os, sys, re, time
import pysqlite3, time, uuid
import streamlit as st
from datetime import datetime
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from src.assistant import *

REPO_PATH = os.getcwd()             # get current working directory
LOG_FILE = "/logs/app_remote.log"   # log file path
LOG_PATH = REPO_PATH + LOG_FILE     # log file absolute path
TIMEOUT = 60                        # session timeout in seconds

FROM_EMAIL = "quantitopenfarma@gmail.com" # email sender
TO_EMAIL = "quantitopenfarma@gmail.com"  # email receiver
PASSWORD = "ypun odlt sbsp cuev"       # email password

# Trick to update sqlite
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PERSIST_DIRECTORY, 'db.sqlite3'),
    }
}

def main(**kwargs):
    # Get logger
    logger = kwargs.get("logger")
    
    # Track session with a unique ID and last active time
    #if 'session_id' not in st.session_state:
    #    st.session_state.session_id = get_remote_ip()
    #    st.session_state.last_active = time.time()
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.last_active = time.time()
    
    if 'num_lines' not in st.session_state:
        with open(LOG_PATH, "r") as file:
            st.session_state.num_lines = len(file.readlines())
        file.close()

    # loading the vectordatabase
    embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    smalldb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding)

    # Streamlit app configuration
    header = "openfarmAI"
    image_logo = "figures/logo_openfarma.svg"
    footnote = """Soy un asistente virtual especializado en dermocosmética. \
        Podré brindarte información sobre productos, modo de uso, sus beneficios \
            e ingredientes."""
    footnote = re.sub(' +', ' ', footnote)
    hide_streamlit_style = """
                    <style>
                    div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
                    div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
                    div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
                    #MainMenu {visibility: hidden; height: 0%;}
                    header {visibility: hidden; height: 0%;}
                    footer {visibility: hidden; height: 0%;}
                    </style>
                    """

    st.html(
    """
        <style>    
        div[data-testid="stChatMessage"] {
            background-color: white;
            border-style: solid;
            border-color: black;
            border-width: 2px;
            color: black; # Adjust this for expander header color
        }
    """)

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    st.markdown(f"""<h1 style="color:{OLIVE}; position:absolute; top:-70px;"> {header} </h1>""", unsafe_allow_html=True)
    #left, right = st.columns([1.2, 7.0])
    #with left:
    #    st.markdown(f'<p class="powered-by" style="color: {BLACK}; font-weight: bold;"> Powered by</p>', unsafe_allow_html=True)
    #with right:
    #    st.image(image_logo, width=150)
    st.markdown(get_chat_message(footnote), unsafe_allow_html=True)
    # set_background('figures/watermark_spaced.jpg')

    # session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        initial_message = "Hola, ¿en qué puedo ayudarte hoy?"
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
        logger.info(f"[id:{st.session_state.session_id}] BOT: {initial_message}")  # log initial message from assistant

    # conversation
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(get_chat_message(message["content"]), unsafe_allow_html=True)

    # user input
    if prompt_input := st.chat_input("Hacé tu pregunta"):
        logger.info(f"[id:{st.session_state.session_id}] PROMPT: {prompt_input}")  # log user prompt
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user", avatar=USER_AVATAR):
            st.markdown(get_chat_message(prompt_input), unsafe_allow_html=True)

        # Get assistant response
        k = 30 # number of results to retrieve
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            retrived_from_vdb = smalldb.similarity_search_with_score(prompt_input, k=k)
            context = '\n'.join([retrived_from_vdb[i][0].page_content for i in range(k)])
            response = build_prompt(context, prompt_input)
            response = st.write_stream(response)  # write text into the screen by stream (like a chat)
            logger.info(f"[id:{st.session_state.session_id}] BOT: {response}")  # log assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})

    # Call the function to push logs to GitHub if timeout is reached
    if time.time() - st.session_state.last_active >= TIMEOUT:
        st.session_state.last_active = time.time() # update last active time
        with open(LOG_PATH, "r") as file:
            lines = file.readlines()
            if len(lines) > st.session_state.num_lines:
                st.session_state.num_lines = len(lines)
                today = datetime.now().strftime("%Y-%m-%d")
                subject = f"BETA chat: Q&A " + today
                body = ''.join(lines)
                send_email(FROM_EMAIL, TO_EMAIL, PASSWORD, subject, body) # send email with logs
        file.close()

# Run the main function
if __name__ == "__main__":
    main(logger = init_logging(LOG_PATH))