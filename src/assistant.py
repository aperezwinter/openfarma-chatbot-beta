import io, re, time, logging
import base64, smtplib
import streamlit as st
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from streamlit.runtime.scriptrunner import get_script_run_ctx
from langchain_core.output_parsers import StrOutputParser
from langchain_openai.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.parameters import *

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
    return chain.invoke({"context": context, "question": question})
    #return chain.stream({"context": context, "question": question})

def init_logging(log_file: str):
    logger = logging.getLogger(__name__)
    if logger.handlers:  # logger is already setup, don't setup again
        return logger
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    format_msg = '%(asctime)s - %(message)s'
    format_time = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(format_msg, format_time)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def stream_markdown(full_text, role, delay=0.0075, chunk_size=1):
    container = st.empty()
    current_text = ""
    for i in range(0, len(full_text), chunk_size):
        current_text += full_text[i:i+chunk_size]
        if role == "assistant":
            container.markdown(f'<div class="chat-message bot-message">{current_text}</div>', unsafe_allow_html=True)
        else:
            container.markdown(f'<div class="chat-message user-message">{current_text}</div>', unsafe_allow_html=True)
        time.sleep(delay)

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

def custom_image(image_path, resize_factor: float=1.0):
    img = Image.open(image_path)
    width = int(img.size[0] * resize_factor)
    height = int(img.size[1] * resize_factor)
    img = img.resize((width, height))
    return img

# Function to encode the gif from base64
def encode_gif(gif_path: str):
    with open(gif_path, "rb") as f:
        contents = f.read()
        gif = base64.b64encode(contents).decode("utf-8")
        f.close()
    return gif

# Function to encode the image to base64
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to ensure bold and italic text is correctly processed in markdown
def modify_text(text):
    def process_match(match):
        original_text = match.group(0)
        if original_text.startswith('**'):
            symbol = '**'
            content = original_text[2:-2]
        else:
            symbol = '*'
            content = original_text[1:-1]
        parts = content.split(' ')
        modified_content = ' '.join([f'{symbol}{part}{symbol}' for part in parts])
        return modified_content

    modified_text = re.sub(r'(\*\*.*?\*\*|\*.*?\*)', process_match, text)
    return modified_text

# Function to remove bold and italic text
def remove_bold_italic(text):
    def process_match(match):
        original_text = match.group(0)
        if original_text.startswith('**'):
            content = original_text[2:-2]  # Remueve los símbolos de negrita
        else:
            content = original_text[1:-1]  # Remueve los símbolos de cursiva
        parts = content.split(' ')  # Separa las palabras
        modified_content = ' '.join(parts)  # Une las palabras de nuevo
        return modified_content

    lines = text.splitlines()
    modified_lines = [re.sub(r'(\*\*.*?\*\*|\*.*?\*)', process_match, line) for line in lines]
    modified_text = '\n'.join(modified_lines)
    
    return modified_text