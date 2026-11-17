"""Callbacks do agente: validação de argumentos, limite de iterações e log (P1-3).

Atenção (regra 8): o ADK chama os callbacks passando os argumentos POR NOME.
Os parâmetros têm de se chamar exatamente:
- before_tool_callback(tool, args, tool_context)
- after_tool_callback(tool, args, tool_context, tool_response)
- before_model_callback(callback_context, llm_request)
- on_model_error_callback(callback_context, llm_request, error)
Renomear qualquer um causa erro em execução.

O que cada um faz:
- `validar_argumentos`: confere os argumentos antes de a ferramenta rodar. Se
  algo estiver errado, devolve `status: "erro"` no formato do contrato e a
  ferramenta NÃO é executada; o modelo recebe o erro e pode corrigir.
- `limitar_iteracoes`: conta as chamadas ao modelo em cada mensagem do usuário
  e interrompe ao passar de LIMITE_ITERACOES (o e-book manda limitar; para
  agente único não há parâmetro pronto, então contamos aqui).
- `registrar_resultado`: loga o status devolvido por cada ferramenta.
- `tratar_erro_modelo`: quando a API do Gemini está fora do ar (503/429) ou o
  modelo não existe (404), devolve uma mensagem legível em vez de quebrar o chat.

As regras de negócio (prazo anterior ao recebimento, safra, capacidade,
vigência) NÃO ficam aqui: são das ferramentas. Aqui só entra o formato.
"""

import logging
from datetime import date
from typing import Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import errors, types

from .tools.contrato import resposta

log = logging.getLogger("sabor_da_terra")

LIMITE_ITERACOES = 5
CHAVE_CONTADOR = "temp:contador_iteracoes"

# --- Regras de formato dos argumentos ---------------------------------------

CAMPOS_DATA = {"data_recebimento", "prazo_entrega", "data", "data_inicio", "data_fim"}

OBRIGATORIOS: dict[str, list[str]] = {
    "registrar_pedido": ["comprador", "data_recebimento"],
    "buscar_documentos": ["pergunta"],
    "verificar_certificacao": ["produtor", "produto", "certificacao", "data"],
    "consultar_lote": ["codigo_lote"],
    "apurar_financeiro": ["produtor"],
    "gerar_comunicacao": ["tipo", "produtor"],
}

VALORES_PERMITIDOS: dict[tuple[str, str], set[str]] = {
    ("gerar_comunicacao", "tipo"): {"resumo", "notificacao"},
    ("buscar_documentos", "tipo_documento"): {"", "certificacao", "contrato", "ficha_tecnica"},
}

# Ferramentas que recebem lista de itens, e se a lista pode vir vazia.
FERRAMENTAS_COM_ITENS = {"registrar_pedido": False, "atualizar_pedido": True}


def _vazio(valor: Any) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def _erros_data(nome: str, valor: Any) -> list[str]:
    if _vazio(valor):
        return []
    if not isinstance(valor, str):
        return [f"'{nome}' deve ser texto no formato AAAA-MM-DD."]
    try:
        date.fromisoformat(valor.strip())
    except ValueError:
        return [f"'{nome}' = '{valor}' não é uma data válida no formato AAAA-MM-DD."]
    if len(valor.strip()) != 10:
        return [f"'{nome}' = '{valor}' deve ter só a data, no formato AAAA-MM-DD."]
    return []


def _erros_itens(itens: Any, pode_vazio: bool) -> list[str]:
    if itens is None:
        return [] if pode_vazio else ["'itens' é obrigatório: informe ao menos um produto."]
    if not isinstance(itens, list):
        return ["'itens' deve ser uma lista de objetos com 'produto', 'quantidade' e 'unidade'."]
    if not itens and not pode_vazio:
        return ["'itens' está vazio: informe ao menos um produto."]
    problemas = []
    for i, item in enumerate(itens, start=1):
        if not isinstance(item, dict):
            problemas.append(f"item {i} deve ser um objeto com 'produto', 'quantidade' e 'unidade'.")
            continue
        if _vazio(item.get("produto")):
            problemas.append(f"item {i} está sem 'produto'.")
        qtd = item.get("quantidade")
        # Quantidade ausente é permitida: o pedido fica pendente (regra do P2).
        if qtd is not None and (isinstance(qtd, bool) or not isinstance(qtd, (int, float)) or qtd <= 0):
            problemas.append(f"item {i}: 'quantidade' deve ser um número maior que zero (veio {qtd!r}).")
    return problemas


