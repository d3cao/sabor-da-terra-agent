"""Agente Root: roteia perguntas para os agentes especializados."""
from .common import classificar_intencao, fallback_intencao, normalizar_pergunta
from .financeiro_agent import executar as executar_financeiro
from .produtores_agent import executar as executar_produtores
from .pedidos_agent import executar as executar_pedidos
from .lotes_agent import executar as executar_lotes

def executar_rota(pergunta, historico=None):
    historico = historico or []
    p = normalizar_pergunta(pergunta)

    # Rastreabilidade tem precedência quando há identificador ou termos de lote.
    if "lote" in p or "rastreabilidade" in p or "validade do lote" in p:
        return executar_lotes(pergunta, historico)

    # Certificações e consultas coletivas são encaminhadas ao agente de produtores.
    if any(t in p for t in ("certificacao", "certificado", "organico", "laudo")):
        return executar_produtores(pergunta, historico, intencao="documental")

    # Financeiro é determinístico: não depende do classificador para escolher a ferramenta.
    if any(t in p for t in ("financeiro","vendas","vendeu","pagamento","pagamentos","pendente","em aberto","recebido","recebeu","saldo","faturamento","maior valor pendente","maior pendencia")):
        return executar_financeiro(pergunta, historico)

    intencao = classificar_intencao(pergunta, historico)

    if intencao in ("pedido", "notificacao"):
        return executar_pedidos(pergunta, historico, intencao=intencao)

    if intencao in ("produtor", "documental", "operacional"):
        return executar_produtores(pergunta, historico, intencao=intencao)

    # Fallback conversacional permanece no classificador/resposta original.
    from .common import gerar_resposta_com_contexto
    return gerar_resposta_com_contexto(
        pergunta,
        "Esta pergunta não acionou uma consulta às bases.",
        historico,
    )
