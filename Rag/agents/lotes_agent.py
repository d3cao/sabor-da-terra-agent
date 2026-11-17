"""Agente de rastreabilidade de lotes."""
try:
    from Rag.lotes_modulo import consultar_lote, consultar_lotes_por_produtor, consultar_lotes_por_produto, listar_lotes, consultar_rastreabilidade
except ImportError:
    from lotes_modulo import consultar_lote, consultar_lotes_por_produtor, consultar_lotes_por_produto, listar_lotes, consultar_rastreabilidade
from .common import responder_com_evidencias

def executar(pergunta, historico=None, lote_id=None):
    historico = historico or []
    # Identificador explícito de lote (ex.: LOT-2026-0001).
    import re
    if lote_id is None:
        m = re.search(r"\bLOT[-_ ]?\d{4}[-_ ]?\d+\b", pergunta, re.I)
        lote_id = m.group(0) if m else None
    if lote_id:
        dados = consultar_rastreabilidade(lote_id)
        return responder_com_evidencias(pergunta, dados, historico)
    dados = listar_lotes()
    return responder_com_evidencias(pergunta, dados, historico)
