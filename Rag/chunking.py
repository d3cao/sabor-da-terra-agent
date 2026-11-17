
def dividir_documento(
    texto: str,
    tamanho: int = 700,
    sobreposicao: int = 100
) -> list[str]:

    palavras = texto.split()

    if sobreposicao >= tamanho:
        raise ValueError(
            "A sobreposição deve ser menor que o tamanho."
        )

    chunks = []

    inicio = 0

    while inicio < len(palavras):

        fim = inicio + tamanho

        trecho = palavras[inicio:fim]

        if trecho:
            chunks.append(" ".join(trecho))

        inicio += tamanho - sobreposicao

    return chunks
