"""Tela: Rede de Conexões e Busca de Mentores (Neo4j) integrada a Redis e MongoDB."""
import streamlit as st

from utils.ui import AVISO, exigir_login, get_mongo, get_neo4j, get_redis, mostrar_log, registrar_op

st.set_page_config(page_title="Rede e Mentores", page_icon="🕸️", layout="wide")
st.title("🕸️ Rede de Conexões e Mentores")
st.caption(AVISO)

sessao = exigir_login()
uid, meu_nome = sessao["usuario_id"], sessao["nome"]
mongo, redis_svc, neo = get_mongo(), get_redis(), get_neo4j()

try:
    pessoas = neo.listar_pessoas()
except Exception as erro:
    st.error(f"Erro ao consultar o Neo4j: {erro}")
    st.stop()

nomes = {p["id"]: p["nome"] for p in pessoas}
if uid not in nomes:
    st.warning("Seu usuário não existe no grafo. Rode `python -m scripts.init_neo4j`.")
    st.stop()


def montar_dot(arestas, nos_destaque=(), arestas_destaque=()):
    linhas = [
        "graph G {",
        'layout=neato; overlap=false; splines=true;',
        'node [shape=box, style="rounded,filled", fillcolor="#E8F1FB", fontname="Helvetica", fontsize=11];',
    ]
    for pid, nome in nomes.items():
        if pid == uid:
            cor = "#9FD3A8"
        elif pid in nos_destaque:
            cor = "#F5B971"
        else:
            cor = "#E8F1FB"
        linhas.append(f'"{pid}" [label="{nome}", fillcolor="{cor}"];')
    for a, b in arestas:
        destaque = frozenset((a, b)) in arestas_destaque
        estilo = 'color="#D9822B", penwidth=3' if destaque else 'color="#888888"'
        linhas.append(f'"{a}" -- "{b}" [{estilo}];')
    linhas.append("}")
    return "\n".join(linhas)


def conectar_e_notificar(destino):
    criada = neo.conectar(uid, destino)
    registrar_op("Neo4j", f"CREATE (:Pessoa {uid})-[:CONECTADO_COM]->(:Pessoa {destino})")
    if not criada:
        st.warning("Vocês já estão conectados.")
        return
    mongo.registrar_evento("conexao", uid, {"destino": destino})
    registrar_op("MongoDB", "insert eventos (conexao)")
    redis_svc.notificar(destino, f"{meu_nome} conectou-se com você.")
    registrar_op("Redis", f"INCR notif:nao_lidas:{destino}")
    st.rerun()


aba_rede, aba_graus, aba_mentor, aba_mapa = st.tabs(
    ["Minha rede", "Graus de separação", "Buscar mentor", "Mapa da rede"]
)

with aba_rede:
    st.markdown("**Minhas conexões diretas**")
    diretas = neo.conexoes_diretas(uid)
    registrar_op("Neo4j", f"MATCH conexoes diretas de {uid} -> {len(diretas)}")
    if not diretas:
        st.caption("Você ainda não tem conexões.")
    for c in diretas:
        st.write(f"- {c['nome']} ({c['papel']})")

    st.markdown("**Sugestões (amigos de amigos)**")
    sugestoes = neo.sugerir_conexoes(uid)
    registrar_op("Neo4j", f"MATCH amigos-de-amigos -> {len(sugestoes)}")
    if not sugestoes:
        st.caption("Sem sugestões no momento.")
    for s in sugestoes:
        col1, col2 = st.columns([4, 1])
        col1.write(f"{s['nome']} — {s['em_comum']} conexão(ões) em comum, via {', '.join(s['via'])}")
        if col2.button("Conectar", key=f"conectar_{s['id']}"):
            conectar_e_notificar(s["id"])

with aba_graus:
    outros = {i: n for i, n in nomes.items() if i != uid}
    destino = st.selectbox("Calcular caminho até", list(outros), format_func=lambda i: outros[i], key="destino_caminho")
    caminho = neo.caminho_mais_curto(uid, destino)
    registrar_op("Neo4j", f"shortestPath {uid} -> {destino}")
    if not caminho:
        st.info("Não há caminho entre os dois profissionais.")
        nos, pares = set(), set()
    else:
        st.success(f"{caminho['graus']} grau(s) de separação: " + " → ".join(caminho["nomes"]))
        nos = set(caminho["ids"])
        pares = {frozenset(par) for par in zip(caminho["ids"], caminho["ids"][1:])}
    arestas = [(c["a"], c["b"]) for c in neo.todas_conexoes()]
    st.graphviz_chart(montar_dot(arestas, nos, pares))

with aba_mentor:
    habilidades = neo.listar_habilidades()
    habilidade = st.selectbox("Habilidade que quero desenvolver", habilidades)
    mentores = neo.recomendar_mentores(uid, habilidade)
    registrar_op("Neo4j", f"recomendar mentores para '{habilidade}' -> {len(mentores)}")
    if not mentores:
        st.info("Nenhum mentor (nível 4 ou 5) encontrado para essa habilidade.")
    for m in mentores:
        graus = "sem caminho" if m["graus"] == 99 else ("conexão direta" if m["graus"] == 1 else f"{m['graus']} graus")
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{m['nome']}** ({m['papel']}) · nível {m['nivel']}/5 · {graus}")
        if col2.button("Pedir mentoria", key=f"mentor_{m['id']}"):
            mongo.registrar_evento("pedido_mentoria", uid, {"mentor": m["id"], "habilidade": habilidade})
            registrar_op("MongoDB", "insert eventos (pedido_mentoria)")
            redis_svc.notificar(m["id"], f"{meu_nome} pediu mentoria em {habilidade}.")
            registrar_op("Redis", f"INCR notif:nao_lidas:{m['id']}")
            st.success(f"Pedido enviado a {m['nome']}.")

with aba_mapa:
    arestas = [(c["a"], c["b"]) for c in neo.todas_conexoes()]
    st.caption("Verde = você. Cada linha é uma conexão profissional (CONECTADO_COM).")
    st.graphviz_chart(montar_dot(arestas))

mostrar_log()
