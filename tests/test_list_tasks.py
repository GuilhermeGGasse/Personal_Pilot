"""Testes unitários das ferramentas de gerenciamento de tarefas."""

from unittest.mock import MagicMock

import pytest
from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.tools import tasks


def test_listar_tarefas_com_status_invalido(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.listar_tarefas(status="aguardando")

    assert resultado["sucesso"] is False
    assert "Status inválido" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()

def test_listar_todas_as_tarefas(mocker):
    board = MagicMock()

    lista_todo = MagicMock()
    lista_progress = MagicMock()
    lista_done = MagicMock()

    lista_todo.name = "A Fazer"
    lista_progress.name = "Em andamento"
    lista_done.name = "Concluído"

    card_1 = MagicMock()
    card_1.id = "card-001"
    card_1.name = "Estudar Python"
    card_1.desc = "Revisar funções"
    card_1.due = None

    card_2 = MagicMock()
    card_2.id = "card-002"
    card_2.name = "Desenvolver projeto"
    card_2.desc = "Implementar testes"
    card_2.due = None

    card_3 = MagicMock()
    card_3.id = "card-003"
    card_3.name = "Revisar código"
    card_3.desc = "Verificar qualidade"
    card_3.due = None

    lista_todo.list_cards.return_value = [card_1]
    lista_progress.list_cards.return_value = [card_2]
    lista_done.list_cards.return_value = [card_3]

    board.list_lists.return_value = [
        lista_todo,
        lista_progress,
        lista_done,
    ]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.listar_tarefas()

    assert resultado["sucesso"] is True
    assert resultado["dados"]["total"] == 3
    assert len(resultado["dados"]["tarefas"]) == 3

    assert resultado["dados"]["tarefas"][0]["nome"] == "Estudar Python"
    assert resultado["dados"]["tarefas"][0]["status"] == "A Fazer"

    assert resultado["dados"]["tarefas"][1]["nome"] == "Desenvolver projeto"
    assert resultado["dados"]["tarefas"][1]["status"] == "Em andamento"

    assert resultado["dados"]["tarefas"][2]["nome"] == "Revisar código"
    assert resultado["dados"]["tarefas"][2]["status"] == "Concluído"

@pytest.mark.parametrize(
    ("status", "nome_lista"),
    [
        ("a fazer", "A Fazer"),
        ("em andamento", "Em andamento"),
        ("concluído", "Concluído"),
    ],
)
def test_listar_tarefas_por_status(mocker, status, nome_lista):
    board = MagicMock()
    lista = MagicMock()

    lista.name = nome_lista

    card = MagicMock()
    card.id = "card-001"
    card.name = "Estudar Python"
    card.desc = "Revisar funções"
    card.due = None

    lista.list_cards.return_value = [card]

    mock_get_board = mocker.patch.object(
        tasks, "_get_board", return_value=board
    )

    mock_get_list = mocker.patch.object(
        tasks, "_get_list", return_value=lista
    )

    resultado = tasks.listar_tarefas(status=status)

    mock_get_board.assert_called_once()
    mock_get_list.assert_called_once_with(board, nome_lista)

    assert resultado["sucesso"] is True
    assert resultado["dados"]["total"] == 1
    assert resultado["dados"]["tarefas"][0]["nome"] == "Estudar Python"
    assert resultado["dados"]["tarefas"][0]["status"] == nome_lista

def test_listar_tarefas_com_status_numerico(mocker):
    """Testa a rejeição de um status numérico."""

    resultado = tasks.listar_tarefas(status=123)

    assert resultado["sucesso"] is False
    assert "status" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_listar_tarefas_com_status_vazio(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.listar_tarefas(status="   ")

    assert resultado["sucesso"] is False
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_listar_tarefas_sem_tarefas(mocker):
    board = MagicMock()
    lista = MagicMock()

    lista.list_cards.return_value = []
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.listar_tarefas()

    assert resultado == {
        "sucesso": True,
        "mensagem": "0 tarefa(s) encontrada(s).",
        "dados": {
            "total": 0,
            "tarefas": [],
        },
    }

def test_listar_tarefas_com_falha_ao_consultar_listas(mocker):
    """Testa o tratamento de falha ao consultar as listas do quadro."""

    board = mocker.Mock()
    board.list_lists.side_effect = ResourceUnavailable(
        "Erro ao consultar listas",
        mocker.Mock(status_code=503),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    resultado = tasks.listar_tarefas()

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()

def test_listar_tarefas_com_falha_ao_consultar_cards(mocker):
    """Testa o tratamento de falha ao consultar os cards de uma lista."""

    lista = mocker.Mock()
    lista.name = "A Fazer"
    lista.list_cards.side_effect = ResourceUnavailable(
        "Erro ao consultar cards",
        mocker.Mock(status_code=503),
    )

    board = mocker.Mock()
    board.list_lists.return_value = [lista]

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_list",
        return_value=lista,
    )

    resultado = tasks.listar_tarefas()

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

    lista.list_cards.assert_called_once()

def test_listar_tarefas_com_status_nulo(mocker):
    """Testa a rejeição de um status nulo."""

    resultado = tasks.listar_tarefas(status=None)

    assert resultado["sucesso"] is False
    assert "status" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_listar_tarefas_com_token_invalido(mocker):
    """Testa o tratamento de token inválido durante a consulta."""

    board = mocker.Mock()
    board.list_lists.side_effect = TokenError("Token inválido")

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    resultado = tasks.listar_tarefas()

    assert resultado["sucesso"] is False
    assert "token" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()

def test_listar_tarefas_sem_autorizacao(mocker):
    """Testa o tratamento de falta de autorização durante a consulta."""

    board = mocker.Mock()
    board.list_lists.side_effect = Unauthorized(
        "Acesso não autorizado",
        mocker.Mock(status_code=401),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    resultado = tasks.listar_tarefas()

    assert resultado["sucesso"] is False
    assert "autorizado" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()