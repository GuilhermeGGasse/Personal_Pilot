
"""Gerencia a conexão com a API do Trello."""

from trello import TrelloClient

from agenttaskmanager.config import (
    TRELLO_API_KEY,
    TRELLO_API_SECRET,
    TRELLO_TOKEN,
)


def get_trello_client() -> TrelloClient:
    """
    Cria e retorna um cliente autenticado do Trello.
    """
    return TrelloClient(
        api_key=TRELLO_API_KEY,
        api_secret=TRELLO_API_SECRET,
        token=TRELLO_TOKEN,
    )
