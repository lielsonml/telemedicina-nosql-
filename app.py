"""Página inicial: status dos bancos, login (sessão no Redis) e painel dos três bancos."""
import streamlit as st

from utils.ui import (
    AVISO, exigir_login, get_mongo, get_neo4j, get_redis, mostrar_log, registrar_op, sessao_atual,
)

st.set_page_config(page_title="TeleRede Saúde", page_icon="🩺", layout="wide")
st.title("🩺 TeleRede Saúde")
st.caption("Rede profissional de telemedicina · persistência poliglota: MongoDB + Redis + Neo4j")
st.info(AVISO)


def status_bancos():
    resultado = {}
    for nome, getter in (("MongoDB", get_mongo), ("Redis", get_redis), ("Neo4j", get_neo4j)):
        try:
            resultado[nome] = getter().ping()
        except Exception:
            resultado[nome] = False
    return resultado


status = status_bancos()
cols = st.columns(3)
for col, (nome, ok) in zip(cols, status.items()):
    col.metric(nome, "conectado ✅" if ok else "indisponível ❌")

if not all(status.values()):
    st.error("Algum banco está indisponível. Confira o .env e rode `python -m scripts.check_connections`.")
    st.stop()

mongo, redis_svc, neo4j = get_mongo(), get_redis(), get_neo4j()

try:
    sessao = sessao_atual()
except Exception as erro:
    st.error(f"Erro ao consultar a sessão: {erro}")
    st.stop()

if not sessao:
    st.subheader("Entrar (sessão armazenada no Redis)")
    usuarios = mongo.listar_usuarios()
    if not usuarios:
        st.warning("Nenhum usuário encontrado. Rode os scripts de inicialização (veja o README).")
        st.stop()
    nomes = {u["_id"]: f"{u['nome']} — {u['titulo']}" for u in usuarios}
    escolhido = st.selectbox("Profissional (dados fictícios)", list(nomes), format_func=lambda i: nomes[i])
    if st.button("Entrar", type="primary"):
        nome = next(u["nome"] for u in usuarios if u["_id"] == escolhido)
        token = redis_svc.criar_sessao(escolhido, nome)
        st.session_state["token"] = token
        st.session_state["status_presenca"] = "online"
        redis_svc.definir_presenca(escolhido, "online")
        mongo.registrar_evento("login", escolhido, {"nome": nome})
        registrar_op("MongoDB", "SELECT usuarios (lista de profissionais)")
        registrar_op("Redis", f"SET sessao:<token> TTL e presenca:{escolhido}")
        registrar_op("MongoDB", "INSERT eventos (login)")
        st.rerun()
    mostrar_log()
    st.stop()

sessao = exigir_login()
st.success(f"Bem-vindo(a), {sessao['nome']}! Use o menu lateral para navegar pelas telas.")

st.subheader("Painel dos três bancos")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**MongoDB** — documentos")
    st.json(mongo.contagens())
with c2:
    st.markdown("**Redis** — tempo real")
    presenca = redis_svc.listar_presenca([u["_id"] for u in mongo.listar_usuarios()])
    st.metric("Profissionais online", sum(1 for s in presenca.values() if s != "offline"))
    st.json(redis_svc.stats_cache())
with c3:
    st.markdown("**Neo4j** — grafo")
    st.json(neo4j.estatisticas())

with st.expander("Últimos eventos registrados (MongoDB)"):
    for ev in mongo.listar_eventos(8):
        st.caption(f"{str(ev['criado_em'])[:19]} · {ev['tipo']} · {ev['usuario_id']} · {ev['detalhes']}")

mostrar_log()
