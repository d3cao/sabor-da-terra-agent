"""Agente de produtores e certificações."""
import json
try:
    from Rag.produtores_modulo import buscar_acervo_local, consultar_dados_operacionais, gerar_resumo_produtor
    from Rag.certificacoes_modulo import consultar_certificacoes
except ImportError:
    from produtores_modulo import buscar_acervo_local, consultar_dados_operacionais, gerar_resumo_produtor
    from certificacoes_modulo import consultar_certificacoes
from .common import responder_com_evidencias, gerar_resposta_com_contexto, consultar_lista_produtores, eh_consulta_coletiva_produtores, eh_consulta_certificacao

def executar(pergunta, historico=None, intencao=None):
    historico = historico or []
    if eh_consulta_certificacao(pergunta):
        return responder_com_evidencias(pergunta, consultar_certificacoes(pergunta), historico)
    if eh_consulta_coletiva_produtores(pergunta):
        return responder_com_evidencias(pergunta, consultar_lista_produtores(), historico)
    if intencao == "documental":
        evidencias = buscar_acervo_local(pergunta)
        if isinstance(evidencias, str):
            return evidencias
        if not evidencias:
            return "Não localizei essa informação nos documentos disponíveis. Tente outro termo ou informe o arquivo."
        return gerar_resposta_com_contexto(pergunta, json.dumps(evidencias, ensure_ascii=False, indent=2), historico)
    if intencao == "operacional":
        dados = consultar_dados_operacionais(pergunta)
        if not dados:
            return "Não localizei registros operacionais para essa pergunta. Informe o produto, produtor ou período."
        return gerar_resposta_com_contexto(pergunta, json.dumps(dados, ensure_ascii=False, indent=2), historico)
    dados = gerar_resumo_produtor(pergunta)
    if isinstance(dados, str):
        return dados
    return gerar_resposta_com_contexto(pergunta, json.dumps(dados, ensure_ascii=False, indent=2), historico)
