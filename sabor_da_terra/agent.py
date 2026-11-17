"""Agente único do Sabor da Terra (padrão ADK).

Só o P1 edita este arquivo. Ferramenta nova ou ajuste no prompt: peçam ao P1.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types

from .callbacks import (
    limitar_iteracoes,
    registrar_resultado,
    tratar_erro_modelo,
    validar_argumentos,
)
from .prompts import instrucao_raiz
from .tools import FERRAMENTAS

# Aceita o .env na pasta do agente ou na raiz do projeto (o primeiro vence).
# O Streamlit não carrega .env sozinho, então carregamos aqui.
# Não sobrescreve variáveis já definidas no ambiente.
_PACOTE = Path(__file__).parent
load_dotenv(_PACOTE / ".env")
load_dotenv(_PACOTE.parent / ".env")

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Repete a chamada quando a API devolve 429/503 (sobrecarga), com espera
# crescente. Evita que um pico curto derrube a demo; poucas tentativas para
# o chat não ficar "carregando" muito tempo quando o modelo está fora do ar.
modelo = Gemini(
    model=MODELO,
    retry_options=types.HttpRetryOptions(
        attempts=3,
        initial_delay=2,
        max_delay=8,
        http_status_codes=[429, 500, 503, 504],
    ),
)

root_agent = Agent(
    name="sabor_da_terra",
    model=modelo,
    description="Assistente da Cooperativa Sabor da Terra: pedidos, documentos e comunicação com produtores.",
    instruction=instrucao_raiz,
    tools=FERRAMENTAS,
    before_tool_callback=validar_argumentos,
    after_tool_callback=registrar_resultado,
    before_model_callback=limitar_iteracoes,
    on_model_error_callback=tratar_erro_modelo,
)
