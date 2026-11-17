
import os
from pathlib import Path

from pypdf import PdfReader


# ==========================================
# CONFIGURAÇÕES
# ==========================================

PASTAS_DOCUMENTAIS = [
    "certificacoes",
    "contratos",
    "fichas_tecnicas",
]

EXTENSOES_SUPORTADAS = {
    ".txt",
    ".md",
    ".pdf",
}


def localizar_facepe() -> Path:

    configurado = os.getenv("SABOR_DATA_DIR")

    if configurado:
        pasta = Path(configurado).expanduser()

        if not pasta.exists():
            raise FileNotFoundError(
                f"SABOR_DATA_DIR não existe: {pasta}"
            )

        return pasta.resolve()

    raiz_projeto = Path(__file__).resolve().parent.parent

    candidatos = [
        raiz_projeto / "Facepe",
        raiz_projeto / "Rag" / "Facepe",
    ]

    for pasta in candidatos:

        if pasta.exists():
            return pasta.resolve()

    raise FileNotFoundError(
        "Pasta Facepe não encontrada. "
        "Verifique a estrutura do projeto ou configure "
        "SABOR_DATA_DIR no arquivo .env."
    )


# ==========================================
# EXTRAÇÃO DE TEXTO
# ==========================================

def extrair_txt(caminho: Path) -> str:

    try:
        return caminho.read_text(
            encoding="utf-8-sig"
        )

    except UnicodeDecodeError:

        return caminho.read_text(
            encoding="latin-1"
        )


def extrair_pdf(caminho: Path) -> list[dict]:

    reader = PdfReader(str(caminho))

    paginas = []

    for numero, pagina in enumerate(reader.pages, start=1):

        texto = pagina.extract_text() or ""

        if texto.strip():

            paginas.append({
                "pagina": numero,
                "texto": texto.strip()
            })

    return paginas


# ==========================================
# CARREGAMENTO DE UM DOCUMENTO
# ==========================================

def carregar_arquivo(
    caminho: Path,
    raiz: Path,
    categoria: str
) -> list[dict]:

    extensao = caminho.suffix.lower()

    try:

        if extensao == ".pdf":

            paginas = extrair_pdf(caminho)

        elif extensao in {".txt", ".md"}:

            texto = extrair_txt(caminho)

            paginas = [{
                "pagina": None,
                "texto": texto
            }]

        else:

            return []

    except Exception as erro:

        print(
            f"[ERRO] Não foi possível ler "
            f"{caminho.name}: {erro}"
        )

        return []

    documentos = []

    for pagina in paginas:

        texto = pagina["texto"].strip()

        if not texto:
            continue

        documentos.append({

            "texto": texto,

            "arquivo": caminho.name,

            "caminho": str(
                caminho.relative_to(raiz)
            ).replace("\\", "/"),

            "categoria": categoria,

            "pagina": pagina["pagina"],

            "extensao": extensao

        })

    return documentos


# ==========================================
# CARREGAMENTO DO ACERVO COMPLETO
# ==========================================

def carregar_documentos() -> list[dict]:

    raiz = localizar_facepe()

    documentos = []

    print("\n========== CARREGAMENTO FACEPE ==========\n")

    for categoria in PASTAS_DOCUMENTAIS:

        pasta = raiz / categoria

        if not pasta.exists():

            print(
                f"[AVISO] Pasta não encontrada: {categoria}"
            )

            continue

        arquivos = sorted(
            arquivo
            for arquivo in pasta.rglob("*")
            if arquivo.is_file()
            and arquivo.suffix.lower() in EXTENSOES_SUPORTADAS
        )

        print(
            f"[PASTA] {categoria}: {len(arquivos)} arquivos"
        )

        for caminho in arquivos:

            paginas = carregar_arquivo(
                caminho,
                raiz,
                categoria
            )

            documentos.extend(paginas)

            print(
                f"  [OK] {caminho.name}: "
                f"{len(paginas)} unidade(s) de texto"
            )

    print("\n=========================================")

    print(
        f"Total de unidades documentais: {len(documentos)}"
    )

    return documentos


if __name__ == "__main__":

    documentos = carregar_documentos()

    print("\nPRIMEIRO DOCUMENTO:")

    if documentos:
        print(documentos[0])
    else:
        print("Nenhum documento foi carregado.")