def validar(nome_ferramenta: str, args: dict[str, Any]) -> list[str]:
    """Devolve a lista de problemas de formato nos argumentos (vazia se estiver tudo certo)."""
    problemas: list[str] = []
    for campo in OBRIGATORIOS.get(nome_ferramenta, []):
        if _vazio(args.get(campo)):
            problemas.append(f"'{campo}' é obrigatório e veio vazio.")
    for campo, valor in args.items():
        if campo in CAMPOS_DATA:
            problemas += _erros_data(campo, valor)
        permitidos = VALORES_PERMITIDOS.get((nome_ferramenta, campo))
        if permitidos is not None and (valor or "") not in permitidos:
            opcoes = ", ".join(sorted(v for v in permitidos if v))
            problemas.append(f"'{campo}' = '{valor}' não é válido. Use um destes: {opcoes}.")
    if nome_ferramenta in FERRAMENTAS_COM_ITENS:
        problemas += _erros_itens(args.get("itens"), FERRAMENTAS_COM_ITENS[nome_ferramenta])
    return problemas


# --- Callbacks ----------------------------------------------------------------

def validar_argumentos(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> dict | None:
    """before_tool_callback: loga a chamada e barra argumentos com formato inválido."""
    log.info("ferramenta=%s args=%s", tool.name, args)
    problemas = validar(tool.name, args)
    if not problemas:
        return None  # segue para a ferramenta
    log.warning("ferramenta=%s argumentos inválidos: %s", tool.name, problemas)
    return resposta(
        "erro",
        dados={"argumentos_invalidos": problemas},
        mensagem=(
            f"Argumentos inválidos para {tool.name}: " + " ".join(problemas)
            + " Corrija os argumentos ou pergunte à equipe o que falta."
        ),
    )


def registrar_resultado(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: Any
) -> dict | None:
    """after_tool_callback: loga o status e a mensagem devolvidos pela ferramenta."""
    if isinstance(tool_response, dict):
        log.info(
            "ferramenta=%s status=%s fontes=%d mensagem=%s",
            tool.name,
            tool_response.get("status"),
            len(tool_response.get("fontes") or []),
            str(tool_response.get("mensagem", ""))[:200],
        )
    else:
        log.warning("ferramenta=%s devolveu fora do contrato: %r", tool.name, tool_response)
    return None  # não altera a resposta


def _mensagem(texto: str) -> LlmResponse:
    return LlmResponse(content=types.Content(role="model", parts=[types.Part(text=texto)]))


def limitar_iteracoes(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """before_model_callback: interrompe ao passar de LIMITE_ITERACOES chamadas ao modelo
    na mesma mensagem do usuário."""
    contador = callback_context.state.get(CHAVE_CONTADOR) or {}
    invocacao = callback_context.invocation_id
    n = contador.get("n", 0) + 1 if contador.get("invocacao") == invocacao else 1
    callback_context.state[CHAVE_CONTADOR] = {"invocacao": invocacao, "n": n}
    log.info("chamada ao modelo %d/%d (invocação %s)", n, LIMITE_ITERACOES, invocacao)
    if n <= LIMITE_ITERACOES:
        return None
    log.warning("limite de %d iterações atingido (invocação %s)", LIMITE_ITERACOES, invocacao)
    return _mensagem(
        f"Parei aqui porque atingi o limite de {LIMITE_ITERACOES} etapas para uma única "
        "mensagem. Pode reformular o pedido em partes menores ou me dizer qual informação "
        "falta para eu continuar?"
    )


def tratar_erro_modelo(
    callback_context: CallbackContext, llm_request: LlmRequest, error: Exception
) -> LlmResponse | None:
    """on_model_error_callback: mensagem legível quando a API do Gemini falha por
    sobrecarga (429/503) ou modelo indisponível (404). Outros erros propagam."""
    if not isinstance(error, errors.APIError):
        return None
    modelo = llm_request.model or "(modelo do .env)"
    if error.code in (429, 500, 503, 504):
        log.warning("modelo %s indisponível: %s", modelo, error)
        return _mensagem(
            f"O modelo {modelo} está sobrecarregado no Google agora (erro {error.code}). "
            "Tente de novo em alguns instantes ou troque GEMINI_MODEL no .env."
        )
    if error.code == 404:
        log.error("modelo %s não encontrado: %s", modelo, error)
        return _mensagem(
            f"O modelo {modelo} não está disponível para esta chave (erro 404). "
            "Troque GEMINI_MODEL no .env por um modelo disponível."
        )
    return None
