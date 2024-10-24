import io, os, re, time
import datetime, base64
import smtplib, textwrap, logging
import streamlit as st
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from src.parameters import LOG_EMAIL_PATH, TIMEOUT
from src.parameters import FROM_EMAIL, TO_EMAIL, PASSWORD

# Setup email logging configuration
level = logging.DEBUG
format_time = "%Y-%m-%d %H:%M:%S"
format_msg = '%(asctime)s - %(levelname)s - %(message)s'
logger_email = logging.getLogger(name="email")
logger_email.propagate = False
logger_email.setLevel(level)
formatter = logging.Formatter(format_msg, format_time)
handler = logging.FileHandler(os.getcwd() + LOG_EMAIL_PATH)
handler.setLevel(level)
handler.setFormatter(formatter)
logger_email.addHandler(handler)

def checkForEmail2Send(file_path: str, subject: str="Chat Q&A: "):
    if time.time() - st.session_state.last_active >= TIMEOUT:
        st.session_state.last_active = time.time()
        if st.session_state.send_email:
            # Send email with the chat log
            with open(file_path, "r") as file:
                lines = file.readlines()
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                subject += today
                body = ''.join(lines)
                sendEmail(FROM_EMAIL, TO_EMAIL, PASSWORD, subject, body)
            file.close()
            # Clear the chat log
            with open(file_path, "w") as file:
                file.write("")
            file.close()
            # Reset the email sending flag
            st.session_state.send_email = False

def customImage(image_path: str, resize_factor: float=1.0):
    img = Image.open(image_path)
    width = int(img.size[0] * resize_factor)
    height = int(img.size[1] * resize_factor)
    img = img.resize((width, height))
    return img

def cutString(string: str, max_length: int=1000) -> str:
    """
    Recorta un string a una longitud máxima, agregando puntos suspensivos si el string es más largo.

    :param string: El texto a recortar.
    :param max_length: La longitud máxima del texto.
    :return: El texto recortado.
    """
    string = re.sub(r'\n+', '\n', string) # remove extra newlines
    string = string.replace('\n', ' ') # replace newlines with spaces
    string = re.sub(r' +', ' ', string) # remove extra spaces
    if len(string) > max_length:
        return string[:max_length] + "..."
    return string

