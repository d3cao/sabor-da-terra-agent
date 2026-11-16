"""Agente único do Sabor da Terra (padrão ADK).

Só o P1 edita este arquivo. Ferramenta nova ou ajuste no prompt: peçam ao P1.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

from .prompts import instrucao_raiz
from .tools import FERRAMENTAS

# O `adk web` já carrega o .env da pasta do agente; o Streamlit não, então
# carregamos aqui também. Não sobrescreve variáveis já definidas no ambiente.
load_dotenv(Path(__file__).parent / ".env")

MODELO = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

root_agent = Agent(
    name="sabor_da_terra",
    model=MODELO,
    description="Assistente da Cooperativa Sabor da Terra: pedidos, documentos e comunicação com produtores.",
    instruction=instrucao_raiz,
    tools=FERRAMENTAS,
)
