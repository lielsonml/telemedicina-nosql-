"""Integração dos três bancos: conectar no Neo4j + evento no MongoDB + notificação no Redis."""
import uuid


def test_fluxo_conexao_nos_tres_bancos(mongo, redis_svc, neo):
    a, b = f"t_{uuid.uuid4().hex[:6]}", f"t_{uuid.uuid4().hex[:6]}"
    neo.upsert_pessoa(a, "Teste A", "Médico")
    neo.upsert_pessoa(b, "Teste B", "Médico")

    assert neo.conectar(a, b) is True
    mongo.registrar_evento("conexao", a, {"destino": b})
    total = redis_svc.notificar(b, "Teste A conectou-se com você.")

    assert neo.caminho_mais_curto(a, b)["graus"] == 1
    assert mongo.listar_eventos(1)[0]["detalhes"]["destino"] == b
    assert total == 1 and redis_svc.contar_nao_lidas(b) == 1

    redis_svc.marcar_lidas(b)
    redis_svc.r.delete(f"notif:lista:{b}")
