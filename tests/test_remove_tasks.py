"""Testes unitários da ferramenta de remoção de tarefas."""

from unittest.mock import MagicMock

from trello.exceptions import (
    ResourceUnavailable,
    TokenError,
    Unauthorized,
)

from agenttaskmanager.tools import tasks


def test_remover_tarefa_com_sucesso(mocker):
    """Testa a remoção bem-sucedida de uma tarefa."""

    board = MagicMock()

    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = "Revisar fundamentos"
    card.due = "2026-11-03"

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    card.delete.assert_called_once_with()

    assert resultado["sucesso"] is True
    assert resultado["mensagem"] == "Tarefa removida com sucesso."
    assert resultado["dados"]["id"] == "card-123"
    assert resultado["dados"]["nome"] == "Estudar Python"
    assert resultado["dados"]["descricao"] == "Revisar fundamentos"
    assert resultado["dados"]["data_vencimento"] == "2026-11-03"


def test_remover_tarefa_com_id_vazio(mocker):
    """Testa a rejeição de um ID vazio."""

    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.remover_tarefa(card_id="   ")

    assert resultado["sucesso"] is False
    assert "ID" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_remover_tarefa_com_id_numerico(mocker):
    """Testa a rejeição de um ID numérico."""

    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.remover_tarefa(card_id=123)

    assert resultado["sucesso"] is False
    assert "ID" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_remover_tarefa_com_id_nulo(mocker):
    """Testa a rejeição de um ID nulo."""

    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.remover_tarefa(card_id=None)

    assert resultado["sucesso"] is False
    assert "ID" in resultado["mensagem"]
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_remover_tarefa_id_inexistente(mocker):
    """Testa a tentativa de remover uma tarefa inexistente."""

    board = MagicMock()

    lista = MagicMock()
    lista.list_cards.return_value = []

    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-inexistente")

    assert resultado["sucesso"] is False
    assert "Tarefa não encontrada" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_remover_tarefa_sem_listas(mocker):
    """Testa a tentativa de remoção em um quadro sem listas."""

    board = MagicMock()
    board.list_lists.return_value = []

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "Tarefa não encontrada" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_remover_tarefa_em_lista_posterior(mocker):
    """Testa a localização do card em uma lista posterior."""

    board = MagicMock()

    lista_1 = MagicMock()
    lista_2 = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = ""
    card.due = None

    lista_1.list_cards.return_value = []
    lista_2.list_cards.return_value = [card]

    board.list_lists.return_value = [lista_1, lista_2]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    card.delete.assert_called_once_with()
    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-123"


def test_remover_tarefa_com_nomes_iguais(mocker):
    """Testa a remoção pelo ID quando existem nomes iguais."""

    board = MagicMock()

    lista = MagicMock()

    card_1 = MagicMock()
    card_1.id = "card-001"
    card_1.name = "Estudar Python"

    card_2 = MagicMock()
    card_2.id = "card-002"
    card_2.name = "Estudar Python"
    card_2.desc = "Segunda tarefa"
    card_2.due = None

    lista.list_cards.return_value = [card_1, card_2]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-002")

    card_1.delete.assert_not_called()
    card_2.delete.assert_called_once_with()

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-002"


