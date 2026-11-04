from unittest.mock import MagicMock

from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.tools import tasks


def test_adicionar_tarefa_com_sucesso(mocker):
    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.name = "Estudar Python"

    board.list_lists.return_value = [lista]
    lista.name = "A Fazer"
    lista.add_card.return_value = card

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções e classes.",
    )

    lista.add_card.assert_called_once_with(
        name="Estudar Python",
        desc="Revisar funções e classes.",
        due=None,
    )

    assert resultado == {
    "sucesso": True,
    "mensagem": "Tarefa criada com sucesso.",
    "dados": {
        "id": "card-123",
        "nome": "Estudar Python",
        "status": "A Fazer",
    },
}

def test_adicionar_tarefa_com_nome_vazio():
    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="   ",
        descricao_da_tarefa="Descrição de teste.",
    )

    assert resultado == {
    "sucesso": False,
    "mensagem": "O nome da tarefa não pode estar vazio.",
    "dados": None,
}

def test_adicionar_tarefa_com_nome_numerico(mocker):
    """Testa a rejeição de um nome de tarefa numérico."""

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa=123,
        descricao_da_tarefa="Revisar funções",
    )

    assert resultado["sucesso"] is False
    assert "nome" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_adicionar_tarefa_com_token_invalido(mocker):
    mocker.patch.object(
        tasks,
        "_get_board",
        side_effect=TokenError("Token inválido"),
    )

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções.",
    )

    assert resultado == {
    "sucesso": False,
    "mensagem": "Problema com o token do Trello: Token inválido",
    "dados": None,
}

def test_adicionar_tarefa_sem_autorizacao(mocker):
    erro = Unauthorized("Acesso negado", MagicMock(status_code=401))

    mocker.patch.object(
        tasks,
        "_get_board",
        side_effect=erro,
    )

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções.",
    )

    assert resultado["sucesso"] is False
    assert "Acesso não autorizado" in resultado["mensagem"]
    assert resultado["dados"] is None

def test_adicionar_tarefa_com_falha_de_requisicao(mocker):
    erro = ResourceUnavailable(
        "Falha na requisição",
        MagicMock(status_code=500),
    )

    mocker.patch.object(
        tasks,
        "_get_board",
        side_effect=erro,
    )

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções.",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

def test_adicionar_tarefa_com_descricao_opcional(mocker):
    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    lista.name = "A Fazer"
    lista.add_card.return_value = card
    card.id = "card-123"
    card.name = "Estudar Python"

    mocker.patch.object(tasks, "_get_board", return_value=board)
    mocker.patch.object(tasks, "_get_list", return_value=lista)

    resultado = tasks.adicionar_tarefa("Estudar Python")

    lista.add_card.assert_called_once_with(
        name="Estudar Python",
        desc="",
        due=None,
    )

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-123"


def test_adicionar_tarefa_com_descricao_invalida(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa=123,
    )

    assert resultado["sucesso"] is False
    assert "descrição" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_adicionar_tarefa_com_data_invalida(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções",
        data_vencimento=123,
    )

    assert resultado["sucesso"] is False
    assert "data de vencimento" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()

def test_adicionar_tarefa_com_falha_ao_criar_card(mocker):
    """Testa o tratamento de falha do Trello durante a criação do card."""

    lista = mocker.Mock()
    lista.add_card.side_effect = ResourceUnavailable(
        "Erro ao criar card",
        mocker.Mock(status_code=503),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=mocker.Mock(),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_list",
        return_value=lista,
    )

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

    lista.add_card.assert_called_once()

def test_adicionar_tarefa_com_data_em_formato_invalido(mocker):
    """Testa a rejeição de uma data em formato inválido."""

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções",
        data_vencimento="31/10/2026",
    )

    assert resultado["sucesso"] is False
    assert "data" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_adicionar_tarefa_com_data_inexistente(mocker):
    """Testa a rejeição de uma data inexistente no calendário."""

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções",
        data_vencimento="2026-02-30",
    )

    assert resultado["sucesso"] is False
    assert "data" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

def test_adicionar_tarefa_sem_data_de_vencimento(mocker):
    """Testa a criação de uma tarefa sem data de vencimento."""

    lista = mocker.Mock()
    card = mocker.Mock()
    card.id = "card-123"
    card.name = "Estudar Python"
    lista.name = "A Fazer"
    lista.add_card.return_value = card

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_board",
        return_value=mocker.Mock(),
    )

    mocker.patch(
        "agenttaskmanager.tools.tasks._get_list",
        return_value=lista,
    )

    resultado = tasks.adicionar_tarefa(
        nome_da_tarefa="Estudar Python",
        descricao_da_tarefa="Revisar funções",
    )

    assert resultado["sucesso"] is True
    assert resultado["dados"]["nome"] == "Estudar Python"
    assert resultado["dados"]["status"] == "A Fazer"

    lista.add_card.assert_called_once_with(
        name="Estudar Python",
        desc="Revisar funções",
        due=None,
    )