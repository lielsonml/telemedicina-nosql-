"""Testes do Neo4j: nós, relacionamentos e consultas Cypher (ids de teste começam com t_)."""


def _montar_rede(neo):
    for pid in ("t_a", "t_b", "t_c", "t_d"):
        neo.upsert_pessoa(pid, f"Pessoa {pid}", "Médico")
    neo.associar_habilidade("t_c", "T_Habilidade", 5)
    neo.associar_habilidade("t_d", "T_Habilidade", 3)
    neo.associar_empresa("t_a", "T_Empresa", "Cargo")
    neo.conectar("t_a", "t_b")
    neo.conectar("t_b", "t_c")


def test_ping(neo):
    assert neo.ping() is True


def test_conexao_duplicada_e_caminho(neo):
    _montar_rede(neo)
    assert neo.conectar("t_a", "t_b") is False
    assert neo.conectar("t_b", "t_a") is False
    caminho = neo.caminho_mais_curto("t_a", "t_c")
    assert caminho["graus"] == 2 and caminho["ids"] == ["t_a", "t_b", "t_c"]
    assert neo.caminho_mais_curto("t_a", "t_a") is None


def test_mentores_e_sugestoes(neo):
    _montar_rede(neo)
    mentores = neo.recomendar_mentores("t_a", "T_Habilidade")
    assert [m["id"] for m in mentores] == ["t_c"]
    assert mentores[0]["graus"] == 2
    sugestoes = neo.sugerir_conexoes("t_a")
    assert [s["id"] for s in sugestoes] == ["t_c"]


def test_desconectar(neo):
    _montar_rede(neo)
    assert neo.desconectar("t_b", "t_c") is True
    assert neo.caminho_mais_curto("t_a", "t_c") is None
    neo.conectar("t_b", "t_c")
