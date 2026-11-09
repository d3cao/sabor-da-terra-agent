import os
import pandas as pd


def apurar_financeiro(
    nome_produtor: str, caminho_csv: str = None
) -> dict | str:
  """Lê o arquivo financeiro e apura vendas com base na estrutura real da Facepe."""
  try:
    if caminho_csv is None:
      script_dir = os.path.dirname(os.path.abspath(__file__))
      candidatos = [
          os.path.join(script_dir, "Facepe", "financeiro.csv"),
          os.path.join(script_dir, "..", "Facepe", "financeiro.csv"),
      ]
      for cam in candidatos:
        if os.path.exists(cam):
          caminho_csv = cam
          break

    if not caminho_csv or not os.path.exists(caminho_csv):
      return "⚠️ Ficheiro financeiro não encontrado."

    # O Pandas lê as vírgulas do CSV e cria as colunas automaticamente
    df = pd.read_csv(caminho_csv)

    # Padroniza os nomes das colunas para minúsculas
    df.columns = [c.strip().lower() for c in df.columns]

    # Verifica se a coluna de nome existe
    if "produtor_nome" not in df.columns:
      return (
          f"⚠️ Coluna 'produtor_nome' não encontrada. Colunas disponíveis:"
          f" {list(df.columns)}"
      )

    # Filtra pelo produtor (ignorando maiúsculas/minúsculas ou pequenas variações)
    df_prod = df[
        df["produtor_nome"].str.contains(nome_produtor, case=False, na=False)
    ]

    if df_prod.empty:
      return f"Nenhum registo financeiro encontrado para {nome_produtor}."

    # Calcula de forma determinística usando as colunas reais da imagem
    total_vendas = (
        df_prod["valor_total"].sum() if "valor_total" in df.columns else 0.0
    )

    # Se o status_pagamento for 'pago', conta como recebido; senão, aberto
    recebido = 0.0
    em_aberto = 0.0

    if "status_pagamento" in df.columns and "valor_total" in df.columns:
      recebido = df_prod[
          df_prod["status_pagamento"].str.lower().isin(["pago", "quitado"])
      ]["valor_total"].sum()
      em_aberto = total_vendas - recebido
    else:
      em_aberto = total_vendas

    return {
        "produtor": nome_produtor,
        "vendas_totais": float(total_vendas),
        "recebido": float(recebido),
        "em_aberto": float(em_aberto),
    }

  except Exception as e:
    return f"Erro ao processar o arquivo financeiro: {e}"