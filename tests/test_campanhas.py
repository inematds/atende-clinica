"""Seção 9: campanha só com consentimento e trava por conselho."""
import pytest

from conftest import Servidor, com_conselho

CASOS = [
    # conselho, texto, violações esperadas (None = permitido)
    ("cfo", "Clareamento por R$ 300 em 10x sem juros", {"preco", "parcelamento"}),
    ("cfo", "Sorteio de um kit de escovas", {"sorteio_brinde"}),
    ("cfo", "Veja o antes e depois dos nossos pacientes", {"antes_depois"}),
    ("cfo", "Avaliação grátis este mês", {"gratuito"}),
    ("cfo", "Resultado garantido no seu sorriso", {"promessa_resultado"}),
    ("cfo", "O melhor dentista do Batel", {"melhor_profissional"}),
    ("cfo", "Semana da saúde bucal: agende sua revisão.", None),
    ("cfm", "Consulta por R$ 300 nesta semana", None),
    ("cfm", "Participe do sorteio de um check-up", {"sorteio_brinde"}),
    ("cfm", "Consórcio para sua cirurgia", {"consorcio"}),
    ("cfm", "Melhor médico da cidade, 100% de satisfação", {"melhor_profissional", "promessa_resultado"}),
    ("coffito", "Promoção de pilates clínico", {"promocao"}),
    ("coffito", "Sessão por apenas 80 reais", {"preco"}),
    ("coffito", "Novas turmas de pilates clínico às terças", None),
    ("estetica", "Limpeza de pele por R$ 120 com desconto", None),
    ("estetica", "Resultado garantido em 1 sessão", {"promessa_resultado"}),
]


@pytest.mark.parametrize("conselho,texto,esperado", CASOS, ids=[f"{c[0]}-{i}" for i, c in enumerate(CASOS)])
def test_trava_por_conselho(dados, conselho, texto, esperado):
    com_conselho(dados, conselho)
    s = Servidor(dados)
    try:
        api = s.subir()
        api.paciente("Maria", "41999990001", marketing=True)
        st, r = api.post("/api/campanhas", {"texto": texto})
        if esperado is None:
            assert st == 200 and r["enviadas"] == 1, (st, r)
        else:
            assert st == 422, (st, r)
            assert set(r["violacoes"]) == esperado
            assert api.saida("campanha") == []
    finally:
        s.parar()


def test_publico_so_com_consentimento_e_sem_parar(api):
    api.paciente("Com", "41999990001", marketing=True)
    api.paciente("Sem", "41999990002", marketing=False)
    api.paciente("Parou", "41999990003", marketing=True)
    api.msg("41999990003", "parar")
    st, r = api.post("/api/campanhas", {"texto": "Semana da saúde bucal: agende sua revisão."})
    assert st == 200 and r["enviadas"] == 1
    assert [m["telefone"] for m in api.saida("campanha")] == ["+5541999990001"]
