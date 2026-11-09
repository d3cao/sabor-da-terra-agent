import os
import sys
import streamlit as st

# Configuração da Página do Streamlit (Deve ser sempre a primeira instrução Streamlit)
st.set_page_config(
    page_title="Sabor da Terra - Assistente Construtor", layout="centered"
)

# Adiciona o diretório raiz ao path do Python com segurança absoluta
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
  sys.path.append(parent_dir)

# Importação segura dos módulos desenvolvidos pela equipe
try:
  from Rag.financeiro_modulo import apurar_financeiro
  from Rag.produtores_modulo import buscar_acervo_local

  modulos_carregados = True
except Exception as e:
  modulos_carregados = False
  erro_import = e

st.title("🌱 Assistente Inteligente - Cooperativa Sabor da Terra")
st.markdown(
    "*Módulo de Orquestração Local (Agente Construtor + Sub-Módulos)*"
)

# Alerta caso haja algum problema de importação dos módulos
if not modulos_carregados:
  st.error(
      f"⚠️ Erro ao carregar os módulos locais: {erro_import}. Verifique se os"
      " arquivos estão na pasta Rag/."
  )

# Inicializa o histórico de conversas na sessão
if "messages" not in st.session_state:
  st.session_state.messages = []

# Exibe o histórico de mensagens na interface do Streamlit
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

# Entrada do usuário pelo chat (Interface principal)
if prompt := st.chat_input(
    "Ex: 'Resumo de outubro da Ana' ou 'Quem tem certificação de mel?'"
):
  # Adiciona a mensagem do usuário ao histórico
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  # Lógica do Agente Construtor (Router / Orquestrador)
  resposta = ""
  prompt_lower = prompt.lower()

  with st.chat_message("assistant"):
    with st.spinner("O Agente Construtor está a processar a solicitação..."):

      if not modulos_carregados:
        resposta = (
            "⚠️ Os módulos de backend não estão disponíveis para processar o"
            " pedido."
        )

      # Intenção 1: Módulo Financeiro
      elif any(
          palavra in prompt_lower
          for palavra in ["resumo", "outubro", "financeiro", "vendas"]
      ):
        # Identifica o produtor mencionado de forma dinâmica
        nome_alvo = "Ana"  # Padrão
        if "maria" in prompt_lower:
          nome_alvo = "Maria"
        elif "antonio" in prompt_lower or "antônio" in prompt_lower:
          nome_alvo = "Antônio"

        dados_fin = apurar_financeiro(nome_alvo)

        if isinstance(dados_fin, dict):
          resposta = (
              f"📊 **Sub-Agente Financeiro - Relatório Apurado:**\n\n"
              f"- **Produtora(o):** {dados_fin['produtor']}\n"
              f"- **Vendas Totais:** R$ {dados_fin['vendas_totais']:.2f}\n"
              f"- **Recebido:** R$ {dados_fin['recebido']:.2f}\n"
              f"- **Em Aberto (Pendente):** R$ {dados_fin['em_aberto']:.2f}\n\n"
              f"*(Dados processados deterministicamente via Pandas local).*_"
          )
        else:
          resposta = str(dados_fin)

      # Intenção 2: Módulo de Produtores e Acervo (RAG Local)
      elif any(
          palavra in prompt_lower
          for palavra in [
              "certificação",
              "mel",
              "queijo",
              "laudo",
              "contrato",
              "ficha",
          ]
      ):
        evidencias = buscar_acervo_local(prompt)

        if isinstance(evidencias, list) and len(evidencias) > 0:
          resposta = (
              f"🔍 **Sub-Agente de Acervo (RAG Local) - Evidências"
              f" Encontradas:**\n\n"
          )
          for ev in evidencias:
            resposta += (
                f"📄 **Fonte:** `{ev['arquivo']}`\n"
                f"> *Trecho:* {ev['trecho']}\n\n"
            )
        else:
          resposta = (
              "🔍 **RAG Local:** Não encontrei referências diretas nos"
              " documentos oficiais para esta consulta."
          )

      # Intenção 3: Triagem ou Genérico
      else:
        resposta = (
            "🤖 **Agente Construtor:** Compreendi a mensagem. Para consultar os"
            " sub-agentes, experimente pedir o **resumo financeiro** (ex:"
            " *'resumo de outubro da Ana'*) ou consultar o **acervo documental**"
            " (ex: *'certificação de mel'*)."
        )

    st.markdown(resposta)

  # Salva a resposta no histórico da sessão
  st.session_state.messages.append({"role": "assistant", "content": resposta})