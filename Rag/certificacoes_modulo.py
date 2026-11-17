
import os
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Optional


# Produtos e termos equivalentes para as consultas.
ALIASES_PRODUTOS = {
    "mel": ["mel"],
    "queijo": ["queijo"],
    "manteiga": ["manteiga"],
    "nata": ["nata"],
    "goiaba": ["goiaba"],
    "acerola": ["acerola"],
    "manga": ["manga"],
    "hortalicas": [
        "hortalicas", "hortalica", "alface", "rucula",
        "espinafre", "couve", "hortela", "manjericao",
        "coentro", "cebolinha", "tomate", "pimentao",
        "pepino", "berinjela", "quiabo"
    ],
    "frutas_vermelhas": [
        "morango", "amora", "mirtilo", "framboesa"
    ],
}


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )


def obter_pasta_certificados(diretorio=None):
    """
    Localiza Facepe/certificacoes.
    Aceita caminho explícito ou variável SABOR_DATA_DIR.
    """

    if diretorio:
        pasta = Path(diretorio)

        if pasta.name.casefold() == "certificacoes":
            return pasta

        return pasta / "certificacoes"

    configurado = os.getenv("SABOR_DATA_DIR")
    candidatos = []

    if configurado:
        base = Path(configurado)

        if base.name.casefold() == "certificacoes":
            candidatos.append(base)

        candidatos.append(base / "certificacoes")

    raiz = Path(__file__).resolve().parent.parent

    candidatos.extend([
        raiz / "Facepe" / "certificacoes",
        Path(__file__).resolve().parent / "Facepe" / "certificacoes"
    ])

    for pasta in candidatos:
        if pasta.is_dir():
            return pasta

    raise FileNotFoundError(
        "Pasta certificacoes não encontrada. "
        "Verifique a pasta Facepe ou SABOR_DATA_DIR."
    )


def extrair_data(texto, rotulo):
    padrao = (
        rf"{rotulo}\s*:?\s*"
        rf"(\d{{2}}/\d{{2}}/\d{{4}})"
    )

    resultado = re.search(
        padrao,
        texto,
        flags=re.IGNORECASE
    )

    if not resultado:
        return None

    try:
        return datetime.strptime(
            resultado.group(1),
            "%d/%m/%Y"
        ).date()

    except ValueError:
        return None


def extrair_produtos(texto):
    """
    Extrai a seção de produtos certificados.
    Não considera laudos sanitários como certificados orgânicos.
    """

    linhas = texto.splitlines()
    inicio = None

    for i, linha in enumerate(linhas):

        linha_norm = normalizar(linha)

        if (
            "produtos certificados:" in linha_norm
            or "produtos que eram certificados:" in linha_norm
        ):
            inicio = i + 1
            break

    if inicio is None:
        return []

    marcadores_fim = [
        "sistema de producao:",
        "sistema:",
        "flora:",
        "dados do rebanho:",
        "queijaria:",
        "norma aplicavel:",
        "resultado da auditoria",
        "nao conformidade",
        "observacoes:",
        "restricoes:",
        "diferencial:",
        "dados bancarios",
        "nota:",
        "________________________________________________",
        "================================================"
    ]

    produtos = []

    for linha in linhas[inicio:]:

        linha_limpa = linha.strip()
        linha_norm = normalizar(linha_limpa)

        if any(
            linha_norm.startswith(m)
            for m in marcadores_fim
        ):
            break

        if not linha_limpa:
            continue

        # Inclui produtos numerados e descrições complementares.
        # Alguns documentos não numeram os produtos.
        produtos.append(linha_limpa)

    return produtos