# Function to encode the image to base64
def encodeImage(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def extractData(args, database):
    str_args = str(args)
    retrived_from_vdb = database.similarity_search_with_score(str_args, k=5)
    context = '\n'.join([retrived_from_vdb[i][0].page_content for i in range(5)])
    output = re.sub(' +', ' ', f"Contexto: {context}\nExtra: Responder sin precios \
                    ni keywords, realizar comparación entre productos si hay más de uno.")
    return output

def formatLogMessage(log_message: str, max_line_length: int=150, header_length: int = 50) -> str:
    """
    Formatea un string para que tenga una longitud de línea limitada entre los saltos de línea existentes.
    El primer renglón será más corto debido al encabezado del logging.

    :param log_message: El mensaje de log que se quiere formatear.
    :param max_line_length: La cantidad máxima de caracteres por renglón.
    :param header_length: La longitud del encabezado del log (primer renglón más corto).
    :return: El mensaje formateado.
    """
    log_message = re.sub(r'\n+', '\n', log_message) # remove extra newlines
    lines = log_message.splitlines() # split the message into lines
    first_width = max_line_length - header_length
    formatted_message = textwrap.fill(lines[0], width=first_width) # format the first line
    for line in lines[1:]: # format the rest of the lines 
        formatted_message += "\n" + textwrap.fill(line, width=max_line_length)

    return formatted_message

def getBase64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def removeBoldItalic(text: str) -> str:
    """
    Remueve los símbolos de negrita ('**') y cursiva ('*') de un texto dado.

    Args:
        text (str): El texto que contiene formato de negrita y cursiva.

    Returns:
        str: El texto sin los símbolos de negrita y cursiva.
    """
    logging.info("Iniciando el proceso de eliminación de formato de negrita e itálica.")

    def processMatch(match) -> str:
        """
        Procesa cada coincidencia para remover los símbolos de formato de negrita o cursiva.

        Args:
            match: Coincidencia de texto con símbolos de negrita ('**') o cursiva ('*').

        Returns:
            str: El texto sin los símbolos de negrita o cursiva.
        """
        original_text = match.group(0)
        logging.debug(f"Procesando el texto: {original_text}")
        
        if original_text.startswith('**'):
            content = original_text[2:-2]  # Remueve los símbolos de negrita
            logging.debug("Símbolos de negrita eliminados.")
        else:
            content = original_text[1:-1]  # Remueve los símbolos de cursiva
            logging.debug("Símbolos de cursiva eliminados.")
        
        # Separa las palabras y las une de nuevo, manteniendo el contenido intacto
        parts = content.split(' ')
        modified_content = ' '.join(parts)
        return modified_content

    try:
        lines = text.splitlines()
        modified_lines = [re.sub(r'(\*\*.*?\*\*|\*.*?\*)', processMatch, line) for line in lines]
        modified_text = '\n'.join(modified_lines)
        logging.info("El proceso de eliminación de formato se completó con éxito.")
        return modified_text
    
    except Exception as e:
        logging.error(f"Ocurrió un error durante el procesamiento del texto: {e}")
        raise

def retrieveLastMessage(client, thread_id):
    """
    Recupera el último mensaje de un hilo específico y procesa su contenido para
    eliminar anotaciones, y luego remueve los textos en negrita e itálica.

    Args:
        client: El cliente de la API utilizado para obtener los mensajes.
        thread_id: El ID del hilo del cual se recupera el último mensaje.

    Returns:
        str: El contenido del último mensaje con las anotaciones eliminadas y
        sin formato de negrita o itálica.

    Raises:
        Exception: Si hay algún error al recuperar los mensajes o procesar el contenido.
    """
    logging.info(f"Recuperando el último mensaje del hilo con ID: {thread_id}")
    
    try:
        # Listar los mensajes en el hilo
        messages = list(client.beta.threads.messages.list(thread_id=thread_id))
        if not messages:
            logging.warning(f"No se encontraron mensajes en el hilo con ID: {thread_id}")
            return ""
        message_content = messages[0].content[0].text
        logging.debug(f"Mensaje recuperado: {message_content}")

        # Procesar anotaciones en el contenido del mensaje
        annotations = message_content.annotations
        if annotations:
            logging.debug(f"Procesando {len(annotations)} anotaciones en el mensaje.")
            for annotation in annotations:
                message_content.value = message_content.value.replace(annotation.text, "")
                logging.debug(f"Anotación '{annotation.text}' eliminada del mensaje.")
        else:
            logging.debug("No se encontraron anotaciones en el mensaje.")

        # Remover negrita e itálica del mensaje
        processed_message = removeBoldItalic(message_content.value)
        logging.info("El procesamiento del mensaje se completó exitosamente.")
        return processed_message

    except Exception as e:
        logging.error(f"Error al recuperar el mensaje del hilo {thread_id}. Detalles: {e}")
        raise

def streamMarkdown(full_text: str, role: str, delay: float=0.0075, chunk_size: int=1):
    """
    Simula un efecto de escritura en tiempo real para mensajes de chat, mostrando texto de forma progresiva.

    Args:
        full_text (str): El texto completo que se va a mostrar en el chat.
        role (str): El rol del emisor del mensaje ('user' o 'assistant') para aplicar estilos específicos.
        delay (float, opcional): Tiempo de espera (seg) entre la aparición de cada fragmento de texto. Por defecto es 0.0075 segundos.
        chunk_size (int, opcional): Tamaño de cada fragmento de texto que se añade en cada iteración. Por defecto es 1 carácter.
    
    Returns:
        None
    """
    container = st.empty()  # Contenedor para mostrar el mensaje de manera progresiva
    current_text = ""       # Texto acumulado que se irá mostrando
    
    logging.info(f"Streaming markdown for role: {role}, with delay {delay} and chunk size {chunk_size}.")
    
    # Iterar sobre el texto, añadiendo fragmentos progresivamente
    for i in range(0, len(full_text), chunk_size):
        current_text += full_text[i:i+chunk_size]
        
        # Estilo condicional según el rol del emisor
        if role == "assistant":
            container.markdown(
                f'<div class="chat-message bot-message bot-message ul">{current_text}</div>', 
                unsafe_allow_html=True
            )
        else:
            container.markdown(
                f'<div class="chat-message user-message">{current_text}</div>', 
                unsafe_allow_html=True
            )
        
        # Simular el retraso entre la escritura de fragmentos de texto
        time.sleep(delay)

def sendEmail(from_email: str, to_email: str, password: str, subject: str, body: str) -> None:
    """
    Envía un correo electrónico desde una cuenta de Gmail a un destinatario.

    Args:
        from_email (str): Dirección de correo electrónico del remitente.
        to_email (str): Dirección de correo electrónico del destinatario.
        password (str): Contraseña de la cuenta del remitente.
        subject (str): Asunto del correo electrónico.
        body (str): Cuerpo del correo electrónico.

    Returns:
        None

    Raises:
        Exception: Si ocurre un error al enviar el correo electrónico.
    """
    try:
        logger_email.info(f"Preparando para enviar un correo a {to_email} desde {from_email} con el asunto '{subject}'.")

        # Configuración del mensaje MIME
        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        # Inicio de la sesión SMTP
        logger_email.debug("Iniciando sesión SMTP con Gmail...")
        session = smtplib.SMTP('smtp.gmail.com', 587)   # Usar servidor Gmail con puerto 587
        session.starttls()                              # Activar el modo seguro TLS
        session.login(from_email, password)             # Autenticación

        # Convertir el mensaje a formato string y enviar
        text = message.as_string()
        session.sendmail(from_email, to_email, text)
        session.quit()  # Terminar la sesión SMTP

        logger_email.info(f"Correo enviado exitosamente a {to_email}.")
    
    except smtplib.SMTPAuthenticationError:
        logger_email.error("Error de autenticación. Verifique la dirección de correo y la contraseña.")
        raise
    except smtplib.SMTPConnectError:
        logger_email.error("No se pudo conectar al servidor SMTP. Revise la conexión a internet.")
        raise
    except Exception as e:
        logger_email.error(f"Error al enviar el correo: {e}")
        raise



