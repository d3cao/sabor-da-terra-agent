
import ollama
import os

# ==========================================
# CONFIGURAÇÕES
# ==========================================

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "bge-m3"
)

# ==========================================
# GERAÇÃO DE EMBEDDINGS
# ==========================================

def gerar_embedding(texto: str) -> list[float]:

    if not texto or not texto.strip():
        raise ValueError("O texto não pode estar vazio.")

    resposta = ollama.embed(
        model=MODEL_NAME,
        input=texto
    )

    # Compatibilidade com diferentes versões
    # do cliente Python do Ollama.

    if isinstance(resposta, dict):
        vetores = resposta["embeddings"]
    else:
        vetores = resposta.embeddings

    vetor = vetores[0]

    if len(vetor) != 1024:
        raise ValueError(
            f"Dimensão inesperada: {len(vetor)}"
        )

    return list(vetor)


# ==========================================
# EMBEDDING DE DOCUMENTOS
# ==========================================

def embedding_documento(
    texto: str,
    titulo: str = None
) -> list[float]:

    conteudo = texto

    if titulo:
        conteudo = f"Documento: {titulo}\n\n{texto}"

    return gerar_embedding(conteudo)


# ==========================================
# EMBEDDING DE CONSULTAS
# ==========================================

def embedding_consulta(
    pergunta: str
) -> list[float]:

    return gerar_embedding(pergunta)
