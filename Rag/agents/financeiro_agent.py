"""Agente financeiro: usa os cálculos determinísticos do módulo financeiro."""
import os, ollama
from dotenv import load_dotenv
load_dotenv()
MODELO_OLLAMA = os.getenv("OLLAMA_MODEL", "qwen3:8b")
try:
    from Rag.financeiro_modulo import apurar_financeiro
except ImportError:
    from financeiro_modulo import apurar_financeiro
from .common import normalizar_pergunta


def formatar_resposta_financeira(pergunta, dados):
    """Formata números diretamente dos cálculos Python, sem delegar valores ao LLM."""
    if not isinstance(dados, dict):
        return str(dados)
    if dados.get("erro"):
        return dados.get("mensagem", "Não foi possível consultar o financeiro.")
    if dados.get("mensagem") and not dados.get("transacoes"):
        return dados["mensagem"]

    def moeda(valor):
        valor = float(valor or 0)
        return (f"R$ {valor:,.2f}").replace(",", "X").replace(".", ",").replace("X", ".")

    p = normalizar_pergunta(pergunta)
    individual = dados.get("tipo_consulta") == "financeiro_individual"
    nome = dados.get("produtor_nome", "")
    codigo = dados.get("produtor_id", "")
    periodo = dados.get("periodo_consultado", "todos os períodos disponíveis")

    if any(x in p for x in ["maior valor pendente", "maior pendencia", "quem tem mais pendencia"]):
        maior = dados.get("maior_pendencia")
        if not maior:
            return "Não há pagamentos pendentes registrados no período consultado."
        return (f"O produtor com maior valor pendente é {maior.get('produtor_nome', maior.get('produtor', ''))} "
                f"({maior.get('produtor_id', '')}), com {moeda(maior.get('valor_pendente', maior.get('valor_em_aberto', 0)))} em aberto.")

    if any(x in p for x in ["quais pagamentos", "pagamentos do", "transacoes do", "transações do"]):
        transacoes = dados.get("transacoes_pendentes", [])
        if not transacoes:
            return f"{nome} ({codigo}) não possui pagamentos pendentes registrados no período consultado."
        linhas = [f"Pagamentos em aberto de {nome} ({codigo}):"]
        for t in transacoes:
            partes = [str(t.get("produto") or "Produto não informado"), moeda(t.get("valor_total", 0))]
            if t.get("data_vencimento"):
                partes.append(f"vencimento: {t['data_vencimento']}")
            if t.get("status_pagamento"):
                partes.append(f"status: {t['status_pagamento']}")
            linhas.append("• " + " — ".join(partes))
        return "\n".join(linhas)

    if any(x in p for x in ["quais produtores", "quem possui", "quem tem", "produtores com", "produtores possuem"]):
        lista = dados.get("produtores_com_pendencias", [])
        if not lista:
            return "Não há produtores com pagamentos pendentes registrados no período consultado."
        linhas = ["Produtores com pagamentos pendentes:"]
        for item in lista:
            linhas.append(f"• {item.get('produtor_nome', item.get('produtor', ''))} ({item.get('produtor_id', '')}): {moeda(item.get('valor_pendente', item.get('valor_em_aberto', 0)))}")
        return "\n".join(linhas) + f"\n\nTotal pendente da cooperativa: {moeda(dados.get('total_pendente', dados.get('total_em_aberto', 0)))}."

    if individual:
        if "recebid" in p or "recebeu" in p:
            rotulo, valor = "Total recebido", dados.get("total_recebido", 0)
        elif "atras" in p or "vencid" in p:
            rotulo, valor = "Total em atraso", dados.get("total_atrasado", 0)
        elif "pend" in p or "aberto" in p:
            rotulo, valor = "Total pendente", dados.get("total_pendente", 0)
        else:
            rotulo, valor = "Vendas registradas", dados.get("total_vendas", 0)
        return (f"{rotulo} de {nome} ({codigo}): {moeda(valor)}. "
                f"Total de transações: {dados.get('quantidade_transacoes', 0)}. Período: {periodo}.")

    # Consulta geral focada em um indicador específico.
    if "recebid" in p or "recebeu" in p or "quanto ja foi" in p:
        return f"A cooperativa já recebeu {moeda(dados.get('total_recebido', 0))}, em {dados.get('quantidade_pagas', 0)} transações pagas. Período: {periodo}."
    if "atras" in p or "vencid" in p:
        return f"A cooperativa possui {moeda(dados.get('total_atrasado', 0))} em pagamentos atrasados, distribuídos em {dados.get('quantidade_atrasadas', 0)} transações. Período: {periodo}."
    if "pend" in p or "aberto" in p:
        return f"A cooperativa possui {moeda(dados.get('total_pendente', dados.get('total_em_aberto', 0)))} em pagamentos pendentes. Período: {periodo}."
    return ("Indicadores financeiros da cooperativa:\n"
            f"• Vendas totais: {moeda(dados.get('total_vendas', dados.get('vendas_totais_sem_cancelamentos', 0)))}\n"
            f"• Total recebido: {moeda(dados.get('total_recebido', 0))}\n"
            f"• Total pendente: {moeda(dados.get('total_pendente', dados.get('total_em_aberto', 0)))}\n"
            f"• Total em atraso: {moeda(dados.get('total_atrasado', 0))}\n"
            f"• Transações: {dados.get('quantidade_transacoes', 0)}.")

def executar(pergunta, historico=None):
    dados = apurar_financeiro(pergunta)
    if isinstance(dados, str):
        return dados
    if isinstance(dados, dict) and dados.get("erro"):
        return dados.get("mensagem", "Não foi possível consultar o financeiro.")
    # O Python é a fonte de verdade dos números. O Ollama só introduz a resposta.
    try:
        abertura = ollama.chat(
            model=MODELO_OLLAMA,
            messages=[
                {"role":"system","content":"Interprete a intenção financeira e escreva uma introdução curta. Não inclua números, valores, datas, percentuais ou nomes. Não calcule. Português brasileiro."},
                {"role":"user","content":pergunta},
            ],
            options={"temperature":0.1},
        )["message"]["content"].strip()
    except Exception:
        abertura = "Consultei os registros financeiros disponíveis."
    return f"{abertura}\n\n{formatar_resposta_financeira(pergunta, dados)}"