def extrair_certificado(caminho, raiz, referencia):

    texto = caminho.read_text(
        encoding="utf-8-sig",
        errors="replace"
    )

    nome = re.search(
        r"^\s*Nome\s*:\s*(.+?)\s*$",
        texto,
        flags=re.IGNORECASE | re.MULTILINE
    )

    numero = re.search(
        r"Certificado\s*N[ºo°.]?\s*:\s*([A-Z0-9-]+)",
        texto,
        flags=re.IGNORECASE
    )

    codigo = re.search(
        r"_(P\d{3})\.txt$",
        caminho.name,
        flags=re.IGNORECASE
    )

    emissao = extrair_data(
        texto,
        "Data de Emissão"
    )

    validade = extrair_data(
        texto,
        "Data de Validade"
    )

    renovacao = extrair_data(
        texto,
        "Renovação deve ser solicitada até"
    )

    texto_norm = normalizar(texto)

    marcado_vencido = (
        "*** vencida ***" in texto_norm
        or "este certificado expirou" in texto_norm
    )

    if validade is None:
        status = "validade_nao_informada"

    elif marcado_vencido or validade < referencia:
        status = "vencida"

    else:
        status = "vigente"

    alertas = []

    # Não presumir suspensão apenas porque o prazo de renovação passou.
    if (
        renovacao
        and renovacao < referencia
        and status == "vigente"
    ):
        alertas.append(
            "O prazo indicado para solicitar renovação já passou. "
            "O documento não informa suspensão da certificação. "
            "É necessário confirmar a situação com a certificadora."
        )

    if (
        status == "vencida"
        and (
            "nao podem ser comercializados" in texto_norm
            or "nao podem ser comercializadas" in texto_norm
        )
    ):
        alertas.append(
            "O documento informa que os produtos não podem ser "
            "comercializados como orgânicos até a conclusão da renovação."
        )

    return {
        "produtor_id": (
            codigo.group(1).upper()
            if codigo else None
        ),

        "produtor": (
            nome.group(1).strip()
            if nome else "Nome não identificado"
        ),

        "numero_certificado": (
            numero.group(1).strip()
            if numero else None
        ),

        "emissao": (
            emissao.isoformat()
            if emissao else None
        ),

        "validade": (
            validade.isoformat()
            if validade else None
        ),

        "status": status,

        "produtos": extrair_produtos(texto),

        "alertas": alertas,

        "fonte": str(caminho.relative_to(raiz))
    }


def carregar_certificados(
    diretorio=None,
    data_referencia=None
):
    """
    Lê todos os certificados originais.
    Não utiliza embeddings ou ChromaDB.
    """

    pasta = obter_pasta_certificados(diretorio)

    referencia = data_referencia or date.today()

    raiz = pasta.parent

    arquivos = sorted(
        pasta.glob("cert_organica_*.txt")
    )

    certificados = []

    for caminho in arquivos:

        try:

            certificado = extrair_certificado(
                caminho,
                raiz,
                referencia
            )

            certificados.append(certificado)

        except OSError as erro:

            print(
                f"[AVISO] Erro ao ler {caminho.name}: {erro}"
            )

    return certificados


def detectar_produto(pergunta):

    pergunta_norm = normalizar(pergunta)

    for produto, aliases in ALIASES_PRODUTOS.items():

        for alias in aliases:

            alias_norm = normalizar(alias)

            if re.search(
                rf"\b{re.escape(alias_norm)}\b",
                pergunta_norm
            ):
                return produto

    return None


def produto_esta_certificado(certificado, produto):

    texto_produtos = normalizar(
        " ".join(certificado["produtos"])
    )

    aliases = ALIASES_PRODUTOS.get(
        produto,
        [produto]
    )

    return any(
        re.search(
            rf"\b{re.escape(normalizar(alias))}\b",
            texto_produtos
        )
        for alias in aliases
    )


