import os, re, time, logging
import base64, subprocess, smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from streamlit import runtime
from streamlit.runtime.scriptrunner import get_script_run_ctx
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Define some global variables
PERSIST_DIRECTORY   = "database/DB_Chroma"          # embedding database directory
MODEL               = "gpt-4o"                      # "gpt-4o", "gpt-3.5-turbo" set the model to use
OPENAI_API_KEY      = st.secrets["OPENAI_API_KEY"]  # OpenAI API key
USER_AVATAR         = "figures/user_icon.png"
BOT_AVATAR          = "figures/ai_icon.png"

# HTML color codes
GREEN   = "#8EA749"
ORANGE  = "#FF5733"
BLACK   = "#000000"
WHITE   = "#FFFFFF"
RED     = "#FF0000"
OLIVE   = "#8EA749"

def get_chat_message(content, color=BLACK, bold=False):
    if bold:
        return f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <div style="background-color: {WHITE}; padding: 10px; border-radius: 10px;">
            <p style="margin: 0; color: {color}; font-weight: bold;"> {content}</p>
            </div>
            </div>"""
    else:
        return f"""
            <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <div style="background-color: {WHITE}; padding: 10px; border-radius: 10px;">
            <p style="margin: 0; color: {color};"> {content}</p>
            </div>
            </div>"""

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
    background-image: url("data:image/png;base64,%s");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

def response_stream(response):
    for line in response.splitlines():
        for word in line.split():
            yield f"**{word}**" + " "
            time.sleep(0.05)  # time processing delay
        yield "\n"  # add a new line after each line

def split_string_to_lines(input_string, line_length):
    words = input_string.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line) + len(word) + 1 <= line_length:
            current_line += (word + " ")
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    if current_line:
        lines.append(current_line.strip())
    
    return "\n".join(lines)

def build_prompt(context, question):
    parser = StrOutputParser()
    template = """ROL: Analista asistente experto en cosmética.\n\
                  ORIENTACIÓN: Productos de belleza, cuidado personal y cosmética.\n\
                  INSTRUCCIONES: Contestar la PREGUNTA a partir de los DATOS. Restringir la respuesta según la pregunta hecha. \
                    Si la pregunta o la respuesta tienen más de un producto, incluir una comparación entre todos ellos en la respuesta. \
                        Prohibido incluir precios en la respuesta. Prohibido incluir keywords en la respuesta. \n\
                  DATOS: {context}\n\
                  PREGUNTA: {question}
                """
    template = re.sub(' +', ' ', template)
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | ChatOpenAI(openai_api_key=OPENAI_API_KEY, model=MODEL) | parser
    #return chain.invoke({"context": context, "question": question})
    #return chain.stream({"chat_history": context, "user_question": question})
    return chain.stream({"context": context, "question": question})

def get_remote_ip() -> str:
    """Get remote ip."""
    try:
        ctx = get_script_run_ctx()
        if ctx is None:
            return None
        session_info = runtime.get_instance().get_client(ctx.session_id)
        if session_info is None:
            return None
    except Exception as e:
        return None

    return session_info.request.remote_ip

class ContextFilter(logging.Filter):
    def filter(self, record):
        # record.user_ip = get_remote_ip()
        record.user_ip = st.session_state.session_id
        return super().filter(record)

def init_logging(log_file: str):
    # Make sure to instanciate the logger only once
    # otherwise, it will create a StreamHandler at every run
    # and duplicate the messages

    # create a custom logger
    logger = logging.getLogger(__name__)
    if logger.handlers:  # logger is already setup, don't setup again
        return logger
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    # in the formatter, use the variable "user_ip"
    format_msg = '%(asctime)s - [user_ip=%(user_ip)s] - %(message)s'
    format_time = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(format_msg, format_time)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    handler.addFilter(ContextFilter())
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# Function to push log to GitHub
def push_log_to_github(file_name: str, repo_path: str, commit_message: str="update log file"):
    os.chdir(repo_path)
    subprocess.run(["git", "add", file_name]) # stage the log files
    subprocess.run(["git", "commit", "-m", commit_message]) # commit the log file
    subprocess.run(["git", "push", "origin", "main"]) # push to the repo


def send_email(from_email: str, to_email: str, password: str, subject: str, body: str) -> None:
    # Setup the MIME
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    
    # Attach the body with the msg instance
    message.attach(MIMEText(body, 'plain'))

    # Create SMTP session for sending the mail
    try:
        session = smtplib.SMTP('smtp.gmail.com', 587)   # use gmail with port
        session.starttls()                              # enable security
        session.login(from_email, password)             # login with mail_id and password
        text = message.as_string()
        session.sendmail(from_email, to_email, text)
        session.quit()
    except Exception as e:
        print(f"Failed to send email. Error: {e}")