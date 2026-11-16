"""Apuração financeira (dono: P4). Migrar do Rag/financeiro_modulo.py."""

from .contrato import Resultado, nao_implementada


def apurar_financeiro(
    produtor: str,
    data_inicio: str = "",
    data_fim: str = "",
) -> Resultado:
    """Apura as vendas de um produtor: total vendido, recebido e em aberto.

    Use para qualquer pergunta sobre valores, vendas ou pagamentos de um
    produtor. Os números vêm desta ferramenta; não calcule nada por conta própria.

    Args:
        produtor: Nome do produtor.
        data_inicio: Início do período, formato AAAA-MM-DD. Vazio = desde o início.
        data_fim: Fim do período, formato AAAA-MM-DD. Vazio = até hoje.

    Returns:
        Resultado no formato do contrato, com vendas por data, totais e
        `dados["lacunas"]` (registros incompletos), e as linhas do CSV em `fontes`.
    """
    return nao_implementada("apurar_financeiro")
