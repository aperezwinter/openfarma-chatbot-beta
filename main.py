import os, sys, time, json, uuid, pysqlite3
import streamlit as st
from openai import OpenAI
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

# Loading the vectordatabase
embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
smalldb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding)

client = OpenAI(api_key=OPENAI_API_KEY)

class Thread:
    def __init__(self, client):
        self.thread = client.beta.threads.create()

    def get_num_messages(self, client):
        msg = client.beta.threads.messages.list(thread_id=self.thread.id)
        msg = [m.content[0].text.value for m in msg]
        return len(msg)

def get_tool_outputs(run):
    tool_outputs = []; function_calls = []
    if run.required_action is not None:
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            function_calls.append({
                "id": tool.id,
                "name": tool.function.name,
                "args": json.loads(tool.function.arguments)
            })
            print(f"Function: {tool.function.name}, Args: {tool.function.arguments}")
    for function in function_calls:
        if function["name"] == "extract_data":
            tool_outputs.append({
                "tool_call_id": function["id"], 
                "output": extract_data(function["args"])})
    return tool_outputs

def extract_data(args):
    str_args = str(args)
    retrived_from_vdb = smalldb.similarity_search_with_score(str_args, k=3)
    context = '\n'.join([retrived_from_vdb[i][0].page_content for i in range(3)])
    output = f"""Contestar la pregunta a partir de los DATOS. Restringir la respuesta según la pregunta hecha. \
                Si la pregunta o la respuesta tienen más de un producto, incluir una comparación entre todos ellos en la respuesta. \
                Prohibido incluir precios en la respuesta. Prohibido incluir keywords en la respuesta. \n\
                DATOS: {context}"""
    output = re.sub(' +', ' ', output)
    return output

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
    # embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    # smalldb = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding)

    # Streamlit app configuration
    st.html(streamlit_style)
    st.markdown(
        """
        <style>
        h1 { font-size: 2.5em; }
        h2 { font-size: 2em; }
        h3 { font-size: 1.75em; }
        h4 { font-size: 1.5em; }
        h5 { font-size: 1.25em; }
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

    # create a new thread
    if "thread" not in st.session_state:
        st.session_state.thread = Thread(client)

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
        ## Add user input to the thread
        thread_id =  st.session_state.thread.thread.id
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt_input)

        # Get assistant response
        container = st.empty()
        container.markdown(f'<img src="data:image/gif;base64,{encode_gif(GIF_PATH)}">', unsafe_allow_html=True)

        messages_list = []
        run = client.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=ASSISTANT_ID)
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        while not (run.status in ["completed", "requires_action"]):
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            time.sleep(0.1)

        while run.status == "requires_action":
            tool_outputs = get_tool_outputs(run)
            run = client.beta.threads.runs.submit_tool_outputs(thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            while not (run.status in ["completed", "requires_action"]):
                run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                time.sleep(0.1)

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            for message in messages:
                messages_list.append(message.content[0].text.value)
            response = messages_list[0]
        response = remove_bold_italic(response)
        
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