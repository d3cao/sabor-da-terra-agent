
import chromadb
from pathlib import Path

CAMINHO_BANCO = Path("data/chroma")

CAMINHO_BANCO.mkdir(
    parents=True,
    exist_ok=True
)

client = chromadb.PersistentClient(
    path=str(CAMINHO_BANCO)
)

collection = client.get_or_create_collection(
    name="sabor_da_terra",
    metadata={
        "hnsw:space": "cosine"
    }
)


def inserir_documentos(documentos):

    if not documentos:
        return 0

    ids = [
        documento["id"]
        for documento in documentos
    ]

    textos = [
        documento["texto"]
        for documento in documentos
    ]

    embeddings = [
        documento["embedding"]
        for documento in documentos
    ]

    metadados = [
        documento["metadata"]
        for documento in documentos
    ]

    collection.upsert(
        ids=ids,
        documents=textos,
        embeddings=embeddings,
        metadatas=metadados
    )

    return len(ids)


def buscar_documentos(
    embedding_consulta,
    limite=5,
    categoria=None
):

    filtro = (
        {"categoria": categoria}
        if categoria
        else None
    )

    resultado = collection.query(
        query_embeddings=[embedding_consulta],
        n_results=limite,
        where=filtro,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    encontrados = []

    for i, texto in enumerate(
        resultado["documents"][0]
    ):

        encontrados.append({

            "texto": texto,

            "metadata": resultado["metadatas"][0][i],

            "distancia": resultado["distances"][0][i]
        })

    return encontrados
