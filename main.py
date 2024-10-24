import os, sys, time, uuid, json, csv, pysqlite3
import streamlit as st
from openai import OpenAI
from typing_extensions import override
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from openai import AssistantEventHandler
from src.chatbot import *
from src.tools import *
from src.settings import *
from src.parameters import *

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
LOG_PATH    = REPO_PATH + LOG_PATH_LOCAL    # log file absolute path

# Loading the vectordatabase
embedding = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
database = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding)

def searchByEan(file_name_csv: str, ean_list: list) -> list:
    data = [''] * len(ean_list)
    ean_list = [str(ean) for ean in ean_list]
    ean_map = {str(ean): idx for idx, ean in enumerate(ean_list)}

    with open(file_name_csv, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            ean_actual = row['ean']
            if ean_actual in ean_list:
                idx = ean_map[ean_actual]
                stock = int(round(float(row['stock']))) # stock must be an integer
                data[idx] = f"Stock: {stock}. Precio: ${row['precio']}. Promoción: {row['promo']}."
    file.close()
    return data

def search_in_database(args):
    str_args = str(args)
    retrived_from_vdb = database.similarity_search_with_score(str_args, k=5)
    ean_list = [retrived_from_vdb[i][0].metadata['EAN'] for i in range(5)]
    data = searchByEan(REPO_PATH + "/database/stock.csv", ean_list)
    content = [retrived_from_vdb[i][0].page_content for i in range(5)]
    context = '\n'.join([f"{content[i]} {data[i]}" for i in range(5)])
    output = f"Contexto: {context}"
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
            if function["name"] == "search_in_database":
                tool_outputs.append({
                    "tool_call_id": function["id"], 
                    "output": search_in_database(function["args"])})
        
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

def main():
    
    # Track session with a unique ID and last active time
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.last_active = time.time()
    
    # Set email sending flag
    if 'send_email' not in st.session_state:
        st.session_state.send_email = False

    if 'requires_action_occurred' not in st.session_state:
        st.session_state.requires_action_occurred = False
    
    if 'force_stream' not in st.session_state:
        st.session_state.force_stream = False
    
    # Create thread for the assistant
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    # Streamlit app configuration
    st.html(streamlit_style)
    st.markdown(reinforces_style, unsafe_allow_html=True)
    setHeader(IMAGE_LOGO, HEADER_CAPTION)

    # Add initial message and print the conversation
    if "messages" not in st.session_state:
        st.session_state.messages = []
        addMessage("assistant", INITIAL_MESSAGE)
    printConversation()    

    # User input
    if prompt_input := st.chat_input(ASKING_PROMPT):
        addMessage("user", prompt_input)
        printMessage("user", prompt_input, stream=False)
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=prompt_input)
        st.session_state.send_email = True # Activate email sending condition

        # Get assistant response
        with st.spinner(LOADING_MESSAGE):
            with client.beta.threads.runs.stream(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID,
                event_handler=EventHandler()
            ) as stream:
                stream.until_done()
            
            # Retrieve messages added by the assistant
            response = retrieveLastMessage(client, st.session_state.thread_id)

        # Display assistant response manually (based on requires_action)
        if st.session_state.force_stream:
            printMessage("assistant", response, stream=True)
        addMessage("assistant", response)

    # After a certain time, send an email with the logs
    checkForEmail2Send(REPO_PATH + LOG_CHAT2EMAIL_PATH, subject="Beta chat: Q&A ")

# Run the main function
if __name__ == "__main__":
    main()