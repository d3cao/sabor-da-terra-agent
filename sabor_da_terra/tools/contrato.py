"""Formato único de retorno das ferramentas (seção 3 do plano).

`status: "erro"` é só para erros esperados (lote não encontrado, argumento
inválido). Falhas inesperadas devem propagar: nada de `except Exception`
genérico dentro das ferramentas (regra 4).
"""

from typing import Any, Literal

# typing_extensions (e não typing): o Pydantic exige isso em Python < 3.12
# para gerar o schema de retorno que o ADK manda ao Gemini.
from typing_extensions import TypedDict

Status = Literal["ok", "nao_encontrado", "pendente", "erro"]


class Fonte(TypedDict):
    arquivo: str
    referencia: str  # página, linha ou seção


class Resultado(TypedDict):
    status: Status
    dados: dict[str, Any]
    fontes: list[Fonte]
    mensagem: str


def resposta(
    status: Status,
    dados: dict[str, Any] | None = None,
    fontes: list[Fonte] | None = None,
    mensagem: str = "",
) -> Resultado:
    """Monta o retorno padrão de uma ferramenta."""
    return {
        "status": status,
        "dados": dados or {},
        "fontes": fontes or [],
        "mensagem": mensagem,
    }


def nao_implementada(nome: str) -> Resultado:
    """Retorno dos stubs enquanto a ferramenta real não chega em `main`."""
    return resposta(
        "erro",
        mensagem=f"A ferramenta {nome} ainda não foi implementada (stub do esqueleto).",
    )
