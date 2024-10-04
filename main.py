import os, sys, time, uuid, pysqlite3, json
import streamlit as st
from openai import OpenAI
from datetime import datetime
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from typing_extensions import override
from openai import AssistantEventHandler
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
    retrived_from_vdb = smalldb.similarity_search_with_score(str_args, k=8)
    context = '\n'.join([retrived_from_vdb[i][0].page_content for i in range(8)])
    output = f"Consulta: {str_args}\nContexto: {context}\nExtra: Responder sin precios \
        ni keywords, realizar comparación entre productos si hay más de uno."
    output = re.sub(' +', ' ', output)
    return output

class EventHandler(AssistantEventHandler):
    
    @override
    def on_event(self, event):
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            st.session_state.requires_action_occurred = True
            self.handle_requires_action(event.data, run_id)
        elif event.event == 'thread.run.completed':
            if st.session_state.requires_action_occurred:
                st.session_state.requires_action_occurred = False
                st.session_state.force_stream = False
            else:
                st.session_state.force_stream = True
    
    def handle_requires_action(self, data, run_id):
        tool_outputs = []
        function_calls = []

        for tool in data.required_action.submit_tool_outputs.tool_calls:
            function_calls.append({
                "id": tool.id,
                "name": tool.function.name,
                "args": json.loads(tool.function.arguments)
            })
        for function in function_calls:
            if function["name"] == "extract_data":
                tool_outputs.append({
                    "tool_call_id": function["id"], 
                    "output": extract_data(function["args"])})
        
        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)
 
    def submit_tool_outputs(self, tool_outputs, run_id):
        # Use the submit_tool_outputs_stream helper
        with client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            event_handler=EventHandler(),
        ) as stream:
            left, _ = st.columns(BOT_CHAT_COLUMNS)
            with left:
                with st.chat_message("assistant", avatar=BOT_AVATAR):
                    container = st.empty()
                    current_text = ""
                    for text in stream.text_deltas:
                        current_text += text
                        container.markdown(f'<div class="chat-message bot-message bot-message ul">{current_text}</div>', unsafe_allow_html=True)
                        time.sleep(0.05)
                    #self.st_container.markdown(f'<div class="chat-message bot-message bot-message ul">{current_text}</div>', unsafe_allow_html=True)

client = OpenAI(api_key=OPENAI_API_KEY)

def main(**kwargs):
    logger = kwargs.get("logger") # get logger from kwargs
    enlapsed_time = {}
    
    # Track session with a unique ID and last active time
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.last_active = time.time()
    
    if 'num_lines' not in st.session_state:
        with open(LOG_PATH, "r") as file:
            st.session_state.num_lines = len(file.readlines())
        file.close()

    if 'requires_action_occurred' not in st.session_state:
        st.session_state.requires_action_occurred = False
    
    if 'force_stream' not in st.session_state:
        st.session_state.force_stream = False

    # Streamlit app configuration
    st.html(streamlit_style)
    st.markdown(
        """
        <style>
        h1 { font-size: 3em; }
        h2 { font-size: 2.5em; }
        h3 { font-size: 2em; }
        h4 { font-size: 1.75em; }
        h5 { font-size: 1.5em; }
        h6 { font-size: 1.25em; }
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
    st.markdown(f"""<div class="header-caption">{HEADER_CAPTION}</div>""", unsafe_allow_html=True)
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        initial_message = "Hola, ¿en qué puedo ayudarte hoy?"
        st.session_state.messages.append({"role": "assistant", "content": initial_message})
        logger.info(f"[id:{st.session_state.session_id}] BOT: {initial_message}")
    
    # Create thread for the assistant
    if "thread" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

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

        # Add user input to the thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, 
            role="user", 
            content=prompt_input,
        )

        # Get assistant response
        instructions = "Por favor responder la pregunta del usuario siguiendo la conversación en el Thread. \
            Además, utilizar la información dada en los archivos. De ser necesario, repreguntar al usuario \
                para obtener más información."
        instructions = re.sub(' +', ' ', instructions)
        with st.spinner("Generando respuesta..."):
            start_time = time.time()
            with client.beta.threads.runs.stream(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID,
                event_handler=EventHandler()
            ) as stream:
                stream.until_done()
            enlapsed_time["run_stream"] = time.time() - start_time

            for key, value in enlapsed_time.items():
                print(f"{key}:\t{value:.2f} seconds")
            
            # Retrieve messages added by the assistant
            messages = list(client.beta.threads.messages.list(thread_id=thread.id))
            message_content = messages[0].content[0].text
            annotations = message_content.annotations
            for annotation in annotations:
                message_content.value = message_content.value.replace(annotation.text, f"")
            response = remove_bold_italic(message_content.value)

        # Process and display assistant messages
        if st.session_state.force_stream:
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