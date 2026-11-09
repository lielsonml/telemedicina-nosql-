"""Limpa apenas as chaves da aplicação e cria presença/notificações iniciais no Redis.

Uso: python -m scripts.init_redis
Obs.: a presença tem TTL (PRESENCA_TTL); depois que expira, o usuário aparece offline.
"""
import sys

from services.redis_service import RedisService


def main():
    redis_svc = RedisService()
    if not redis_svc.ping():
        print("ERRO: não foi possível conectar ao Redis. Verifique REDIS_URL no .env.")
        sys.exit(1)

    apagadas = redis_svc.limpar_dados_app()
    print(f"Chaves antigas da aplicação removidas: {apagadas}")

    for uid, status in (("p01", "online"), ("p03", "online"), ("p06", "online"), ("p02", "em_consulta")):
        redis_svc.definir_presenca(uid, status)

    redis_svc.notificar("p01", "Bem-vinda à TeleRede Saúde!")
    redis_svc.notificar("p01", "Dr. Marcos Vieira pediu uma segunda opinião (caso fictício).")
    redis_svc.notificar("p02", "Você tem um novo convite de conexão.")

    print("Redis pronto: presença inicial e notificações de exemplo criadas.")


if __name__ == "__main__":
    main()
