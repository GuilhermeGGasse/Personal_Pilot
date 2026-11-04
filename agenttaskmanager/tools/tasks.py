
"""Ferramentas de gerenciamento de tarefas no Trello."""

import unicodedata
from datetime import datetime

from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.config import (
    TRELLO_BOARD_NAME,
    TRELLO_LIST_DONE,
    TRELLO_LIST_IN_PROGRESS,
    TRELLO_LIST_TODO,
)
from agenttaskmanager.tools.trello import get_trello_client


def _handle_trello_error(error: Exception) -> dict:
    """Converte exceções do Trello em respostas padronizadas."""

    if isinstance(error, ValueError):
        mensagem = str(error)

    elif isinstance(error, TokenError):
        mensagem = f"Problema com o token do Trello: {error}"

    elif isinstance(error, Unauthorized):
        mensagem = f"Acesso não autorizado ao Trello: {error}"

    elif isinstance(error, ResourceUnavailable):
        mensagem = f"Falha na comunicação com o Trello: {error}"

    else:
        raise error

    return {
        "sucesso": False,
        "mensagem": mensagem,
        "dados": None,
    }

def _normalize(value: str) -> str:
    """Normaliza textos para comparação, ignorando acentos e caixa."""
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    ).strip().casefold()


def _get_board():
    """Localiza o quadro configurado no Trello."""
    client = get_trello_client()
    boards = client.list_boards()

    matching_boards = [
        board for board in boards
        if _normalize(board.name) == _normalize(TRELLO_BOARD_NAME)
    ]

    if not matching_boards:
        raise ValueError(
            f"Quadro '{TRELLO_BOARD_NAME}' não encontrado."
        )

    if len(matching_boards) > 1:
        raise ValueError(
            f"Mais de um quadro encontrado com o nome '{TRELLO_BOARD_NAME}'."
        )

    return matching_boards[0]


def _get_list(board, list_name: str):
    """Localiza uma lista pelo nome dentro do quadro."""
    matching_lists = [
        trello_list for trello_list in board.list_lists()
        if _normalize(trello_list.name) == _normalize(list_name)
    ]

    if not matching_lists:
        raise ValueError(
            f"Lista '{list_name}' não encontrada no quadro."
        )

    if len(matching_lists) > 1:
        raise ValueError(
            f"Mais de uma lista encontrada com o nome '{list_name}'."
        )

    return matching_lists[0]

def adicionar_tarefa(
    nome_da_tarefa: str,
    descricao_da_tarefa: str = "",
    data_vencimento: str | None = None,
) -> dict:
    """
    Cria uma tarefa na lista A Fazer.

    A descrição e a data de vencimento são opcionais.
    A data deve ser fornecida em formato ISO 8601.
    """
    try:
        if not isinstance(nome_da_tarefa, str) or not nome_da_tarefa.strip():
            return {
                "sucesso": False,
                "mensagem": "O nome da tarefa não pode estar vazio.",
                "dados": None,
            }

        if descricao_da_tarefa is None:
            descricao_da_tarefa = ""

        if not isinstance(descricao_da_tarefa, str):
            return {
                "sucesso": False,
                "mensagem": "A descrição deve ser um texto válido.",
                "dados": None,
            }

        if data_vencimento is not None:
            if not isinstance(data_vencimento, str):
                return {
                    "sucesso": False,
                    "mensagem": "A data de vencimento deve ser um texto válido.",
                    "dados": None,
                }

            try:
                datetime.fromisoformat(data_vencimento)
            except ValueError:
                return {
                    "sucesso": False,
                    "mensagem": (
                        "A data de vencimento deve estar em formato ISO 8601 válido."
                    ),
                    "dados": None,
                }

        board = _get_board()
        lista = _get_list(board, TRELLO_LIST_TODO)

        card = lista.add_card(
            name=nome_da_tarefa.strip(),
            desc=descricao_da_tarefa.strip(),
            due=data_vencimento,
        )

        return {
            "sucesso": True,
            "mensagem": "Tarefa criada com sucesso.",
            "dados": {
                "id": card.id,
                "nome": card.name,
                "status": lista.name,
            },
        }

    except (ValueError, TokenError, Unauthorized, ResourceUnavailable) as error:
        return _handle_trello_error(error)

