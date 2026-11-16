"""Triagem de pedidos (dono: P2).

O pedido em análise fica em `tool_context.state["pedido_atual"]` (regra 5).
Não guardar o pedido só no `st.session_state` do Streamlit.
"""

from google.adk.tools import ToolContext

from .contrato import Resultado, nao_implementada

CHAVE_PEDIDO = "pedido_atual"


def registrar_pedido(
    tool_context: ToolContext,
    comprador: str,
    itens: list[dict],
    data_recebimento: str,
    prazo_entrega: str = "",
    dia_semana_citado: str = "",
    observacao: str = "",
) -> Resultado:
    """Registra um NOVO pedido de compra a partir da mensagem do comprador.

    Use quando chegar um pedido novo. Se o usuário estiver completando ou
    corrigindo o pedido já em análise (ex.: "são 4 caixas"), use
    `atualizar_pedido` em vez desta.

    Args:
        comprador: Nome do comprador (pessoa ou empresa) como aparece na mensagem.
        itens: Lista de itens, cada um com "produto" (str), "quantidade" (número)
            e "unidade" (str, ex.: "kg", "caixa"). Deixe fora o que não foi dito.
        data_recebimento: Data em que a mensagem foi recebida, formato AAAA-MM-DD.
        prazo_entrega: Data de entrega pedida, formato AAAA-MM-DD. Vazio se não informada.
        dia_semana_citado: Dia da semana citado pelo comprador (ex.: "sexta"), se houver.
        observacao: Qualquer outra informação relevante da mensagem.

    Returns:
        Resultado no formato do contrato. `status` "pendente" quando faltam
        campos obrigatórios, listados em `dados["campos_pendentes"]`.
    """
    return nao_implementada("registrar_pedido")


def atualizar_pedido(
    tool_context: ToolContext,
    comprador: str = "",
    itens: list[dict] | None = None,
    data_recebimento: str = "",
    prazo_entrega: str = "",
    dia_semana_citado: str = "",
    observacao: str = "",
) -> Resultado:
    """Completa ou corrige o pedido JÁ em análise, sem perder os campos existentes.

    Use quando o usuário trouxer informação que falta ou corrigir algo do pedido
    atual. Passe só os campos que mudaram; os demais ficam como estão.

    Args:
        comprador: Novo nome do comprador, se mudou.
        itens: Itens a acrescentar ou corrigir, cada um com "produto",
            "quantidade" e "unidade".
        data_recebimento: Data de recebimento corrigida (AAAA-MM-DD).
        prazo_entrega: Prazo de entrega informado ou corrigido (AAAA-MM-DD).
        dia_semana_citado: Dia da semana citado, se houver.
        observacao: Observação adicional.

    Returns:
        Resultado no formato do contrato, com o pedido atualizado em `dados`.
        `status` "nao_encontrado" se não houver pedido em análise.
    """
    return nao_implementada("atualizar_pedido")


def avaliar_pedido(tool_context: ToolContext) -> Resultado:
    """Avalia o pedido em análise: datas, safra, capacidade e produtores sugeridos.

    Use depois de registrar (ou atualizar) o pedido. Toda a avaliação é feita em
    código: prazo anterior ao recebimento, dia da semana incoerente com a data,
    produto fora de safra, quantidade acima da capacidade, capacidade a confirmar
    e sugestão de produtores. Não tire essas conclusões por conta própria.

    Returns:
        Resultado no formato do contrato, com `dados["alertas"]` e
        `dados["produtores_sugeridos"]`.
    """
    return nao_implementada("avaliar_pedido")
