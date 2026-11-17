"""Agente de pedidos e notificações."""
import json
try:
    from Rag.produtores_modulo import consultar_dados_operacionais
    from Rag.notificacoes_modulo import consultar_notificacoes
except ImportError:
    from produtores_modulo import consultar_dados_operacionais
    from notificacoes_modulo import consultar_notificacoes
from .common import gerar_resposta_com_contexto

def executar(pergunta, historico=None, intencao="pedido"):
    historico = historico or []
    if intencao == "notificacao":
        notificacoes, sem_vinculo = consultar_notificacoes(pergunta)
        if not notificacoes:
            return ("Não encontrei pedidos associados aos produtores. Confira os IDs e nomes em pedidos.json e produtores.csv.")
        blocos = [item["mensagem"] for item in notificacoes]
        resposta = f"Foram encontradas {len(blocos)} notificação(ões):\n\n" + "\n\n---\n\n".join(blocos)
        if sem_vinculo:
            resposta += f"\n\nAtenção: {len(sem_vinculo)} pedido(s) não foram associados a um produtor."
        return resposta
    dados = consultar_dados_operacionais(
        pergunta,
        fontes=["produtores.csv", "sazonalidade.csv", "tabela_precos_outubro_2026.csv"],
    )
    contexto = json.dumps(dados, ensure_ascii=False, indent=2, default=str)
    return gerar_resposta_com_contexto(pergunta, contexto, historico)
