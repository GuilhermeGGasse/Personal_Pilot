
"""Testes unitários das ferramentas de gerenciamento de tarefas."""

from unittest.mock import MagicMock

from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.tools import tasks


def test_editar_tarefa_com_id_vazio(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="   ",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "ID" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_id_numerico(mocker):
    resultado = tasks.editar_tarefa(
        card_id=123,
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "id" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_editar_tarefa_com_id_nulo(mocker):
    resultado = tasks.editar_tarefa(
        card_id=None,
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "id" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_editar_tarefa_sem_campos_para_atualizar(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
    )

    assert resultado["sucesso"] is False
    assert "campo" in resultado["mensagem"].lower()
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_nome_vazio(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="   ",
    )

    assert resultado["sucesso"] is False
    assert "nome" in resultado["mensagem"].lower()
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_nome_numerico(mocker):
    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa=123,
    )

    assert resultado["sucesso"] is False
    assert "nome" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_editar_tarefa_com_descricao_numerica(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        descricao_da_tarefa=123,
    )

    assert resultado["sucesso"] is False
    assert "descrição" in resultado["mensagem"].lower()
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_data_numerica(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento=20261105,
    )

    assert resultado["sucesso"] is False
    assert "data" in resultado["mensagem"].lower()
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_data_em_formato_invalido(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="05/11/2026",
    )

    assert resultado["sucesso"] is False
    assert "ISO 8601" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_data_inexistente(mocker):
    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="2026-02-30",
    )

    assert resultado["sucesso"] is False
    assert "ISO 8601" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_editar_tarefa_com_sucesso(mocker):
    board = MagicMock()

    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = "Revisar funções"
    card.due = None

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
        descricao_da_tarefa="Revisar orientação a objetos",
        data_vencimento="2026-11-05T18:00:00",
    )

    card.set_name.assert_called_once_with("Estudar Java")
    card.set_description.assert_called_once_with(
        "Revisar orientação a objetos"
    )
    card.set_due.assert_called_once()

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-123"


def test_editar_tarefa_apenas_nome(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.name = "Estudar Python"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
    )

    card.set_name.assert_called_once_with("Estudar Java")
    card.set_description.assert_not_called()
    card.set_due.assert_not_called()
    card.remove_due.assert_not_called()

    assert resultado["sucesso"] is True


def test_editar_tarefa_apenas_descricao(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        descricao_da_tarefa="Nova descrição",
    )

    card.set_name.assert_not_called()
    card.set_description.assert_called_once_with("Nova descrição")
    card.set_due.assert_not_called()

    assert resultado["sucesso"] is True


def test_editar_tarefa_apenas_data(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="2026-11-05",
    )

    card.set_name.assert_not_called()
    card.set_description.assert_not_called()
    card.set_due.assert_called_once()

    assert resultado["sucesso"] is True


def test_editar_tarefa_com_descricao_vazia(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        descricao_da_tarefa="",
    )

    card.set_description.assert_called_once_with("")

    assert resultado["sucesso"] is True


def test_editar_tarefa_removendo_data(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="",
    )

    card.remove_due.assert_called_once()
    card.set_due.assert_not_called()

    assert resultado["sucesso"] is True


def test_editar_tarefa_id_inexistente(mocker):
    board = MagicMock()
    lista = MagicMock()

    lista.list_cards.return_value = []
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-inexistente",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "não encontrada" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_token_invalido(mocker):
    board = MagicMock()
    board.list_lists.side_effect = TokenError("Token inválido")

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "token" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_editar_tarefa_sem_autorizacao(mocker):
    board = MagicMock()
    board.list_lists.side_effect = Unauthorized(
        "Acesso não autorizado",
        mocker.Mock(status_code=401),
    )

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "autorizado" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_editar_tarefa_com_falha_ao_consultar_cards(mocker):
    board = MagicMock()
    lista = MagicMock()

    lista.list_cards.side_effect = ResourceUnavailable(
        "Erro ao consultar cards",
        mocker.Mock(status_code=503),
    )

    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_falha_ao_atualizar_nome(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.set_name.side_effect = ResourceUnavailable(
        "Erro ao atualizar nome",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Estudar Java",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_falha_ao_atualizar_descricao(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.set_description.side_effect = ResourceUnavailable(
        "Erro ao atualizar descrição",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        descricao_da_tarefa="Nova descrição",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_falha_ao_atualizar_data(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.set_due.side_effect = ResourceUnavailable(
        "Erro ao atualizar vencimento",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="2026-11-05",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_falha_ao_remover_data(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.remove_due.side_effect = ResourceUnavailable(
        "Erro ao remover vencimento",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        data_vencimento="",
    )

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_editar_tarefa_com_atualizacao_parcial(mocker):
    board = MagicMock()
    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.set_description.side_effect = ResourceUnavailable(
        "Erro ao atualizar descrição",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.editar_tarefa(
        card_id="card-123",
        nome_da_tarefa="Novo nome",
        descricao_da_tarefa="Nova descrição",
    )

    card.set_name.assert_called_once_with("Novo nome")
    card.set_description.assert_called_once_with("Nova descrição")

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None