def listar_tarefas(status: str = "todas") -> dict:
    """
    Lista as tarefas do quadro, opcionalmente filtradas por status.

    Status aceitos: todas, a fazer, em andamento e concluído.
    """
    try:
        if not isinstance(status, str) or not status.strip():
            return {
                "sucesso": False,
                "mensagem": (
                    "Informe um status válido: todas, a fazer, "
                    "em andamento ou concluído."
                ),
                "dados": None,
            }

        status_map = {
            "a fazer": TRELLO_LIST_TODO,
            "em andamento": TRELLO_LIST_IN_PROGRESS,
            "concluido": TRELLO_LIST_DONE,
        }

        normalized_status = _normalize(status)

        if normalized_status != "todas" and normalized_status not in status_map:
            return {
                "sucesso": False,
                "mensagem": (
                    "Status inválido. Use: todas, a fazer, "
                    "em andamento ou concluído."
                ),
                "dados": None,
            }

        board = _get_board()

        if normalized_status == "todas":
            listas = board.list_lists()
        else:
            listas = [
                _get_list(board, status_map[normalized_status])
            ]

        tarefas = []

        for trello_list in listas:
            for card in trello_list.list_cards():
                tarefas.append({
                    "id": card.id,
                    "nome": card.name,
                    "descricao": card.desc,
                    "vencimento": card.due,
                    "status": trello_list.name,
                })

        return {
            "sucesso": True,
            "mensagem": f"{len(tarefas)} tarefa(s) encontrada(s).",
            "dados": {
                "total": len(tarefas),
                "tarefas": tarefas,
            },
        }

    except (ValueError, TokenError, Unauthorized, ResourceUnavailable) as error:
        return _handle_trello_error(error)

def mudar_status_tarefa(card_id: str, novo_status: str) -> dict:
    """
    Move uma tarefa para outra lista utilizando seu ID do Trello.
    """
    try:
        if not isinstance(card_id, str) or not card_id.strip():
            return {
                "sucesso": False,
                "mensagem": "O ID da tarefa não pode estar vazio.",
                "dados": None,
            }

        if not isinstance(novo_status, str) or not novo_status.strip():
            return {
                "sucesso": False,
                "mensagem": "Informe um status válido.",
                "dados": None,
            }

        status_map = {
            "a fazer": TRELLO_LIST_TODO,
            "em andamento": TRELLO_LIST_IN_PROGRESS,
            "concluido": TRELLO_LIST_DONE,
        }

        normalized_status = _normalize(novo_status)

        if normalized_status not in status_map:
            return {
                "sucesso": False,
                "mensagem": (
                    "Status inválido. Use: a fazer, "
                    "em andamento ou concluído."
                ),
                "dados": None,
            }

        board = _get_board()

        lista_destino = _get_list(
            board,
            status_map[normalized_status],
        )

        card_encontrado = None
        lista_origem = None

        for trello_list in board.list_lists():
            for card in trello_list.list_cards():
                if card.id == card_id.strip():
                    card_encontrado = card
                    lista_origem = trello_list
                    break

            if card_encontrado:
                break

        if not card_encontrado:
            return {
                "sucesso": False,
                "mensagem": f"Tarefa com ID '{card_id}' não encontrada.",
                "dados": None,
            }

        if lista_origem.id == lista_destino.id:
            return {
                "sucesso": True,
                "mensagem": "A tarefa já está nessa lista.",
                "dados": {
                    "id": card_id,
                    "nome": card_encontrado.name,
                    "status": lista_destino.name,
                },
            }

        card_encontrado.change_list(lista_destino.id)

        return {
            "sucesso": True,
            "mensagem": "Status da tarefa atualizado com sucesso.",
            "dados": {
                "id": card_id,
                "nome": card_encontrado.name,
                "status_anterior": lista_origem.name,
                "novo_status": lista_destino.name,
            },
        }

    except (ValueError, TokenError, Unauthorized, ResourceUnavailable) as error:
        return _handle_trello_error(error)