def test_remover_tarefa_com_falha_ao_excluir(mocker):
    """Testa o tratamento de falha durante a exclusão."""

    board = MagicMock()

    lista = MagicMock()

    card = MagicMock()
    card.id = "card-123"
    card.delete.side_effect = ResourceUnavailable(
        "Erro ao excluir card",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None

    card.delete.assert_called_once_with()


def test_remover_tarefa_com_token_invalido(mocker):
    """Testa o tratamento de token inválido."""

    board = mocker.Mock()
    board.list_lists.side_effect = TokenError("Token inválido")

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "token" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()


def test_remover_tarefa_sem_autorizacao(mocker):
    """Testa o tratamento de falta de autorização."""

    board = mocker.Mock()
    board.list_lists.side_effect = Unauthorized(
        "Acesso não autorizado",
        mocker.Mock(status_code=401),
    )

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "autorizado" in resultado["mensagem"].lower()
    assert resultado["dados"] is None

    board.list_lists.assert_called_once()


def test_remover_tarefa_com_falha_ao_consultar_listas(mocker):
    """Testa falha ao consultar as listas do quadro."""

    board = mocker.Mock()
    board.list_lists.side_effect = ResourceUnavailable(
        "Erro ao consultar listas",
        mocker.Mock(status_code=503),
    )

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_remover_tarefa_com_falha_ao_consultar_cards(mocker):
    """Testa falha ao consultar os cards de uma lista."""

    board = MagicMock()

    lista = mocker.Mock()
    lista.list_cards.side_effect = ResourceUnavailable(
        "Erro ao consultar cards",
        mocker.Mock(status_code=503),
    )

    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_remover_tarefa_com_falha_ao_excluir_por_token(mocker):
    """Testa token inválido durante a exclusão."""

    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.delete.side_effect = TokenError("Token inválido")

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "token" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_remover_tarefa_com_falha_ao_excluir_sem_autorizacao(mocker):
    """Testa falta de autorização durante a exclusão."""

    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.delete.side_effect = Unauthorized(
        "Acesso não autorizado",
        mocker.Mock(status_code=401),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "autorizado" in resultado["mensagem"].lower()
    assert resultado["dados"] is None


def test_remover_tarefa_nao_exclui_card_diferente(mocker):
    """Testa que somente o card identificado é excluído."""

    board = MagicMock()
    lista = MagicMock()

    card_1 = MagicMock()
    card_1.id = "card-001"

    card_2 = MagicMock()
    card_2.id = "card-002"
    card_2.name = "Tarefa correta"
    card_2.desc = ""
    card_2.due = None

    lista.list_cards.return_value = [card_1, card_2]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-002")

    card_1.delete.assert_not_called()
    card_2.delete.assert_called_once_with()

    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-002"


def test_remover_tarefa_preserva_dados_antes_da_exclusao(mocker):
    """Testa que os dados retornados são capturados antes da exclusão."""

    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = "Revisar fundamentos"
    card.due = "2026-11-03"

    def excluir_card():
        card.name = "Card removido"
        card.desc = ""
        card.due = None

    card.delete.side_effect = excluir_card

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is True
    assert resultado["dados"]["nome"] == "Estudar Python"
    assert resultado["dados"]["descricao"] == "Revisar fundamentos"
    assert resultado["dados"]["data_vencimento"] == "2026-11-03"


def test_remover_tarefa_com_id_com_espacos(mocker):
    """Testa a normalização de espaços ao redor do ID."""

    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = ""
    card.due = None

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id=" card-123 ")

    card.delete.assert_called_once_with()
    assert resultado["sucesso"] is True
    assert resultado["dados"]["id"] == "card-123"


def test_remover_tarefa_nao_exclui_quando_id_invalido(mocker):
    """Testa que um ID inválido não provoca exclusão."""

    mock_get_board = mocker.patch.object(tasks, "_get_board")

    resultado = tasks.remover_tarefa(card_id="")

    assert resultado["sucesso"] is False
    assert resultado["dados"] is None
    mock_get_board.assert_not_called()


def test_remover_tarefa_com_falha_ao_obter_quadro(mocker):
    """Testa o tratamento de erro ao localizar o quadro."""

    mocker.patch.object(
        tasks,
        "_get_board",
        side_effect=ResourceUnavailable(
            "Erro ao localizar quadro",
            mocker.Mock(status_code=503),
        ),
    )

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert "Falha na comunicação" in resultado["mensagem"]
    assert resultado["dados"] is None


def test_remover_tarefa_com_falha_ao_excluir_card(mocker):
    """Testa que a resposta de erro não confirma uma exclusão."""

    board = MagicMock()
    lista = MagicMock()
    card = MagicMock()

    card.id = "card-123"
    card.name = "Estudar Python"
    card.desc = ""
    card.due = None

    card.delete.side_effect = ResourceUnavailable(
        "Erro ao excluir card",
        mocker.Mock(status_code=503),
    )

    lista.list_cards.return_value = [card]
    board.list_lists.return_value = [lista]

    mocker.patch.object(tasks, "_get_board", return_value=board)

    resultado = tasks.remover_tarefa(card_id="card-123")

    assert resultado["sucesso"] is False
    assert resultado["dados"] is None
    assert "Falha na comunicação" in resultado["mensagem"]

    card.delete.assert_called_once_with()