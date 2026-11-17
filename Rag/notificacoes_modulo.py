
"""Geração de notificações de pedidos da Cooperativa Sabor da Terra."""

import csv
import json
import os
from pathlib import Path


def obter_pasta_dados():
    configurada = os.getenv("SABOR_DATA_DIR")

    if configurada:
        return Path(configurada)

    return Path(__file__).resolve().parent.parent / "Facepe"


def localizar_arquivo(nome):
    raiz = obter_pasta_dados()

    candidatos = [
        raiz / nome,
        raiz / "dados" / nome,
        Path(__file__).resolve().parent.parent / "dados" / nome,
    ]

    for caminho in candidatos:
        if caminho.exists():
            return caminho

    raise FileNotFoundError(
        f"Arquivo não encontrado: {nome}"
    )


def carregar_produtores():
    caminho = localizar_arquivo("produtores.csv")

    with caminho.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:
        return list(csv.DictReader(arquivo))


def carregar_pedidos():
    caminho = localizar_arquivo("pedidos.json")

    with caminho.open(
        "r",
        encoding="utf-8"
    ) as arquivo:
        dados = json.load(arquivo)

    if isinstance(dados, dict):
        dados = dados.get("pedidos", [])

    if not isinstance(dados, list):
        raise ValueError(
            "pedidos.json deve conter uma lista de pedidos."
        )

    return dados


def obter_valor(registro, *chaves):
    for chave in chaves:
        valor = registro.get(chave)

        if valor not in (None, ""):
            return str(valor).strip()

    return ""


def relacionar_produtor(pedido, produtores):
    """Relaciona pedido e produtor por ID ou nome."""

    id_pedido = obter_valor(
        pedido,
        "produtor_id",
        "id_produtor",
        "codigo_produtor"
    )

    nome_pedido = obter_valor(
        pedido,
        "produtor",
        "nome_produtor",
        "produtor_nome"
    )

    for produtor in produtores:

        id_produtor = obter_valor(
            produtor,
            "id",
            "produtor_id",
            "codigo",
            "codigo_produtor"
        )

        nome_produtor = obter_valor(
            produtor,
            "nome",
            "nome_produtor"
        )

        if (
            id_pedido
            and id_produtor
            and id_pedido.casefold() == id_produtor.casefold()
        ):
            return produtor

        if (
            nome_pedido
            and nome_produtor
            and nome_pedido.casefold() == nome_produtor.casefold()
        ):
            return produtor

    return None


def gerar_notificacao(produtor, pedido):

    mensagem = f"""
Olá, {obter_valor(produtor, 'nome', 'nome_produtor') or 'produtor(a)'}!

A Cooperativa Sabor da Terra informa
que você recebeu um novo pedido.

Produto: {obter_valor(pedido, 'produto') or 'Não informado'}
Quantidade: {obter_valor(pedido, 'quantidade') or 'Não informada'} {obter_valor(pedido, 'unidade')}
Entrega: {obter_valor(pedido, 'data_entrega', 'entrega') or 'A combinar'}

Por favor, confirme sua disponibilidade.

Cooperativa Sabor da Terra
"""

    return mensagem.strip()


def listar_notificacoes():

    produtores = carregar_produtores()
    pedidos = carregar_pedidos()

    notificacoes = []
    sem_vinculo = []

    for indice, pedido in enumerate(pedidos, start=1):

        produtor = relacionar_produtor(
            pedido,
            produtores
        )

        if produtor:

            notificacoes.append({
                "produtor": produtor,
                "pedido": pedido,
                "mensagem": gerar_notificacao(
                    produtor,
                    pedido
                )
            })

        else:

            sem_vinculo.append({
                "pedido": pedido,
                "indice": indice
            })

    return notificacoes, sem_vinculo


def consultar_notificacoes(pergunta=""):

    notificacoes, sem_vinculo = listar_notificacoes()

    pergunta = (pergunta or "").casefold().strip()

    if pergunta:

        filtradas = []

        for item in notificacoes:

            nome = obter_valor(
                item["produtor"],
                "nome",
                "nome_produtor"
            ).casefold()

            produto = obter_valor(
                item["pedido"],
                "produto"
            ).casefold()

            if pergunta in nome or pergunta in produto:
                filtradas.append(item)

        notificacoes = filtradas

    return notificacoes, sem_vinculo