def consultar_certificacoes(
    pergunta,
    diretorio=None,
    produto=None,
    produtor=None,
    data_referencia=None
):
    """
    Consulta diretamente os documentos originais.

    Por padrão, retorna apenas certificados vigentes.

    Quando a pergunta consulta a validade de um produtor
    específico, também permite retornar certificados vencidos.
    """

    referencia = data_referencia or date.today()

    certificados = carregar_certificados(
        diretorio,
        referencia
    )

    pergunta_norm = normalizar(pergunta)

    produto_filtro = (
        produto or detectar_produto(pergunta)
    )

    codigo = re.search(
        r"\bP\d{3}\b",
        pergunta.upper()
    )

    produtor_filtro = produtor

    if produtor_filtro is None and codigo:
        produtor_filtro = codigo.group(0)

    # Tenta identificar o produtor pelo nome.
    if produtor_filtro is None:

        for cert in certificados:

            nome_norm = normalizar(cert["produtor"])

            if nome_norm in pergunta_norm:
                produtor_filtro = cert["produtor"]
                break

    consulta_individual = produtor_filtro is not None

    consulta_validade = any(
        termo in pergunta_norm
        for termo in [
            "valid", "vence", "vencid", "expir", "renov"
        ]
    )

    consulta_vencidos = any(
        termo in pergunta_norm
        for termo in [
            "vencid", "expirad", "expirou", "fora da validade",
            "perdeu a validade", "renovar", "renovacao"
        ]
    )

    consulta_todos_status = any(
        termo in pergunta_norm
        for termo in [
            "todos os certificados", "todas as certificacoes",
            "situacao das certificacoes"
        ]
    )

    resultados = []

    for cert in certificados:

        if produtor_filtro:

            filtro_norm = normalizar(
                produtor_filtro
            )

            id_match = (
                cert["produtor_id"]
                == produtor_filtro.upper()
            )

            nome_match = (
                filtro_norm in normalizar(cert["produtor"])
            )

            if not (id_match or nome_match):
                continue

        if produto_filtro:

            if not produto_esta_certificado(
                cert,
                produto_filtro
            ):
                continue

        if cert["status"] != "vigente":
            permitir_vencido = (
                (consulta_individual and consulta_validade)
                or consulta_vencidos
                or consulta_todos_status
            )
            if not permitir_vencido:
                continue

        resultados.append(cert)

    return {
        "data_referencia": referencia.isoformat(),

        "produto_consultado": produto_filtro,

        "produtor_consultado": produtor_filtro,

        "total_certificados_analisados": len(certificados),

        "total_resultados": len(resultados),

        "resultados": resultados,

        "observacao": (
            "Consulta realizada diretamente nos certificados "
            "originais. Laudos sanitários e relatórios de inspeção "
            "não são considerados certificados orgânicos."
        )
    }


def formatar_resposta_certificacoes(resultado):

    resultados = resultado["resultados"]

    if not resultados:

        produto = resultado.get("produto_consultado")

        if produto:
            return (
                f"Não encontrei certificado orgânico vigente "
                f"para '{produto}' nos documentos analisados."
            )

        return (
            "Não encontrei certificados que atendam "
            "aos critérios da consulta."
        )

    linhas = [
        "CERTIFICAÇÕES ENCONTRADAS",
        "",
        (
            "Documentos analisados: "
            f"{resultado['total_certificados_analisados']}"
        ),
        (
            "Resultados encontrados: "
            f"{len(resultados)}"
        ),
        ""
    ]

    for cert in resultados:

        validade = cert["validade"] or "Não informada"

        if validade != "Não informada":

            validade = datetime.fromisoformat(
                validade
            ).strftime("%d/%m/%Y")

        linhas.append(
            f"Produtor: {cert['produtor']}"
        )

        linhas.append(
            f"Código: {cert['produtor_id']}"
        )

        linhas.append(
            f"Situação: {cert['status']}"
        )

        linhas.append(
            f"Validade: {validade}"
        )

        if cert["numero_certificado"]:

            linhas.append(
                f"Certificado: {cert['numero_certificado']}"
            )

        linhas.append(
            f"Fonte: {cert['fonte']}"
        )

        for alerta in cert["alertas"]:

            linhas.append(
                f"ATENÇÃO: {alerta}"
            )

        linhas.append("")

    linhas.append(resultado["observacao"])

    return "\n".join(linhas)


# ==========================================
# TESTE DIRETO DO MÓDULO
# ==========================================

if __name__ == "__main__":

    perguntas = [
        "Quais produtores possuem certificação orgânica vigente?",

        "Quais produtores possuem certificação orgânica vigente para mel?",

        "A certificação de Josefa Alves de Souza ainda é válida?",

        "Qual a validade da certificação de P002?",

        "Quais produtores possuem certificação vigente para queijo?"
    ]

    for pergunta in perguntas:

        print("\n" + "=" * 65)

        print("PERGUNTA:", pergunta)

        resultado = consultar_certificacoes(
            pergunta
        )

        print(
            formatar_resposta_certificacoes(
                resultado
            )
        )
