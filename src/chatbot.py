import os, logging
import streamlit as st
from src.tools import customImage, encodeImage
from src.tools import streamMarkdown, formatLogMessage, cutString
from src.parameters import USER_AVATAR, BOT_AVATAR
from src.parameters import LOG_CHAT_PATH, LOG_CHAT2EMAIL_PATH
from src.parameters import USER_CHAT_COLUMNS, BOT_CHAT_COLUMNS

# Some logging general configuration
format_msg = '%(asctime)s - %(levelname)s - %(message)s'
format_time = "%Y-%m-%d %H:%M:%S"
level = logging.DEBUG

# Setup debug chat logging
logger_chat = logging.getLogger(name="chat")
logger_chat.propagate = False
logger_chat.setLevel(level)
formatter_chat = logging.Formatter(format_msg, format_time)
handler_chat = logging.FileHandler(os.getcwd() + LOG_CHAT_PATH)
handler_chat.setLevel(level)
handler_chat.setFormatter(formatter_chat)
logger_chat.addHandler(handler_chat)

# Setup dynamic chat to email logging
logger_chat2email = logging.getLogger(name="chat2email")
logger_chat2email.propagate = False
logger_chat2email.setLevel(level)
formatter_chat2email = logging.Formatter(format_msg, format_time)
handler_chat2email = logging.FileHandler(os.getcwd() + LOG_CHAT2EMAIL_PATH)
handler_chat2email.setLevel(level)
handler_chat2email.setFormatter(formatter_chat2email)
logger_chat2email.addHandler(handler_chat2email)

def setHeader(image_path: str, caption: str) -> None:
    """
    Configura el encabezado de la aplicación con una imagen y un pie de foto.

    Args:
        image_path (str): La ruta de la imagen que se utilizará en el encabezado.
        caption (str): El pie de foto que se mostrará debajo de la imagen.

    Returns:
        None
    """
    try:
        img_header = encodeImage(customImage(image_path))
        logger_chat.debug(f"Imagen del encabezado cargada desde {image_path}")
        
        # Insertar el encabezado con imagen y pie de foto
        st.markdown(f"""
            <div class="fixed-header">
                <div class="header-content">
                    <img src="data:image/jpeg;base64,{img_header}" class="header-image">
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""<div class="header-caption">{caption}</div>""", unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        logger_chat.info("Encabezado configurado correctamente.")
    except Exception as e:
        logger_chat.error(f"Error al configurar el encabezado: {e}")
        raise

def addMessage(role: str, content: str, start: bool=False) -> None:
    """
    Añade un mensaje a la conversación en `st.session_state`.

    Args:
        role (str): El rol del mensaje, debe ser 'user' o 'assistant'.
        content (str): El contenido del mensaje.
        start (bool): Si es True, indica el inicio de la conversación. Default es False.

    Returns:
        None

    Raises:
        AssertionError: Si el rol no es 'user' o 'assistant'.
    """
    try:
        assert role in ["user", "assistant"], "Role must be 'user' or 'assistant'"
        st.session_state.messages.append({"role": role, "content": content})

        # Logging para el inicio de la conversación
        if start:
            logger_chat.info(f"[id:{st.session_state.session_id}] ## Inicio de la conversación ##")

        # Logging del mensaje con formato
        logger_chat.info(f"[id:{st.session_state.session_id}] {role.upper()}: {cutString(content)}")
        logger_chat2email.info(f"[id:{st.session_state.session_id}] - {formatLogMessage(content)}")

    except AssertionError as e:
        logger_chat.error(f"[id:{st.session_state.session_id}] Error de rol: {e}")
        raise

def printMessage(role: str, content: str, stream: bool=False) -> None:
    """
    Muestra un mensaje en el chat con el formato adecuado según el rol.

    Args:
        role (str): El rol del mensaje, debe ser 'user' o 'assistant'.
        content (str): El contenido del mensaje a mostrar.
        stream (bool): Indica si el contenido debe ser mostrado en forma de stream. Default es False.

    Returns:
        None
    """
    logger_chat.debug(f"Mostrando mensaje del rol '{role}'")
    
    if role == "user":
        _, right = st.columns(USER_CHAT_COLUMNS)
        with right:
            with st.chat_message(role, avatar=USER_AVATAR):
                if stream:
                    logger_chat.debug(f"Mostrando mensaje del usuario en modo stream")
                    streamMarkdown(content, role)
                else:
                    st.markdown(
                        f'<div class="chat-message user-message">{content}</div>', 
                        unsafe_allow_html=True
                    )
                    logger_chat.debug(f"Mensaje del usuario mostrado correctamente.")
    else:
        left, _ = st.columns(BOT_CHAT_COLUMNS)
        with left:
            with st.chat_message(role, avatar=BOT_AVATAR):
                if stream:
                    logger_chat.debug(f"Mostrando mensaje del bot en modo stream")
                    streamMarkdown(content, role)
                else:
                    st.markdown(
                        f'<div class="chat-message bot-message">{content}</div>', 
                        unsafe_allow_html=True
                    )
                    logger_chat.debug(f"Mensaje del bot mostrado correctamente.")

    # Espacio en blanco para separar mensajes
    st.write("")

def printConversation() -> None:
    """
    Recorre y muestra la conversación completa almacenada en `st.session_state.messages`.

    Returns:
        None
    """
    logger_chat.info("Imprimiendo toda la conversación almacenada.")
    
    for message in st.session_state.messages:
        printMessage(message["role"], message["content"])
    num_messages = len(st.session_state.messages)
    logger_chat.info(f"Toda la conversación ha sido impresa correctamente con {num_messages} mensajes.")