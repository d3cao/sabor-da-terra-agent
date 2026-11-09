# 🌿 Assistente Inteligente - Cooperativa Sabor da Terra

Protótipo modular local de um assistente inteligente baseado em agentes de tarefas específicas e RAG local, desenvolvido para a cooperativa Sabor da Terra.

## 🏗️ Arquitetura do Sistema
O projeto adota um modelo **Hub-and-Spoke**, onde o núcleo de orquestração (`chat_local.py`) analisa e direciona as solicitações dos utilizadores para sub-módulos especializados através de lógica determinística em Python, garantindo precisão matemática e segurança de dados:

1. **Agente Construtor (`chat_local.py`)**: Interface de chat desenvolvida em **Streamlit** que gere o histórico da sessão e faz o roteamento inteligente das intenções.
2. **Sub-Agente Financeiro (`financeiro_modulo.py`)**: Módulo de apuração de vendas, valores recebidos e saldos em aberto utilizando **Pandas** e leitura de bases CSV locais.
3. **Sub-Agente de Acervo / RAG Local (`produtores_modulo.py`)**: Sistema de varredura documental focado em ficheiros de certificados, contratos e fichas técnicas na pasta de dados.

## 📂 Estrutura de Pastas
- `Rag/`: Contém os scripts do orquestrador e dos sub-módulos.
- `Facepe/`: Base de dados local contendo os arquivos estruturados (`financeiro.csv`, `pedidos.json`, fichas e certificados).

## 🚀 Como Executar o Projeto
1. Certifique-se de que tem o Python e as dependências instaladas (`streamlit`, `pandas`).
2. Abra o terminal na raiz do projeto e execute o comando:
   ```bash
   streamlit run Rag/chat_local.py