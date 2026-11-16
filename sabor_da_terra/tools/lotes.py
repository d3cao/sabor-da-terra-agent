"""Consulta de lotes (dono: P4)."""

from .contrato import Resultado, nao_implementada


def consultar_lote(codigo_lote: str) -> Resultado:
    """Consulta um lote pelo código exato (rastreabilidade).

    Use quando o usuário citar um código de lote. A busca é por igualdade exata;
    se o lote não existir, o status é "nao_encontrado" e não se deve adivinhar.

    Args:
        codigo_lote: Código do lote exatamente como informado.

    Returns:
        Resultado no formato do contrato, com os dados do lote e arquivo e
        linha de origem em `fontes`.
    """
    return nao_implementada("consultar_lote")
