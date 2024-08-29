import os, sys, time, uuid, pysqlite3
import streamlit as st
from datetime import datetime
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from src.parameters import *
from src.assistant import *
from src.settings import *

# Trick to update sqlite
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PERSIST_DIRECTORY, 'db.sqlite3'),
    }
}

REPO_PATH   = os.getcwd()                   # get current working directory
LOG_PATH    = REPO_PATH + LOG_PATH_REMOTE   # log file absolute path
GIF_PATH    = REPO_PATH + GIF_PATH          # gif file absolute path

def main(**kwargs):
    logger = kwargs.get("logger") # get logger from kwargs
    
    # Track session with a unique ID and last active time
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.last_active = time.time()
    
    if 'num_lines' not in st.session_state:
        with open(LOG_PATH, "r") as file:
            st.session_state.num_lines = len(file.readlines())
        file.close()

    # Loading the vectordatabase
    embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    smalldb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding)

    # Streamlit app configuration
    st.html(streamlit_style)
    st.markdown(
        """
        <style>
        h1 { font-size: 2em; }
        h2 { font-size: 1.8em; }
        h3 { font-size: 1.6em; }
        h4 { font-size: 1.4em; }
        h5 { font-size: 1.2em; }
        h6 { font-size: 1em; }
        strong { font-weight: bold; font-size: 20px; }
        em { font-style: italic; font-size: 20px; }
        ul li::marker, ol li::marker { font-size: 20px; }
        ul li, ol li { font-size: 20px; }
        ul * { font-size: 20px; }
        ol * { font-size: 20px; }
        li { font-size: 20px; }
        li * { font-size: 20px; }
        li span { font-size: 20px; }
        span { font-size: 20px; }
        p { font-size: 20px; }
        </style>
        """,
        unsafe_allow_html=True
    )
    img_header = encode_image(custom_image(IMAGE_LOGO))
    st.markdown(f"""
        <div class="fixed-header">
            <div class="header-content">
                <img src="data:image/jpeg;base64,{img_header}" class="header-image">
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown(f"""<div class="header-caption"><p>{HEADER_CAPTION}</p></div>""", unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        initial_message = "Hola, ¿en qué puedo ayudarte hoy?"
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
        logger.info(f"[id:{st.session_state.session_id}] BOT: {initial_message}")

    # conversation
    for message in st.session_state.messages:
        role = message["role"]; msg = message["content"]
        if role == "user":
            avatar = USER_AVATAR
            _, right = st.columns(USER_CHAT_COLUMNS)
            with right:
                with st.chat_message(role, avatar=avatar):
                    st.markdown(f'<div class="chat-message user-message">{msg}</div>', unsafe_allow_html=True)
            st.write("")
        else:
            avatar = BOT_AVATAR
            left, _ = st.columns(BOT_CHAT_COLUMNS)
            with left:
                with st.chat_message(role, avatar=avatar):
                    st.markdown(f'<div class="chat-message bot-message">{msg}</div>', unsafe_allow_html=True)
            st.write("")

    # user input
    if prompt_input := st.chat_input("Hacé tu pregunta"):
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        logger.info(f"[id:{st.session_state.session_id}] USER: {prompt_input}")
        _, right = st.columns(USER_CHAT_COLUMNS)
        with right:
            with st.chat_message(role, avatar=USER_AVATAR):
                st.markdown(f'<div class="chat-message user-message">{prompt_input}</div>', unsafe_allow_html=True)
        st.write("")

        # Get assistant response
        k = 30 # number of results to retrieve
        container = st.empty()
        container.markdown(f'<img src="data:image/gif;base64,{encode_gif(GIF_PATH)}">', unsafe_allow_html=True)
        retrived_from_vdb = smalldb.similarity_search_with_score(prompt_input, k=k)
        context = '\n'.join([retrived_from_vdb[i][0].page_content for i in range(k)])
        response = build_prompt(context, prompt_input)
        container.markdown('<div></div>', unsafe_allow_html=True)
        left, _ = st.columns(BOT_CHAT_COLUMNS)
        with left:
            with st.chat_message("assistant", avatar=BOT_AVATAR):
                stream_markdown(response, role="assistant")
        st.session_state.messages.append({"role": "assistant", "content": response})
        logger.info(f"[id:{st.session_state.session_id}] BOT: {response}")
        st.write("")

    # After a certain time, send an email with the logs
    if time.time() - st.session_state.last_active >= TIMEOUT:
        st.session_state.last_active = time.time()
        with open(LOG_PATH, "r") as file:
            lines = file.readlines()
            if len(lines) > st.session_state.num_lines:
                st.session_state.num_lines = len(lines)
                today = datetime.now().strftime("%Y-%m-%d")
                subject = "Beta chat: Q&A " + today
                body = ''.join(lines)
                send_email(FROM_EMAIL, TO_EMAIL, PASSWORD, subject, body)
        file.close()

# Run the main function
if __name__ == "__main__":
    main(logger = init_logging(LOG_PATH))