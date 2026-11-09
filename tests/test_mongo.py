"""Testes do MongoDB: conexão, CRUD, índice único e eventos."""
import pytest
from pymongo.errors import DuplicateKeyError


def _usuario(uid, email):
    return {"_id": uid, "nome": "Teste", "email": email, "papel": "Médico",
            "titulo": "Titulo", "bio": "Bio", "experiencias": [], "formacao": [], "certificacoes": []}


def test_ping(mongo):
    assert mongo.ping() is True


def test_crud_post(mongo):
    post_id = mongo.criar_post("t_u1", "Teste", "Primeiro post de teste", ["Teleconsulta"])
    posts = mongo.listar_posts(autor_id="t_u1")
    assert len(posts) == 1 and posts[0]["tags"] == ["teleconsulta"]
    assert mongo.curtir_post(post_id) == 1
    assert mongo.excluir_post(post_id, "outro") is False
    assert mongo.excluir_post(post_id, "t_u1") is True
    assert mongo.listar_posts(autor_id="t_u1") == []


def test_post_vazio_e_rejeitado(mongo):
    with pytest.raises(ValueError):
        mongo.criar_post("t_u1", "Teste", "   ")


def test_perfil_atualizacao(mongo):
    mongo.criar_indices()
    mongo.salvar_usuario(_usuario("t_u2", "t_u2@exemplo.fict"))
    assert mongo.atualizar_perfil("t_u2", {"bio": "Nova bio", "campo_proibido": "x"}) is True
    assert mongo.adicionar_experiencia("t_u2", {"instituicao": "X", "cargo": "Y", "inicio": 2020, "fim": None}) is True
    doc = mongo.obter_usuario("t_u2")
    assert doc["bio"] == "Nova bio" and len(doc["experiencias"]) == 1
    assert "campo_proibido" not in doc


def test_email_unico(mongo):
    mongo.criar_indices()
    mongo.salvar_usuario(_usuario("t_u3", "repetido@exemplo.fict"))
    with pytest.raises(DuplicateKeyError):
        mongo.usuarios.insert_one(_usuario("t_u4", "repetido@exemplo.fict"))


def test_eventos(mongo):
    mongo.registrar_evento("teste", "t_u1", {"k": "v"})
    assert mongo.listar_eventos(1)[0]["tipo"] == "teste"
