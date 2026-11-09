import os


def buscar_acervo_local(termo_busca: str, pasta_raiz: str = None):
  """Varre as pastas de certificados, contratos e fichas técnicas procurando o termo."""
  if pasta_raiz is None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pasta_raiz = os.path.join(script_dir, "Facepe")

    if not os.path.exists(pasta_raiz):
      pasta_raiz = os.path.join(script_dir, "..", "Facepe")

  pastas_alvo = ["certificacoes", "contratos", "fichas_tecnicas"]
  resultados = []

  for pasta in pastas_alvo:
    caminho_pasta = os.path.join(pasta_raiz, pasta)
    if not os.path.exists(caminho_pasta):
      continue

    for arquivo in os.listdir(caminho_pasta):
      caminho_arquivo = os.path.join(caminho_pasta, arquivo)

      if os.path.isfile(caminho_arquivo):
        try:
          with open(caminho_arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()
            if termo_busca.lower() in conteudo.lower():
              resultados.append({
                  "arquivo": f"{pasta}/{arquivo}",
                  "trecho": conteudo[:300] + "...",
              })
        except Exception:
          pass

  if not resultados:
    return (
        "Não encontrei essa informação nos documentos oficiais da cooperativa."
    )

  return resultados