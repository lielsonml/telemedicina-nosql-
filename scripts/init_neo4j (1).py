"""Cria constraints e carrega o grafo (Pessoa, Habilidade, Empresa) no Neo4j.

Uso: python -m scripts.init_neo4j [--reset]
"""
import sys

from data.seed_data import CONEXOES, PESSOAS
from services.neo4j_service import Neo4jService


def main():
    reset = "--reset" in sys.argv
    neo = Neo4jService()
    try:
        if not neo.ping():
            print("ERRO: não foi possível conectar ao Neo4j. Verifique NEO4J_URI/USERNAME/PASSWORD no .env.")
            sys.exit(1)

        neo.criar_constraints()
        if reset:
            neo.limpar_grafo()
            print("Grafo limpo.")

        for p in PESSOAS:
            neo.upsert_pessoa(p["id"], p["nome"], p["papel"])
            neo.associar_empresa(p["id"], p["empresa"], p["cargo"])
            for habilidade, nivel in p["habilidades"]:
                neo.associar_habilidade(p["id"], habilidade, nivel)

        for a, b in CONEXOES:
            neo.conectar(a, b)

        print("Neo4j pronto:", neo.estatisticas())
    finally:
        neo.close()


if __name__ == "__main__":
    main()
