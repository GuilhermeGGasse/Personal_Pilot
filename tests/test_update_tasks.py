"""Testes unitários das ferramentas de gerenciamento de tarefas."""

from unittest.mock import MagicMock

from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.tools import tasks


def test_mudar_status_com_id_vazio(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.mudar_status_tarefa(
        card_id="   ",
        novo_status="em andamento",
    )

    assert resultado["sucesso"] is False
    assert "ID" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()

def test_mudar_status_com_status_vazio(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="   ",
    )

    assert resultado["sucesso"] is False
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()

def test_mudar_status_tarefa_com_falha_ao_mover_card(mocker):
    """Testa o tratamento de falha durante a movimentação do card."""

    card = mocker.Mock()
    card.id = "card-123"
    card.name = "Estudar Python"
    card.list_id = "list-todo"
    card.change_list.side_effect = ResourceUnavailable(
        "Erro ao mover card",
        mocker.Mock(status_code=503),
    )

    lista_origem = mocker.Mock()
    lista_origem.id = "list-todo"
    lista_origem.name = "A Fazer"
    lista_origem.list_cards.return_value = [card]

    lista_destino = mocker.Mock()
    lista_destino.id = "list-progress"
    lista_destino.name = "Em andamento"
    lista_destino.list_cards.return_value = []

    board = mocker.Mock()
    board.list_lists.return_value = [lista_origem, lista_destino]

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_list",
        return_value=lista_destino,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="Em andamento",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

    card.change_list.assert_called_once_with("list-progress")

def test_mudar_status_tarefa_com_id_numerico(mocker):
    """Testa a rejeição de um ID numérico."""

    resultado = tasks.mudar_status_tarefa(
        card_id=123,
        novo_status="Em andamento",
    )

    assert resultado["sucesso"] is False
    assert "id" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_mudar_status_tarefa_com_status_nulo(mocker):
    """Testa a rejeição de um status nulo."""

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status=None,
    )

    assert resultado["sucesso"] is False
    assert "status" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_mudar_status_tarefa_com_id_nulo(mocker):
    """Testa a rejeição de um ID nulo."""

    resultado = tasks.mudar_status_tarefa(
        card_id=None,
        novo_status="Em andamento",
    )

    assert resultado["sucesso"] is False
    assert "id" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_mudar_status_com_status_invalido(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="aguardando",
    )

    assert resultado["sucesso"] is False
    assert "Status inválido" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()

def test_mudar_status_tarefa_com_sucesso(mocker):
    board = MagicMock()

    lista_origem = MagicMock()
    lista_destino = MagicMock()

    lista_origem.name = "A Fazer"
    lista_origem.id = "list-001"

    lista_destino.name = "Em andamento"
    lista_destino.id = "list-002"

    card = MagicMock()
    card.id = "card-123"
    card.name = "Estudar Python"

    lista_origem.list_cards.return_value = [card]
    lista_destino.list_cards.return_value = []

    board.list_lists.return_value = [
        lista_origem,
        lista_destino,
    ]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    mocker.patch.object(
        tasks,
        "_get_list",
        return_value=lista_destino,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="em andamento",
    )

    card.change_list.assert_called_once_with("list-002")

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-123"
    assert resultado["dados"]["status_anterior"] == "A Fazer"
    assert resultado["dados"]["novo_status"] == "Em andamento"

def test_mudar_status_tarefa_ja_na_lista(mocker):
    board = MagicMock()

    lista = MagicMock()
    lista.name = "Em andamento"
    lista.id = "list-002"

    card = MagicMock()
    card.id = "card-123"
    card.name = "Estudar Python"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    mocker.patch.object(
        tasks,
        "_get_list",
        return_value=lista,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="em andamento",
    )

    card.change_list.assert_not_called()

    assert resultado["sucesso"] is True
    assert resultado["mensagem"] == "A tarefa já está nessa lista."
    assert resultado["dados"]["status"] == "Em andamento"

def test_mudar_status_tarefa_id_inexistente(mocker):
    board = MagicMock()

    lista = MagicMock()
    lista.name = "A Fazer"
    lista.id = "list-001"
    lista.list_cards.return_value = []

    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    mocker.patch.object(
        tasks,
        "_get_list",
        return_value=lista,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-inexistente",
        novo_status="a fazer",
    )

    assert resultado == {
    "sucesso": False,
    "mensagem": "Tarefa com ID 'card-inexistente' não encontrada.",
    "dados": None,
}

def test_mudar_status_com_nomes_iguais(mocker):
    board = MagicMock()

    lista_origem = MagicMock()
    lista_destino = MagicMock()

    lista_origem.name = "A Fazer"
    lista_origem.id = "list-001"

    lista_destino.name = "Concluído"
    lista_destino.id = "list-003"

    card_1 = MagicMock()
    card_1.id = "card-001"
    card_1.name = "Estudar Python"

    card_2 = MagicMock()
    card_2.id = "card-002"
    card_2.name = "Estudar Python"

    lista_origem.list_cards.return_value = [
        card_1,
        card_2,
    ]

    lista_destino.list_cards.return_value = []

    board.list_lists.return_value = [
        lista_origem,
        lista_destino,
    ]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    mocker.patch.object(
        tasks,
        "_get_list",
        return_value=lista_destino,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-002",
        novo_status="concluído",
    )

    card_1.change_list.assert_not_called()
    card_2.change_list.assert_called_once_with("list-003")

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-002"

def test_mudar_status_tarefa_com_status_numerico(mocker):
    """Testa a rejeição de um status numérico."""

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status=123,
    )

    assert resultado["sucesso"] is False
    assert "status" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_mudar_status_tarefa_com_token_invalido(mocker):
    """Testa o tratamento de token inválido durante a movimentação."""

    board = mocker.Mock()
    board.list_lists.side_effect = TokenError("Token inválido")

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="Em andamento",
    )

    assert resultado["sucesso"] is False
    assert "token" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()

def test_mudar_status_tarefa_sem_autorizacao(mocker):
    """Testa o tratamento de falta de autorização durante a movimentação."""

    board = mocker.Mock()
    board.list_lists.side_effect = Unauthorized(
        "Acesso não autorizado",
        mocker.Mock(status_code=401),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=board,
    )

    resultado = tasks.mudar_status_tarefa(
        card_id="card-123",
        novo_status="Em andamento",
    )

    assert resultado["sucesso"] is False
    assert "autorizado" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()
