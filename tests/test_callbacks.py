"""Testes dos callbacks do agente (P1-3). Não chamam o Gemini."""

from types import SimpleNamespace

from google.genai import errors

from sabor_da_terra import callbacks as cb

PEDIDO_OK = {
    "comprador": "Restaurante Raízes",
    "itens": [{"produto": "queijo coalho", "quantidade": 30, "unidade": "kg"}],
    "data_recebimento": "2026-10-28",
    "prazo_entrega": "2026-11-01",
}


def ferramenta(nome):
    return SimpleNamespace(name=nome)


def contexto(invocacao="inv-1", estado=None):
    return SimpleNamespace(invocation_id=invocacao, state={} if estado is None else estado)


# --- validar_argumentos -------------------------------------------------------

def test_argumentos_validos_seguem_para_a_ferramenta():
    assert cb.validar_argumentos(ferramenta("registrar_pedido"), PEDIDO_OK, None) is None


def test_data_invalida_volta_como_erro_no_contrato():
    args = {**PEDIDO_OK, "prazo_entrega": "01/11/2026"}
    r = cb.validar_argumentos(ferramenta("registrar_pedido"), args, None)
    assert r["status"] == "erro"
    assert set(r) == {"status", "dados", "fontes", "mensagem"}
    assert "prazo_entrega" in r["mensagem"]


def test_data_com_hora_e_rejeitada():
    args = {**PEDIDO_OK, "data_recebimento": "2026-10-28T09:15:00"}
    assert cb.validar("registrar_pedido", args)


def test_data_vazia_opcional_e_aceita():
    assert cb.validar("registrar_pedido", {**PEDIDO_OK, "prazo_entrega": ""}) == []


def test_obrigatorio_vazio():
    problemas = cb.validar("consultar_lote", {"codigo_lote": "  "})
    assert any("codigo_lote" in p for p in problemas)


def test_quantidade_negativa_ou_texto():
    for qtd in (-5, 0, "trinta"):
        args = {**PEDIDO_OK, "itens": [{"produto": "mel", "quantidade": qtd}]}
        assert cb.validar("registrar_pedido", args), qtd


def test_quantidade_ausente_e_permitida():
    args = {**PEDIDO_OK, "itens": [{"produto": "mel", "unidade": "kg"}]}
    assert cb.validar("registrar_pedido", args) == []


def test_registrar_sem_itens_e_erro_mas_atualizar_sem_itens_nao():
    assert cb.validar("registrar_pedido", {**PEDIDO_OK, "itens": []})
    assert cb.validar("atualizar_pedido", {"prazo_entrega": "2026-11-05"}) == []


def test_valor_fora_da_lista():
    assert cb.validar("gerar_comunicacao", {"tipo": "email", "produtor": "Maria"})
    assert cb.validar("gerar_comunicacao", {"tipo": "resumo", "produtor": "Maria"}) == []
    assert cb.validar("buscar_documentos", {"pergunta": "x", "tipo_documento": ""}) == []


def test_ferramenta_sem_regras_passa():
    assert cb.validar("avaliar_pedido", {}) == []


# --- limitar_iteracoes --------------------------------------------------------

def test_limite_de_iteracoes():
    ctx = contexto()
    for _ in range(cb.LIMITE_ITERACOES):
        assert cb.limitar_iteracoes(ctx, None) is None
    resposta = cb.limitar_iteracoes(ctx, None)
    assert resposta is not None
    assert "limite" in resposta.content.parts[0].text


def test_contador_zera_a_cada_mensagem_do_usuario():
    estado = {}
    for _ in range(cb.LIMITE_ITERACOES):
        cb.limitar_iteracoes(contexto("inv-1", estado), None)
    assert cb.limitar_iteracoes(contexto("inv-2", estado), None) is None


# --- tratar_erro_modelo -------------------------------------------------------

def erro_api(codigo):
    return errors.APIError(codigo, {"error": {"code": codigo, "message": "x", "status": "X"}})


def test_erro_503_vira_mensagem():
    req = SimpleNamespace(model="gemini-teste")
    r = cb.tratar_erro_modelo(contexto(), req, erro_api(503))
    assert "sobrecarregado" in r.content.parts[0].text


def test_erro_404_vira_mensagem():
    req = SimpleNamespace(model="gemini-teste")
    r = cb.tratar_erro_modelo(contexto(), req, erro_api(404))
    assert "GEMINI_MODEL" in r.content.parts[0].text


def test_outros_erros_propagam():
    req = SimpleNamespace(model="gemini-teste")
    assert cb.tratar_erro_modelo(contexto(), req, ValueError("bug")) is None
    assert cb.tratar_erro_modelo(contexto(), req, erro_api(400)) is None