def editar_tarefa(
    card_id: str,
    nome_da_tarefa: str | None = None,
    descricao_da_tarefa: str | None = None,
    data_vencimento: str | None = None,
) -> dict:
    """
    Atualiza os campos de uma tarefa existente no Trello.

    Campos omitidos permanecem inalterados.
    Uma descrição vazia limpa a descrição.
    Uma data vazia remove o vencimento.
    A data deve seguir o formato ISO 8601.
    """
    try:
        # Validação do identificador
        if not isinstance(card_id, str) or not card_id.strip():
            return {
                "sucesso": False,
                "mensagem": "O ID da tarefa deve ser um texto válido.",
                "dados": None,
            }

        # Verifica se existe ao menos um campo para atualizar
        if (
            nome_da_tarefa is None
            and descricao_da_tarefa is None
            and data_vencimento is None
        ):
            return {
                "sucesso": False,
                "mensagem": "Informe ao menos um campo para atualizar.",
                "dados": None,
            }

        # Validação do nome
        if nome_da_tarefa is not None:
            if (
                not isinstance(nome_da_tarefa, str)
                or not nome_da_tarefa.strip()
            ):
                return {
                    "sucesso": False,
                    "mensagem": "O nome da tarefa não pode estar vazio.",
                    "dados": None,
                }

            nome_da_tarefa = nome_da_tarefa.strip()

        # Validação da descrição
        if descricao_da_tarefa is not None:
            if not isinstance(descricao_da_tarefa, str):
                return {
                    "sucesso": False,
                    "mensagem": "A descrição deve ser um texto válido.",
                    "dados": None,
                }

            descricao_da_tarefa = descricao_da_tarefa.strip()

        # Validação da data de vencimento
        data_vencimento_convertida = None
        remover_vencimento = False

        if data_vencimento is not None:
            if not isinstance(data_vencimento, str):
                return {
                    "sucesso": False,
                    "mensagem": (
                        "A data de vencimento deve ser um texto válido."
                    ),
                    "dados": None,
                }

            data_vencimento = data_vencimento.strip()

            if not data_vencimento:
                remover_vencimento = True
            else:
                try:
                    data_vencimento_convertida = datetime.fromisoformat(
                        data_vencimento
                    )
                except ValueError:
                    return {
                        "sucesso": False,
                        "mensagem": (
                            "A data de vencimento deve estar "
                            "em formato ISO 8601 válido."
                        ),
                        "dados": None,
                    }

        # Localiza o quadro e a tarefa
        board = _get_board()
        card_encontrado = None

        for lista in board.list_lists():
            for card in lista.list_cards():
                if card.id == card_id.strip():
                    card_encontrado = card
                    break

            if card_encontrado is not None:
                break

        if card_encontrado is None:
            raise ValueError("Tarefa não encontrada no quadro configurado.")

        # Atualiza somente os campos informados
        if nome_da_tarefa is not None:
            card_encontrado.set_name(nome_da_tarefa)

        if descricao_da_tarefa is not None:
            card_encontrado.set_description(descricao_da_tarefa)

        if remover_vencimento:
            card_encontrado.remove_due()

        elif data_vencimento_convertida is not None:
            card_encontrado.set_due(data_vencimento_convertida)

        return {
            "sucesso": True,
            "mensagem": "Tarefa atualizada com sucesso.",
            "dados": {
                "id": card_encontrado.id,
                "nome": card_encontrado.name,
                "descricao": card_encontrado.desc,
                "data_vencimento": card_encontrado.due,
            },
        }

    except (ValueError, TokenError, Unauthorized, ResourceUnavailable) as error:
        return _handle_trello_error(error)

def remover_tarefa(card_id: str) -> dict:
    """
    Remove permanentemente uma tarefa existente do Trello.

    A tarefa é identificada pelo ID do card.
    """
    try:
        # Validação do identificador
        if not isinstance(card_id, str) or not card_id.strip():
            return {
                "sucesso": False,
                "mensagem": "O ID da tarefa deve ser um texto válido.",
                "dados": None,
            }

        # Localiza o quadro configurado
        board = _get_board()

        # Procura a tarefa em todas as listas do quadro
        card_encontrado = None

        for lista in board.list_lists():
            for card in lista.list_cards():
                if card.id == card_id.strip():
                    card_encontrado = card
                    break

            if card_encontrado is not None:
                break

        # Verifica se a tarefa existe
        if card_encontrado is None:
            raise ValueError("Tarefa não encontrada no quadro configurado.")

        # Armazena os dados antes da exclusão
        dados_tarefa = {
            "id": card_encontrado.id,
            "nome": card_encontrado.name,
            "descricao": card_encontrado.desc,
            "data_vencimento": card_encontrado.due,
        }

        # Remove o card do Trello
        card_encontrado.delete()

        return {
            "sucesso": True,
            "mensagem": "Tarefa removida com sucesso.",
            "dados": dados_tarefa,
        }

    except (
        ValueError,
        TokenError,
        Unauthorized,
        ResourceUnavailable,
    ) as error:
        return _handle_trello_error(error)

def get_temporal_context() -> str:
    """
    Retorna a data e hora atuais para contextualização do agente.
    """
    now = datetime.now().astimezone()

    return now.strftime(
        "Data atual: %d/%m/%Y. Horário atual: %H:%M:%S. "
        "Fuso horário: %Z."
    )
