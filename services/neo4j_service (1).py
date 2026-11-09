"""Serviço Neo4j: rede de profissionais, habilidades, instituições e consultas Cypher."""
from neo4j import GraphDatabase

import config


class Neo4jService:
    def __init__(self, uri=None, user=None, password=None, database=None, driver=None):
        self.database = database or config.NEO4J_DATABASE
        self.driver = driver or GraphDatabase.driver(
            uri or config.NEO4J_URI,
            auth=(user or config.NEO4J_USERNAME, password or config.NEO4J_PASSWORD),
        )

    def close(self):
        self.driver.close()

    def ping(self):
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def _ler(self, query, **params):
        with self.driver.session(database=self.database) as sessao:
            return sessao.run(query, **params).data()

    def _escrever(self, query, **params):
        with self.driver.session(database=self.database) as sessao:
            resultado = sessao.run(query, **params)
            resultado.data()
            return resultado.consume().counters

    # --- infraestrutura ---
    def criar_constraints(self):
        for query in (
            "CREATE CONSTRAINT pessoa_id IF NOT EXISTS FOR (p:Pessoa) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT habilidade_nome IF NOT EXISTS FOR (h:Habilidade) REQUIRE h.nome IS UNIQUE",
            "CREATE CONSTRAINT empresa_nome IF NOT EXISTS FOR (e:Empresa) REQUIRE e.nome IS UNIQUE",
        ):
            self._escrever(query)

    def limpar_grafo(self):
        self._escrever("MATCH (n) DETACH DELETE n")

    def estatisticas(self):
        nos = self._ler("MATCH (n) RETURN labels(n)[0] AS tipo, count(*) AS total ORDER BY tipo")
        rels = self._ler("MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY tipo")
        return {"nos": nos, "relacionamentos": rels}

    # --- escrita ---
    def upsert_pessoa(self, pid, nome, papel):
        self._escrever(
            "MERGE (p:Pessoa {id: $id}) SET p.nome = $nome, p.papel = $papel",
            id=pid, nome=nome, papel=papel,
        )

    def associar_habilidade(self, pid, habilidade, nivel):
        self._escrever(
            """
            MATCH (p:Pessoa {id: $id})
            MERGE (h:Habilidade {nome: $hab})
            MERGE (p)-[r:POSSUI_HABILIDADE]->(h)
            SET r.nivel = $nivel
            """,
            id=pid, hab=habilidade, nivel=nivel,
        )

    def associar_empresa(self, pid, empresa, cargo):
        self._escrever(
            """
            MATCH (p:Pessoa {id: $id})
            MERGE (e:Empresa {nome: $empresa})
            MERGE (p)-[r:TRABALHA_EM]->(e)
            SET r.cargo = $cargo
            """,
            id=pid, empresa=empresa, cargo=cargo,
        )

    def conectar(self, a, b):
        counters = self._escrever(
            """
            MATCH (a:Pessoa {id: $a}), (b:Pessoa {id: $b})
            WHERE a <> b AND NOT (a)-[:CONECTADO_COM]-(b)
            CREATE (a)-[:CONECTADO_COM {desde: toString(date())}]->(b)
            """,
            a=a, b=b,
        )
        return counters.relationships_created == 1

    def desconectar(self, a, b):
        counters = self._escrever(
            "MATCH (:Pessoa {id: $a})-[r:CONECTADO_COM]-(:Pessoa {id: $b}) DELETE r",
            a=a, b=b,
        )
        return counters.relationships_deleted >= 1

    # --- leitura ---
    def listar_pessoas(self):
        return self._ler(
            "MATCH (p:Pessoa) RETURN p.id AS id, p.nome AS nome, p.papel AS papel ORDER BY p.nome"
        )

    def listar_habilidades(self):
        dados = self._ler("MATCH (h:Habilidade) RETURN h.nome AS nome ORDER BY h.nome")
        return [d["nome"] for d in dados]

    def habilidades_da_pessoa(self, pid):
        return self._ler(
            """
            MATCH (:Pessoa {id: $id})-[r:POSSUI_HABILIDADE]->(h:Habilidade)
            RETURN h.nome AS nome, r.nivel AS nivel ORDER BY r.nivel DESC, nome
            """,
            id=pid,
        )

    def conexoes_diretas(self, pid):
        return self._ler(
            """
            MATCH (:Pessoa {id: $id})-[:CONECTADO_COM]-(c:Pessoa)
            RETURN c.id AS id, c.nome AS nome, c.papel AS papel ORDER BY c.nome
            """,
            id=pid,
        )

    def todas_conexoes(self):
        return self._ler(
            "MATCH (a:Pessoa)-[:CONECTADO_COM]->(b:Pessoa) RETURN a.id AS a, b.id AS b"
        )

    def caminho_mais_curto(self, origem, destino):
        if origem == destino:
            return None
        dados = self._ler(
            """
            MATCH (a:Pessoa {id: $o}), (b:Pessoa {id: $d})
            MATCH caminho = shortestPath((a)-[:CONECTADO_COM*..8]-(b))
            RETURN [n IN nodes(caminho) | n.id] AS ids,
                   [n IN nodes(caminho) | n.nome] AS nomes,
                   length(caminho) AS graus
            """,
            o=origem, d=destino,
        )
        return dados[0] if dados else None

    def recomendar_mentores(self, pid, habilidade, limite=5):
        return self._ler(
            """
            MATCH (eu:Pessoa {id: $id})
            MATCH (m:Pessoa)-[r:POSSUI_HABILIDADE]->(h:Habilidade {nome: $hab})
            WHERE m <> eu AND r.nivel >= 4
            OPTIONAL MATCH caminho = shortestPath((eu)-[:CONECTADO_COM*..6]-(m))
            RETURN m.id AS id, m.nome AS nome, m.papel AS papel, r.nivel AS nivel,
                   coalesce(length(caminho), 99) AS graus
            ORDER BY graus, nivel DESC, nome
            LIMIT $limite
            """,
            id=pid, hab=habilidade, limite=limite,
        )

    def sugerir_conexoes(self, pid, limite=5):
        return self._ler(
            """
            MATCH (eu:Pessoa {id: $id})-[:CONECTADO_COM]-(amigo:Pessoa)-[:CONECTADO_COM]-(sug:Pessoa)
            WHERE sug <> eu AND NOT (eu)-[:CONECTADO_COM]-(sug)
            RETURN sug.id AS id, sug.nome AS nome,
                   count(DISTINCT amigo) AS em_comum, collect(DISTINCT amigo.nome) AS via
            ORDER BY em_comum DESC, nome
            LIMIT $limite
            """,
            id=pid, limite=limite,
        )
