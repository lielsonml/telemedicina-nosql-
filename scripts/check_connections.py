"""Testa a conexão com os três bancos. Uso: python -m scripts.check_connections"""
import sys

from services.mongo_service import MongoService
from services.neo4j_service import Neo4jService
from services.redis_service import RedisService


def testar(nome, criar):
    try:
        servico = criar()
        ok = servico.ping()
    except Exception as erro:
        print(f"[FALHOU] {nome}: {erro}")
        return False
    print(f"[{'OK' if ok else 'FALHOU'}] {nome}")
    return ok


def main():
    resultados = [
        testar("MongoDB", MongoService),
        testar("Redis", RedisService),
        testar("Neo4j", Neo4jService),
    ]
    sys.exit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
