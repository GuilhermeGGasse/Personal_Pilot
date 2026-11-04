
"""Configuração do agente principal PersonalPilot."""

from google.adk.agents import Agent

from agenttaskmanager.prompts import AGENT_INSTRUCTION
from agenttaskmanager.tools.tasks import (
    adicionar_tarefa,
    editar_tarefa,
    get_temporal_context,
    listar_tarefas,
    mudar_status_tarefa,
    remover_tarefa,
)

root_agent = Agent(
    name="personal_pilot",
    model="gemini-3.5-flash-lite",
    description=(
        "Agente de IA para organização e gerenciamento "
        "de tarefas pessoais utilizando o Trello."
    ),
    instruction=AGENT_INSTRUCTION,
    tools=[
        get_temporal_context,
        adicionar_tarefa,
        listar_tarefas,
        mudar_status_tarefa,
        editar_tarefa,
        remover_tarefa,
    ],
)
