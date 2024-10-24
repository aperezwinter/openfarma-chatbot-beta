streamlit_style = """
        <style>
        div[data-testid="stChatMessage"] {
            background-color: white;
            margin-bottom: -25px; /* Ajusta este valor para más o menos espacio */
        }
        div[data-testid="stToolbar"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stDecoration"] {visibility: hidden; height: 0%; position: fixed;}
        div[data-testid="stStatusWidget"] {visibility: hidden; height: 0%; position: fixed;}
        #MainMenu {visibility: hidden; height: 0%;}
        header {visibility: hidden; height: 0%;}
        footer {visibility: hidden; height: 0%;}
        
        /* Estilo específico para los mensajes del bot */
        .bot-message {
            background-color: #FFFFFF;
            border-style: dotted;
            border-color: #8EA749;
            border-width: 3px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            font-size: 20px;  /* Ajusta el tamaño de la fuente */
            margin-left: auto;  /* Alinea los mensajes del bot a la derecha */
            position: relative;
            top: -13.5px;  /* Ajusta la posición vertical de los mensajes del usuario */
        }

        /* Estilo específico para los mensajes del usuario */
        .user-message {
            background-color: #FFFFFF;
            border-style: dotted;
            border-color: #8EA749;
            border-width: 3px;
            border-radius: 10px;
            padding: 15px;
            color: black;
            font-size: 20px;
            margin-right: auto;  /* Alinea los mensajes del usuario a la izquierda */
            position: relative;
            top: -13.5px;  /* Ajusta la posición vertical de los mensajes del usuario */
        }

        .main .block-container {
            width: 100% !important;
            max-width: 80% !important;
            padding-top: 2rem;
            padding-right: 1rem;
            padding-left: 1rem;
            padding-bottom: 2rem;
        }
        
        .chat-container {
            margin-top: 40px; /* Espacio para el header fijo */
        }
        
        .fixed-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 1000;
            background-color: #FFFFFF;
            padding: 10px 0;
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
            display: flex;
            justify-content: center;
            text-align: center;
            width: 70%;
            margin: 60px auto 0 auto;
            font-size: 24px;
        }
        div[data-testid="stChatInput"] textarea {
            font-size: 20px;  /* Ajusta el tamaño de la fuente aquí */
        }
        </style>
    """

reinforces_style = """
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
    """