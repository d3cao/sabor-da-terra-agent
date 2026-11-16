"""Comunicação com produtores (dono: P5).

Usa o financeiro (P4) e o pedido em análise no estado (P2).
"""

from google.adk.tools import ToolContext

from .contrato import Resultado, nao_implementada


def gerar_comunicacao(
    tool_context: ToolContext,
    tipo: str,
    produtor: str,
) -> Resultado:
    """Reúne os fatos para uma mensagem a um produtor: resumo ou notificação de pedido.

    Use quando pedirem um resumo para o produtor ou para avisá-lo de um novo
    pedido. A ferramenta devolve só fatos e lacunas; redija a mensagem a partir
    deles, sem acrescentar números.

    Args:
        tipo: "resumo" (situação financeira e pedidos) ou "notificacao"
            (novo pedido em análise).
        produtor: Nome do produtor destinatário.

    Returns:
        Resultado no formato do contrato, com `dados["fatos"]` e
        `dados["lacunas"]`.
    """
    return nao_implementada("gerar_comunicacao")
