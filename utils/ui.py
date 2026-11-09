"""Utilitários compartilhados da interface: serviços, sessão/login e log de operações."""
import streamlit as st

from services.mongo_service import MongoService
from services.neo4j_service import Neo4jService
from services.redis_service import RedisService

AVISO = (
    "Protótipo acadêmico com dados fictícios. Não substitui atendimento médico "
    "e não realiza diagnóstico."
)


@st.cache_resource
def get_mongo():
    return MongoService()


@st.cache_resource
def get_redis():
    return RedisService()


@st.cache_resource
def get_neo4j():
    return Neo4jService()


def registrar_op(banco, descricao):
    log = st.session_state.setdefault("log_ops", [])
    log.insert(0, f"[{banco}] {descricao}")
    del log[25:]


def mostrar_log():
    with st.sidebar:
        with st.expander("Log de operações nos bancos", expanded=True):
            for linha in st.session_state.get("log_ops", [])[:12]:
                st.caption(linha)


def sessao_atual():
    """Retorna a sessão válida no Redis (renovando o TTL) ou None."""
    token = st.session_state.get("token")
    if not token:
        return None
    sessao = get_redis().obter_sessao(token)
    if sessao is None:
        st.session_state.pop("token", None)
    return sessao


def sair(sessao):
    redis_svc = get_redis()
    redis_svc.encerrar_sessao(st.session_state.get("token"))
    redis_svc.remover_presenca(sessao["usuario_id"])
    registrar_op("Redis", "DEL sessao e presenca")
    st.session_state.pop("token", None)
    st.session_state.pop("status_presenca", None)
    st.rerun()


def exigir_login():
    """Garante sessão ativa; atualiza a presença (heartbeat) e desenha a barra lateral."""
    try:
        sessao = sessao_atual()
    except Exception as erro:
        st.error(f"Não foi possível consultar o Redis: {erro}")
        st.stop()

    if not sessao:
        st.warning("Sessão inexistente ou expirada. Volte à página inicial e entre novamente.")
        st.stop()

    redis_svc = get_redis()
    uid = sessao["usuario_id"]
    status = st.session_state.get("status_presenca", "online")
    if status != "offline":
        redis_svc.definir_presenca(uid, status)

    with st.sidebar:
        st.markdown(f"**{sessao['nome']}**")
        st.caption(f"Sessão expira em {redis_svc.ttl_sessao(st.session_state['token'])}s (Redis TTL)")
        st.metric("Notificações não lidas", redis_svc.contar_nao_lidas(uid))
        if st.button("Sair", key="btn_sair"):
            sair(sessao)
    return sessao
