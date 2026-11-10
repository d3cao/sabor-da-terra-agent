# 🌿 Assistente Inteligente - Cooperativa Sabor da Terra

Protótipo modular local de um assistente inteligente baseado em orquestração de sub-agentes determinísticos, RAG local e integração com LLM open-source (Ollama), desenvolvido para a automação de processos da **Cooperativa Sabor da Terra**.

---

## 🎯 Aplicação no Estudo de Caso

Na gestão de uma cooperativa agrícola, as operações lidam frequentemente com três grandes gargalos:
1. **Lentidão e ruído na comunicação:** Notificações de demandas e relatórios de repasse financeiro aos produtores dependem de processos telefônicos manuais e repetitivos.
2. **Pedidez informal:** Clientes e compradores enviam pedidos em linguagem natural e coloquial (via mensagens de texto), dificultando a triagem e o controle de inventário.
3. **Dispersão de documentos:** Laudos técnicos da ADAGRO, certificações orgânicas e contratos ficam armazenados de forma não estruturada.

**A Solução:** O sistema atua como um assistente centralizado que interpreta pedidos informais, gera notificações e resumos financeiros automatizados de forma determinística e consulta acervos documentais sem alucinações, recorrendo a modelos de linguagem locais (Ollama) apenas para interações gerais e suporte inteligente.

---

## 🏗️ Arquitetura do Sistema e Funcionamento do Código

O projeto adota uma arquitetura **Hub-and-Spoke**, onde o núcleo orquestrador direciona as solicitações para submódulos especializados em Python:

                  ┌────────────────────────────────┐
                  │  Interface Streamlit / Router  │
                  │       (Rag/chat_local.py)      │
                  └───────────────┬────────────────┘
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ Sub-Agente       │        │ Sub-Agente       │        │ Modelo LLM       │
│ Financeiro       │        │ de Produtores/RAG│        │ Local (Ollama)   │
│ (financeiro.py)  │        │ (produtores.py)  │        │ (.env: llama3)   │
└─────────┬────────┘        └─────────┬────────┘        └──────────────────┘
│                           │
▼                           ▼
┌──────────────────┐        ┌──────────────────┐
│ Facepe/          │        │ Facepe/          │
│ financeiro.csv   │        │ acervo & JSON    │
└──────────────────┘        └──────────────────┘


### 🧠 Funcionamento dos Módulos

1. **Agente Construtor / Orquestrador (`Rag/chat_local.py`)**
   - **Interface Reativa:** Interface web interativa via **Streamlit** com controle de histórico de sessão (`st.session_state`).
   - **Roteamento de Intenções:** Analisa a entrada em linguagem natural e decide deterministicamente qual sub-agente acionar:
     - *Intenções Financeiras* ➔ Chama `apurar_financeiro()`
     - *Intenções Documentais* ➔ Chama `buscar_acervo_local()`
     - *Triagem de Pedidos* ➔ Chama `processar_pedido_natural()`
     - *Comunicação/Resumos* ➔ Chama `gerar_resumo_produtor()`
     - *Consultas Genéricas* ➔ Transmite a requisição ao **Ollama** usando o modelo definido no arquivo `.env`.

2. **Sub-Agente Financeiro (`Rag/financeiro_modulo.py`)**
   - Processa a base estruturada `Facepe/financeiro.csv` via **Pandas**.
   - Calcula valores consolidados de vendas, totais recebidos e pendências em aberto por produtor com **precisão matemática exata** (sem risco de alucinação de valores).

3. **Sub-Agente de Produtores, Pedidos e RAG Local (`Rag/produtores_modulo.py`)**
   - **Triagem de Linguagem Natural (`processar_pedido_natural`):** Extrai produtos, quantidades e prazos a partir de pedidos informais enviados por compradores.
   - **Comunicação Otimizada (`gerar_resumo_produtor`):** Compila o saldo e os pedidos pendentes de cada produtor em mensagens prontas, eliminando chamadas manuais.
   - **RAG Local (`buscar_acervo_local`):** Varre as pastas de certificações, contratos e fichas técnicas (`Facepe/`), retornando trechos relevantes com **atribuição direta da fonte**.

4. **Gerenciamento de Ambiente (`.env`)**
   - Define dinamicamente o modelo local do Ollama (ex: `OLLAMA_MODEL=llama3`) e configurações de execução sem hardcoding no código principal.

---

## 📂 Estrutura de Diretórios

```text
sabor-da-terra-agent/
├── .env                       # Variáveis de ambiente (modelo Ollama, hosts)
├── .gitignore                 # Exclusão de base local (Facepe) e segredos
├── README.md                  # Documentação do projeto
├── Facepe/                    # Base de dados local (desconsiderada no git)
│   ├── financeiro.csv         # Registros de vendas e pagamentos
│   ├── pedidos.json           # Registros de pedidos
│   ├── certificacoes/         # Documentos de certificação orgânica
│   ├── contratos/             # Contratos da cooperativa
│   └── fichas_tecnicas/       # Fichas técnicas de produtos
└── Rag/                       # Código-fonte da aplicação
    ├── chat_local.py          # Agente Construtor / Interface Streamlit
    ├── financeiro_modulo.py   # Sub-agente de apuração financeira
    └── produtores_modulo.py   # Sub-agente de acervo documental e pedidos
🚀 Como Executar o Projeto
Pró-requisitos
Python 3.10+ instalado.

Ollama instalado e em execução no sistema.

1. Instalação das Dependências
No terminal da raiz do projeto, instale as bibliotecas necessárias:

Bash
pip install streamlit pandas python-dotenv ollama
2. Download do Modelo LLM Local
Garanta que o modelo configurado no .env (ex: llama3) está baixado no seu computador:

Bash
ollama run llama3
3. Configuração do Arquivo .env
Crie ou edite o arquivo .env na raiz do projeto:

Snippet de código
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
4. Execução da Aplicação
Na raiz do projeto (sabor-da-terra-agent), execute:

Bash
streamlit run Rag/chat_local.py
Acesse a aplicação no navegador através do endereço http://localhost:8501.

💡 Exemplos de Prompts para Teste
Financeiro: "Qual o resumo de vendas da Ana?" ou "Ver financeiro de Antônio"

RAG / Acervo: "Quem possui certificação de mel?" ou "Buscar laudo técnico de queijo"

Interpretação de Pedido: "Preciso encomendar 40kg de queijo coalho para a próxima semana"

Notificação a Produtor: "Gerar notificação e resumo do produtor Antônio"

Consultas Gerais (Ollama): "Quais são as melhores práticas para conservação de produtos orgânicos?"