import os
import sys
from dotenv import load_dotenv
import ollama
import streamlit as st

# Carrega as variáveis de ambiente do arquivo .env (na raiz do projeto)
load_dotenv()

# Define o modelo Ollama obtido do .env ou assume 'gpt-oss:120b-cloud' como fallback
MODELO_OLLAMA = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")

# Configuração da Página do Streamlit (deve vir no início das chamadas do Streamlit)
st.set_page_config(
    page_title="Sabor da Terra - Assistente Construtor", layout="centered"
)

# Adiciona o diretório raiz ao path do Python com segurança
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
  sys.path.append(parent_dir)

# Importação dos módulos locais da equipe
try:
  from Rag.financeiro_modulo import apurar_financeiro
  from Rag.produtores_modulo import (
      buscar_acervo_local,
      gerar_resumo_produtor,
      processar_pedido_natural,
  )

  modulos_carregados = True
except Exception as e:
  modulos_carregados = False
  erro_import = e

st.title("🌱 Assistente Inteligente - Cooperativa Sabor da Terra")
st.markdown(
    f"*Módulo de Orquestração Local com Ollama (`{MODELO_OLLAMA}`)*"
)

if not modulos_carregados:
  st.error(f"⚠️ Erro ao carregar os módulos locais: {erro_import}")

if "messages" not in st.session_state:
  st.session_state.messages = []

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input(
    "Digite sua mensagem (ex: 'Resumo da Ana', 'Certificação de mel', ou"
    " qualquer dúvida)..."
):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  resposta = ""
  prompt_lower = prompt.lower()

  with st.chat_message("assistant"):
    with st.spinner("O Ollama e os sub-agentes estão a processar..."):

      if not modulos_carregados:
        resposta = "⚠️ Os módulos de backend não estão disponíveis."

      # Intenção 1: Módulo Financeiro
      elif any(
          palavra in prompt_lower
          for palavra in ["resumo", "outubro", "financeiro", "vendas"]
      ):
        nome_alvo = "Ana"
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
              f"- **Em Aberto (Pendente):** R$ {dados_fin['em_aberto']:.2f}"
          )
        else:
          resposta = str(dados_fin)

      # Intenção 2: Módulo de Acervo e RAG Local
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
          resposta = "🔍 **RAG Local:** Não encontrei referências diretas."

      # Intenção 3: Processar Pedidos Informais
      elif any(
          palavra in prompt_lower
          for palavra in ["pedido", "preciso de", "quero comprar", "encomenda"]
      ):
        resposta = processar_pedido_natural(prompt)

      # Intenção 4: Notificações de Produtores
      elif any(
          palavra in prompt_lower
          for palavra in [
              "notificar",
              "notificacao",
              "notificação",
              "resumo do produtor",
              "comunicar",
          ]
      ):
        nome_alvo = "Maria"
        if "antonio" in prompt_lower or "antônio" in prompt_lower:
          nome_alvo = "Antônio"
        elif "ana" in prompt_lower:
          nome_alvo = "Ana"
        resposta = gerar_resumo_produtor(nome_alvo)

      # Intenção 5: Execução via Ollama configurado no .env
      else:
        try:
          resposta_ollama = ollama.chat(
              model=MODELO_OLLAMA,
              messages=[{
                  "role": "system",
                  "content": (
                      "Você é o assistente inteligente da cooperativa agrícola"
                      " Sabor da Terra. Responda de forma prestativa, curta e"
                      " objetiva em português."
                  ),
              }, {
                  "role": "user",
                  "content": prompt,
              }],
          )
          resposta = resposta_ollama["message"]["content"]
        except Exception as err:
          resposta = (
              f"🤖 **Agente Construtor:** (Ollama offline ou modelo"
              f" '{MODELO_OLLAMA}' não encontrado: {err}). Tente pedir um resumo"
              " financeiro ou consulta documental."
          )

    st.markdown(resposta)
  st.session_state.messages.append({"role": "assistant", "content": resposta})