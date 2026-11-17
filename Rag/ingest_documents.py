
import hashlib
import sys
from pathlib import Path

# Permite executar o arquivo diretamente pela raiz do projeto.
RAIZ_PROJETO = Path(__file__).resolve().parent.parent

if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

from Rag.document_loader import carregar_documentos
from Rag.embedding_service import embedding_documento
from Rag.chunking import dividir_documento

from Rag.vector_store import (
    inserir_documentos,
    collection
)


# ==========================================
# CONFIGURAÇÕES
# ==========================================

TAMANHO_CHUNK = 700
SOBREPOSICAO = 100

# Quantos chunks processar antes de continuar.
LOTE_PROCESSAMENTO = 20


# ==========================================
# IDENTIFICADOR ÚNICO
# ==========================================

def gerar_id(
    caminho: str,
    pagina,
    indice: int,
    texto: str
) -> str:

    identificador = (
        f"{caminho}|{pagina}|{indice}|{texto}"
    )

    return hashlib.sha256(
        identificador.encode("utf-8")
    ).hexdigest()


# ==========================================
# PREPARAÇÃO DOS CHUNKS
# ==========================================

def preparar_chunks(documentos):

    chunks = []

    for documento in documentos:

        trechos = dividir_documento(
            documento["texto"],
            tamanho=TAMANHO_CHUNK,
            sobreposicao=SOBREPOSICAO
        )

        for indice, trecho in enumerate(trechos):

            if not trecho.strip():
                continue

            chunks.append({

                "id": gerar_id(
                    documento["caminho"],
                    documento["pagina"],
                    indice,
                    trecho
                ),

                "texto": trecho,

                "metadata": {

                    "arquivo": documento["arquivo"],

                    "caminho": documento["caminho"],

                    "categoria": documento["categoria"],

                    "pagina": (
                        documento["pagina"]
                        if documento["pagina"] is not None
                        else 0
                    ),

                    "indice_chunk": indice,

                    "extensao": documento["extensao"]

                }
            })

    return chunks


# ==========================================
# INDEXAÇÃO NO CHROMADB
# ==========================================

def indexar_documentos():

    print("\n========== INÍCIO DA INDEXAÇÃO ==========\n")

    documentos = carregar_documentos()

    if not documentos:

        print("[AVISO] Nenhum documento encontrado.")

        return

    chunks = preparar_chunks(documentos)

    print(
        f"\nDocumentos/unidades: {len(documentos)}"
    )

    print(
        f"Chunks gerados: {len(chunks)}"
    )

    if not chunks:
        print("[AVISO] Nenhum chunk foi gerado.")
        return

    # Identifica os arquivos presentes nesta ingestão.
    arquivos = {
        documento["caminho"]
        for documento in documentos
    }

    # Remove versões anteriores desses mesmos arquivos.
    # Assim, documentos atualizados não deixam chunks antigos.
    for caminho in arquivos:

        collection.delete(
            where={
                "caminho": caminho
            }
        )

    # Geração e armazenamento em lotes.
    total_indexado = 0

    for inicio in range(
        0,
        len(chunks),
        LOTE_PROCESSAMENTO
    ):

        lote = chunks[
            inicio:inicio + LOTE_PROCESSAMENTO
        ]

        print(
            f"\nProcessando lote "
            f"{inicio // LOTE_PROCESSAMENTO + 1}..."
        )

        documentos_banco = []

        for item in lote:

            vetor = embedding_documento(
                item["texto"],
                titulo=item["metadata"]["arquivo"]
            )

            documentos_banco.append({

                "id": item["id"],

                "texto": item["texto"],

                "embedding": vetor,

                "metadata": item["metadata"]

            })

        quantidade = inserir_documentos(
            documentos_banco
        )

        total_indexado += quantidade

        print(
            f"[OK] {quantidade} chunks armazenados."
        )

    print("\n========== INDEXAÇÃO CONCLUÍDA ==========")

    print(
        f"Total de chunks indexados: {total_indexado}"
    )

    print(
        f"Total registrado no ChromaDB: "
        f"{collection.count()}"
    )


if __name__ == "__main__":

    try:

        indexar_documentos()

    except Exception as erro:

        print("\n[ERRO NA INDEXAÇÃO]")

        print(str(erro))

        raise
