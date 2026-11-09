"""Serviço Redis: sessões, presença online, contador de notificações e cache de leituras."""
import json
import secrets
from datetime import datetime, timezone

import redis

import config

PADROES_APP = ("sessao:*", "presenca:*", "notif:*", "cache:*", "stats:*")


class RedisService:
    def __init__(self, url=None, client=None):
        self.r = client or redis.Redis.from_url(
            url or config.REDIS_URL, decode_responses=True, socket_connect_timeout=5
        )

    def ping(self):
        try:
            return bool(self.r.ping())
        except redis.RedisError:
            return False

    # --- sessões (chave sessao:<token>, String JSON com TTL deslizante) ---
    def criar_sessao(self, usuario_id, nome, ttl=None):
        token = secrets.token_urlsafe(16)
        valor = json.dumps({"usuario_id": usuario_id, "nome": nome})
        self.r.set(f"sessao:{token}", valor, ex=ttl or config.SESSAO_TTL)
        return token

    def obter_sessao(self, token, ttl=None):
        if not token:
            return None
        chave = f"sessao:{token}"
        bruto = self.r.get(chave)
        if bruto is None:
            return None
        self.r.expire(chave, ttl or config.SESSAO_TTL)
        return json.loads(bruto)

    def ttl_sessao(self, token):
        return self.r.ttl(f"sessao:{token}")

    def encerrar_sessao(self, token):
        return self.r.delete(f"sessao:{token}") == 1

    # --- presença (chave presenca:<id> com TTL; sem chave = offline) ---
    def definir_presenca(self, usuario_id, status="online", ttl=None):
        self.r.set(f"presenca:{usuario_id}", status, ex=ttl or config.PRESENCA_TTL)

    def remover_presenca(self, usuario_id):
        self.r.delete(f"presenca:{usuario_id}")

    def obter_presenca(self, usuario_id):
        return self.r.get(f"presenca:{usuario_id}") or "offline"

    def listar_presenca(self, ids):
        if not ids:
            return {}
        valores = self.r.mget([f"presenca:{i}" for i in ids])
        return {i: (v or "offline") for i, v in zip(ids, valores)}

    def ttl_presenca(self, usuario_id):
        return self.r.ttl(f"presenca:{usuario_id}")

    # --- notificações (contador notif:nao_lidas:<id> + lista notif:lista:<id>) ---
    def notificar(self, usuario_id, mensagem):
        item = json.dumps(
            {"mensagem": mensagem, "ts": datetime.now(timezone.utc).isoformat()}
        )
        pipe = self.r.pipeline()
        pipe.incr(f"notif:nao_lidas:{usuario_id}")
        pipe.lpush(f"notif:lista:{usuario_id}", item)
        pipe.ltrim(f"notif:lista:{usuario_id}", 0, 19)
        return pipe.execute()[0]

    def contar_nao_lidas(self, usuario_id):
        return int(self.r.get(f"notif:nao_lidas:{usuario_id}") or 0)

    def listar_notificacoes(self, usuario_id, limite=10):
        itens = self.r.lrange(f"notif:lista:{usuario_id}", 0, limite - 1)
        return [json.loads(i) for i in itens]

    def marcar_lidas(self, usuario_id):
        self.r.delete(f"notif:nao_lidas:{usuario_id}")

    # --- cache de leituras (cache:<chave> com TTL) ---
    def cache_get(self, chave):
        bruto = self.r.get(f"cache:{chave}")
        if bruto is None:
            self.r.incr("stats:cache:miss")
            return None
        self.r.incr("stats:cache:hit")
        return json.loads(bruto)

    def cache_set(self, chave, valor, ttl):
        self.r.set(f"cache:{chave}", json.dumps(valor, default=str), ex=ttl)

    def cache_invalidar(self, prefixo=""):
        chaves = list(self.r.scan_iter(match=f"cache:{prefixo}*"))
        if chaves:
            self.r.delete(*chaves)
        return len(chaves)

    def ttl_cache(self, chave):
        return self.r.ttl(f"cache:{chave}")

    def stats_cache(self):
        return {
            "hit": int(self.r.get("stats:cache:hit") or 0),
            "miss": int(self.r.get("stats:cache:miss") or 0),
        }

    # --- manutenção (só apaga chaves da aplicação, nunca FLUSHALL) ---
    def limpar_dados_app(self):
        total = 0
        for padrao in PADROES_APP:
            chaves = list(self.r.scan_iter(match=padrao))
            if chaves:
                total += self.r.delete(*chaves)
        return total
