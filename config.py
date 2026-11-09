"""Configuração central: lê variáveis de ambiente (.env) usadas pelos três bancos."""
import os

from dotenv import load_dotenv

load_dotenv()


def _int(nome, padrao):
    try:
        return int(os.getenv(nome) or padrao)
    except ValueError:
        return padrao


MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017"
MONGO_DB = os.getenv("MONGO_DB") or "telemedicina"

REDIS_URL = os.getenv("REDIS_URL") or "redis://localhost:6379/0"

NEO4J_URI = os.getenv("NEO4J_URI") or "bolt://localhost:7687"
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") or "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") or ""
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") or "neo4j"

SESSAO_TTL = _int("SESSAO_TTL", 1800)
PRESENCA_TTL = _int("PRESENCA_TTL", 120)
CACHE_TTL_FEED = _int("CACHE_TTL_FEED", 30)
CACHE_TTL_PERFIL = _int("CACHE_TTL_PERFIL", 120)
