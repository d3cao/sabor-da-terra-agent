"""Exporta a lista de ferramentas do agente."""

from .acervo import buscar_documentos, verificar_certificacao
from .comunicacao import gerar_comunicacao
from .financeiro import apurar_financeiro
from .lotes import consultar_lote
from .pedidos import atualizar_pedido, avaliar_pedido, registrar_pedido

FERRAMENTAS = [
    registrar_pedido,
    atualizar_pedido,
    avaliar_pedido,
    buscar_documentos,
    verificar_certificacao,
    consultar_lote,
    apurar_financeiro,
    gerar_comunicacao,
]

__all__ = [f.__name__ for f in FERRAMENTAS] + ["FERRAMENTAS"]
