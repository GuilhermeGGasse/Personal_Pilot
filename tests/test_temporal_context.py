
"""Testes unitários das ferramentas de gerenciamento de tarefas."""

from datetime import datetime

from agenttaskmanager.tools import tasks


def test_get_temporal_context():
    resultado = tasks.get_temporal_context()

    assert "Data atual:" in resultado
    assert "Horário atual:" in resultado
    assert "Fuso horário:" in resultado

    formato_data = "%d/%m/%Y"

    data_extraida = resultado.split("Data atual: ")[1].split(".")[0]

    datetime.strptime(data_extraida, formato_data)
