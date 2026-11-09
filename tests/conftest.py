"""Fixtures compartilhadas. Cada fixture pula os testes se o banco não estiver acessível."""
import pytest

import config
from services.mongo_service import MongoService
from services.neo4j_service import Neo4jService
from services.redis_service import RedisService


@pytest.fixture(scope="session")
def mongo():
    nome_teste = f"{config.MONGO_DB}_teste"
    svc = MongoService(db_name=nome_teste)
    if not svc.ping():
        pytest.skip("MongoDB indisponível")
    yield svc
    svc.client.drop_database(nome_teste)


@pytest.fixture(scope="session")
def redis_svc():
    svc = RedisService()
    if not svc.ping():
        pytest.skip("Redis indisponível")
    yield svc


@pytest.fixture(scope="session")
def neo():
    svc = Neo4jService()
    if not svc.ping():
        pytest.skip("Neo4j indisponível")
    yield svc
    svc._escrever("MATCH (p:Pessoa) WHERE p.id STARTS WITH 't_' DETACH DELETE p")
    svc._escrever("MATCH (h:Habilidade) WHERE h.nome STARTS WITH 'T_' DETACH DELETE h")
    svc._escrever("MATCH (e:Empresa) WHERE e.nome STARTS WITH 'T_' DETACH DELETE e")
    svc.close()
