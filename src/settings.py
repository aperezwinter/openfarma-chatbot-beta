streamlit_style = """
        <style>
        div[data-testid="stChatMessage"] {
            background-color: white;
        }
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
        #MainMenu {visibility: hidden; height: 0%;}
        header {visibility: hidden; height: 0%;}
        footer {visibility: hidden; height: 0%;}

        /* Estilo específico para los mensajes del bot */
        .bot-message {
            background-color: #F0F0F5;
            border-style: solid;
            border-color: black;
            border-width: 2px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            margin-left: auto;  /* Alinea los mensajes del bot a la derecha */
        }

        /* Estilo específico para los mensajes del usuario */
        .user-message {
            background-color: #E6FFE6;
            border-style: solid;
            border-color: black;
            border-width: 2px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            margin-right: auto;  /* Alinea los mensajes del usuario a la izquierda */
        }

        .main .block-container {
            max-width: 60%;
            padding-top: 2rem;
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 2rem;
        }
        
        .chat-container {
            margin-top: 150px; /* Espacio para el header fijo */
        }
        
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            background-color: #F1F1F1;
            padding: 10px 0;
            box-shadow: 0 4px 2px -2px gray;
        }
        .header-content {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            width: 100%;
        }
        .header-image {
            width: 12.5%; /* Ajusta el ancho de la imagen */
            max-width: 100%;
        }
        .header-caption {
            width: 35%; /* Ajusta el ancho del caption */
            margin: 10px 0 0 0;
        }
        </style>
    """