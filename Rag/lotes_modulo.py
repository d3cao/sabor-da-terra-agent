
import os
import re
import unicodedata
from datetime import date
from pathlib import Path

import pandas as pd


# =====================================================
# CONFIGURAÇÕES
# =====================================================

def obter_pasta_dados() -> Path:
    """
    Localiza a pasta Facepe.
    Permite configurar outro caminho usando SABOR_DATA_DIR.
    """

    configurado = os.getenv("SABOR_DATA_DIR")

    if configurado:
        pasta = Path(configurado).expanduser()

        if pasta.exists():
            return pasta

    raiz = Path(__file__).resolve().parent.parent

    candidatos = [
        raiz / "Facepe",
        Path.cwd() / "Facepe",
    ]

    for pasta in candidatos:
        if (pasta / "lotes.csv").exists():
            return pasta

    return raiz / "Facepe"


ARQUIVO_LOTES = obter_pasta_dados() / "lotes.csv"


# =====================================================
# LEITURA DO CSV
# =====================================================

def carregar_lotes() -> pd.DataFrame:
    """
    Carrega os registros de lotes.
    """

    if not ARQUIVO_LOTES.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO_LOTES}"
        )

    try:
        df = pd.read_csv(
            ARQUIVO_LOTES,
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:
        df = pd.read_csv(
            ARQUIVO_LOTES,
            encoding="latin-1"
        )

    df.columns = [
        str(coluna).strip().lower()
        for coluna in df.columns
    ]

    if "lote_id" not in df.columns:
        raise ValueError(
            "A coluna lote_id não existe em lotes.csv."
        )

    return df


# =====================================================
# NORMALIZAÇÃO
# =====================================================

def normalizar_texto(texto) -> str:

    texto = str(texto or "").strip().casefold()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    return re.sub(r"\s+", " ", texto)


def normalizar_id(lote_id: str) -> str:

    return re.sub(
        r"\s+",
        "",
        str(lote_id or "").strip()
    ).upper()


def valor_seguro(valor):
    """
    Converte valores do Pandas em valores compatíveis
    com JSON.
    """

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(valor, "item"):
        return valor.item()

    return valor


# =====================================================
# PREPARAÇÃO DOS REGISTROS
# =====================================================

def preparar_registro(linha: dict, data_referencia=None) -> dict:
    """
    Prepara os dados do lote para resposta.

    Não retorna CPF, telefone, e-mail ou dados bancários.
    """

    campos_proibidos = {
        "cpf",
        "produtor_cpf",
        "telefone",
        "email",
        "banco",
        "agencia",
        "conta_corrente",
        "chave_pix",
    }

    registro = {}

    for chave, valor in linha.items():

        if chave.casefold() in campos_proibidos:
            continue

        registro[chave] = valor_seguro(valor)

    # Verificação da validade do lote.

    validade = registro.get("validade")

    if data_referencia is None:
        referencia = date.today()
    else:
        referencia = pd.to_datetime(
            data_referencia,
            errors="coerce"
        )

        if pd.isna(referencia):
            raise ValueError(
                "Data de referência inválida."
            )

        referencia = referencia.date()

    validade_convertida = pd.to_datetime(
        validade,
        errors="coerce"
    )

    if pd.isna(validade_convertida):

        registro["status_validade"] = "indeterminada"

    else:

        data_validade = validade_convertida.date()

        registro["validade"] = data_validade.isoformat()

        if data_validade < referencia:
            registro["status_validade"] = "vencido"
        else:
            registro["status_validade"] = "vigente"

    # Normalização da inspeção.

    inspecao = normalizar_texto(
        registro.get("inspecao_visual")
    )

    if inspecao == "aprovado":
        registro["status_inspecao"] = "aprovada"

    elif inspecao in ("reprovado", "reprovada"):
        registro["status_inspecao"] = "reprovada"

    elif inspecao:
        registro["status_inspecao"] = "informada"

    else:
        registro["status_inspecao"] = "nao_informada"

    return registro


# =====================================================
# 1. CONSULTAR LOTE PELO ID EXATO
# =====================================================

def consultar_lote(
    lote_id: str,
    data_referencia=None
) -> dict:
    """
    Consulta um lote utilizando seu identificador exato.

    Não substitui lotes inexistentes por registros semelhantes.
    """

    if not lote_id or not str(lote_id).strip():

        return {
            "status": "erro",
            "mensagem": "Informe o identificador do lote.",
            "lote": None
        }

    try:
        df = carregar_lotes()

    except Exception as erro:

        return {
            "status": "erro",
            "mensagem": str(erro),
            "lote": None
        }

    procurado = normalizar_id(lote_id)

    identificadores = (
        df["lote_id"]
        .fillna("")
        .astype(str)
        .apply(normalizar_id)
    )

    resultado = df[
        identificadores == procurado
    ]

    if resultado.empty:

        return {
            "status": "nao_encontrado",
            "lote_solicitado": procurado,
            "mensagem": (
                f"O lote {procurado} não foi encontrado "
                "em lotes.csv. Não serão utilizados "
                "dados de outros lotes."
            ),
            "lote": None,
            "fonte": "lotes.csv"
        }

    # Se houver IDs duplicados, não escolher um registro
    # arbitrariamente.

    if len(resultado) > 1:

        return {
            "status": "erro",
            "lote_solicitado": procurado,
            "mensagem": (
                "Foram encontrados identificadores duplicados "
                "para este lote. É necessário revisar o CSV."
            ),
            "quantidade_registros": len(resultado),
            "lote": None
        }

    linha = resultado.iloc[0].to_dict()

    lote = preparar_registro(
        linha,
        data_referencia
    )

    return {
        "status": "encontrado",
        "lote": lote,
        "fonte": "lotes.csv"
    }


# =====================================================
# 2. CONSULTAR LOTES POR PRODUTOR
# =====================================================

def consultar_lotes_por_produtor(
    produtor_id: str,
    data_referencia=None
) -> dict:
    """
    Retorna todos os lotes vinculados a um produtor.
    """

    try:
        df = carregar_lotes()

    except Exception as erro:

        return {
            "status": "erro",
            "mensagem": str(erro),
            "lotes": []
        }

    if "produtor_id" not in df.columns:

        return {
            "status": "erro",
            "mensagem": (
                "A coluna produtor_id não existe em lotes.csv."
            ),
            "lotes": []
        }

    procurado = normalizar_texto(produtor_id)

    resultado = df[
        df["produtor_id"]
        .fillna("")
        .astype(str)
        .apply(normalizar_texto)
        == procurado
    ]

    if resultado.empty:

        return {
            "status": "nao_encontrado",
            "produtor_id": produtor_id,
            "mensagem": (
                f"Nenhum lote encontrado para o produtor "
                f"{produtor_id}."
            ),
            "lotes": []
        }

    lotes = [
        preparar_registro(
            linha.to_dict(),
            data_referencia
        )
        for _, linha in resultado.iterrows()
    ]

    return {
        "status": "sucesso",
        "produtor_id": produtor_id,
        "quantidade": len(lotes),
        "lotes": lotes,
        "fonte": "lotes.csv"
    }


# =====================================================
# 3. CONSULTAR LOTES POR PRODUTO
# =====================================================

def consultar_lotes_por_produto(
    produto: str,
    data_referencia=None
) -> dict:
    """
    Pesquisa lotes pelo nome do produto.
    """

    try:
        df = carregar_lotes()

    except Exception as erro:

        return {
            "status": "erro",
            "mensagem": str(erro),
            "lotes": []
        }

    if "produto" not in df.columns:

        return {
            "status": "erro",
            "mensagem": (
                "A coluna produto não existe em lotes.csv."
            ),
            "lotes": []
        }

    procurado = normalizar_texto(produto)

    resultado = df[
        df["produto"]
        .fillna("")
        .astype(str)
        .apply(normalizar_texto)
        .str.contains(
            re.escape(procurado),
            na=False
        )
    ]

    if resultado.empty:

        return {
            "status": "nao_encontrado",
            "produto": produto,
            "mensagem": (
                f"Nenhum lote encontrado para o produto {produto}."
            ),
            "lotes": []
        }

    lotes = [
        preparar_registro(
            linha.to_dict(),
            data_referencia
        )
        for _, linha in resultado.iterrows()
    ]

    return {
        "status": "sucesso",
        "produto": produto,
        "quantidade": len(lotes),
        "lotes": lotes,
        "fonte": "lotes.csv"
    }


# =====================================================
# 4. LISTAR LOTES
# =====================================================

def listar_lotes(
    status_validade=None,
    data_referencia=None
) -> dict:
    """
    Lista os lotes cadastrados.

    status_validade:
        - vigente
        - vencido
        - indeterminada
        - None: todos
    """

    try:
        df = carregar_lotes()

    except Exception as erro:

        return {
            "status": "erro",
            "mensagem": str(erro),
            "lotes": []
        }

    lotes = []

    for _, linha in df.iterrows():

        lote = preparar_registro(
            linha.to_dict(),
            data_referencia
        )

        if status_validade:

            if lote["status_validade"] != normalizar_texto(
                status_validade
            ):
                continue

        lotes.append(lote)

    return {
        "status": "sucesso",
        "quantidade": len(lotes),
        "lotes": lotes,
        "fonte": "lotes.csv"
    }


# =====================================================
# 5. RESUMO DE RASTREABILIDADE
# =====================================================

def consultar_rastreabilidade(lote_id: str) -> dict:
    """
    Retorna os principais dados de rastreabilidade
    de um lote específico.
    """

    resultado = consultar_lote(lote_id)

    if resultado["status"] != "encontrado":
        return resultado

    lote = resultado["lote"]

    return {
        "status": "sucesso",
        "lote_id": lote.get("lote_id"),
        "produto": lote.get("produto"),
        "produtor_id": lote.get("produtor_id"),
        "produtor": lote.get("produtor_nome"),
        "data_colheita": lote.get("data_colheita"),
        "data_entrega": lote.get("data_entrega"),
        "quantidade_kg": lote.get("quantidade_kg"),
        "comprador": lote.get("comprador"),
        "pedido_id": lote.get("pedido_id"),
        "validade": lote.get("validade"),
        "status_validade": lote.get("status_validade"),
        "temperatura_transporte_c": lote.get(
            "temperatura_transporte_c"
        ),
        "inspecao_visual": lote.get("inspecao_visual"),
        "status_inspecao": lote.get("status_inspecao"),
        "observacao": lote.get("observacao"),
        "fonte": resultado["fonte"]
    }
