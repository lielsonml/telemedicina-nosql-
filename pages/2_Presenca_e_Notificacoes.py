"""Tela: Dashboard de Presença e Notificações (Redis em tempo real)."""
import pandas as pd
import streamlit as st

import config
from utils.ui import AVISO, exigir_login, get_mongo, get_redis, mostrar_log, registrar_op

st.set_page_config(page_title="Presença e Notificações", page_icon="🟢", layout="wide")
st.title("🟢 Presença e Notificações")
st.caption(AVISO)

sessao = exigir_login()
uid, meu_nome = sessao["usuario_id"], sessao["nome"]
mongo, redis_svc = get_mongo(), get_redis()

OPCOES = ["online", "em_consulta", "offline"]
ICONES = {"online": "🟢 online", "em_consulta": "🟡 em consulta", "offline": "⚪ offline"}

st.subheader("Meu status")
atual = st.session_state.get("status_presenca", "online")
novo = st.radio("Status de presença", OPCOES, index=OPCOES.index(atual), horizontal=True)
if novo != atual:
    st.session_state["status_presenca"] = novo
    if novo == "offline":
        redis_svc.remover_presenca(uid)
        registrar_op("Redis", f"DEL presenca:{uid}")
    else:
        redis_svc.definir_presenca(uid, novo)
        registrar_op("Redis", f"SET presenca:{uid}={novo} EX {config.PRESENCA_TTL}")
    st.rerun()
st.caption(
    f"A presença expira em {config.PRESENCA_TTL}s sem atividade (TTL). "
    f"TTL restante do meu status: {redis_svc.ttl_presenca(uid)}s"
)

st.subheader("Equipe")
usuarios = mongo.listar_usuarios()
ids = [u["_id"] for u in usuarios]
presenca = redis_svc.listar_presenca(ids)
registrar_op("Redis", f"MGET presenca:* ({len(ids)} chaves)")
m1, m2, m3 = st.columns(3)
m1.metric("Online", sum(1 for s in presenca.values() if s == "online"))
m2.metric("Em consulta", sum(1 for s in presenca.values() if s == "em_consulta"))
m3.metric("Offline", sum(1 for s in presenca.values() if s == "offline"))
tabela = pd.DataFrame(
    [
        {
            "Profissional": u["nome"],
            "Papel": u["papel"],
            "Status": ICONES[presenca[u["_id"]]],
            "TTL (s)": redis_svc.ttl_presenca(u["_id"]) if presenca[u["_id"]] != "offline" else None,
        }
        for u in usuarios
    ]
)
st.dataframe(tabela, hide_index=True)
st.button("Atualizar painel")

st.subheader("Notificações")
nao_lidas = redis_svc.contar_nao_lidas(uid)
st.metric("Não lidas", nao_lidas)
for n in redis_svc.listar_notificacoes(uid, 10):
    st.caption(f"{n['ts'][:19]} · {n['mensagem']}")
if st.button("Marcar todas como lidas"):
    redis_svc.marcar_lidas(uid)
    registrar_op("Redis", f"DEL notif:nao_lidas:{uid}")
    st.rerun()

with st.form("enviar_notificacao", clear_on_submit=True):
    st.markdown("**Enviar notificação a um colega**")
    outros = {u["_id"]: u["nome"] for u in usuarios if u["_id"] != uid}
    destino = st.selectbox("Destinatário", list(outros), format_func=lambda i: outros[i])
    mensagem = st.text_input("Mensagem")
    enviar = st.form_submit_button("Enviar")
if enviar and mensagem.strip():
    total = redis_svc.notificar(destino, f"{meu_nome}: {mensagem.strip()}")
    registrar_op("Redis", f"INCR notif:nao_lidas:{destino} -> {total}")
    mongo.registrar_evento("notificacao", uid, {"destino": destino})
    registrar_op("MongoDB", "insert eventos (notificacao)")
    st.success(f"Notificação enviada. {outros[destino]} agora tem {total} não lida(s).")

st.subheader("Cache de leituras")
stats = redis_svc.stats_cache()
c1, c2 = st.columns(2)
c1.metric("Cache hits", stats["hit"])
c2.metric("Cache misses", stats["miss"])
st.caption(f"TTL do cache: feed {config.CACHE_TTL_FEED}s · perfil {config.CACHE_TTL_PERFIL}s")
if st.button("Limpar cache"):
    n = redis_svc.cache_invalidar("")
    registrar_op("Redis", f"cache limpo ({n} chaves)")
    st.rerun()

mostrar_log()
