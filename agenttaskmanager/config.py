"""Configura o carregamento e a validação das variáveis de ambiente."""

import os

from dotenv import load_dotenv

# Carrega as variáveis definidas no arquivo .env
load_dotenv()

def get_required_env(name: str) -> str:
    """
    Recupera uma variável de ambiente obrigatória.
    Gera um erro caso ela não esteja definida ou esteja vazia.
    """
    value = os.getenv(name)

    if not value:
        raise ValueError(
            f"Variável de ambiente obrigatória não configurada: {name}"
        )

    return value

# Google AI Studio / Gemini
GOOGLE_API_KEY = get_required_env("GOOGLE_API_KEY")

# Trello
TRELLO_API_KEY = get_required_env("TRELLO_API_KEY")
TRELLO_API_SECRET = get_required_env("TRELLO_API_SECRET")
TRELLO_TOKEN = get_required_env("TRELLO_TOKEN")

# Configuração do quadro
TRELLO_BOARD_NAME = get_required_env("TRELLO_BOARD_NAME")

TRELLO_LIST_TODO = get_required_env("TRELLO_LIST_TODO")
TRELLO_LIST_IN_PROGRESS = get_required_env("TRELLO_LIST_IN_PROGRESS")
TRELLO_LIST_DONE = get_required_env("TRELLO_LIST_DONE")
