"""Testes do Redis: conexão, sessão, expiração por TTL, notificações e cache."""
import time
import uuid


def _id():
    return f"t_{uuid.uuid4().hex[:8]}"


def test_ping(redis_svc):
    assert redis_svc.ping() is True


def test_sessao_com_ttl(redis_svc):
    uid = _id()
    token = redis_svc.criar_sessao(uid, "Teste", ttl=60)
    assert 0 < redis_svc.ttl_sessao(token) <= 60
    assert redis_svc.obter_sessao(token, ttl=90)["usuario_id"] == uid
    assert 60 < redis_svc.ttl_sessao(token) <= 90
    assert redis_svc.encerrar_sessao(token) is True
    assert redis_svc.obter_sessao(token) is None


def test_presenca_expira(redis_svc):
    uid = _id()
    redis_svc.definir_presenca(uid, "online", ttl=1)
    assert redis_svc.obter_presenca(uid) == "online"
    time.sleep(1.6)
    assert redis_svc.obter_presenca(uid) == "offline"


def test_notificacoes(redis_svc):
    uid = _id()
    assert redis_svc.notificar(uid, "oi") == 1
    assert redis_svc.notificar(uid, "oi 2") == 2
    assert redis_svc.contar_nao_lidas(uid) == 2
    assert redis_svc.listar_notificacoes(uid)[0]["mensagem"] == "oi 2"
    redis_svc.marcar_lidas(uid)
    assert redis_svc.contar_nao_lidas(uid) == 0
    redis_svc.r.delete(f"notif:lista:{uid}")


def test_cache_e_invalidacao(redis_svc):
    chave = f"teste:{_id()}"
    assert redis_svc.cache_get(chave) is None
    redis_svc.cache_set(chave, {"a": [1, 2]}, ttl=30)
    assert redis_svc.cache_get(chave) == {"a": [1, 2]}
    assert redis_svc.cache_invalidar("teste:") >= 1
    assert redis_svc.cache_get(chave) is None
