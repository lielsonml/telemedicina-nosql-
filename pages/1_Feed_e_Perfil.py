"""Tela: Feed e Perfil (MongoDB) com cache de leitura no Redis."""
import streamlit as st

import config
from utils.ui import AVISO, exigir_login, get_mongo, get_redis, mostrar_log, registrar_op

st.set_page_config(page_title="Feed e Perfil", page_icon="📰", layout="wide")
st.title("📰 Feed e Perfil")
st.caption(AVISO)

sessao = exigir_login()
uid, meu_nome = sessao["usuario_id"], sessao["nome"]
mongo, redis_svc = get_mongo(), get_redis()


def carregar_feed(tag, busca):
    chave = f"feed:{tag or '-'}:{busca or '-'}"
    posts = redis_svc.cache_get(chave)
    if posts is not None:
        registrar_op("Redis", f"cache HIT {chave}")
        return posts
    registrar_op("Redis", f"cache MISS {chave}")
    posts = mongo.listar_posts(limite=20, tag=tag or None, busca=busca or None)
    registrar_op("MongoDB", f"find posts -> {len(posts)} docs")
    redis_svc.cache_set(chave, posts, config.CACHE_TTL_FEED)
    registrar_op("Redis", f"SET cache:{chave} EX {config.CACHE_TTL_FEED}")
    return posts


def carregar_perfil(alvo):
    chave = f"perfil:{alvo}"
    perfil = redis_svc.cache_get(chave)
    if perfil is not None:
        registrar_op("Redis", f"cache HIT {chave}")
        return perfil
    registrar_op("Redis", f"cache MISS {chave}")
    perfil = mongo.obter_usuario(alvo)
    registrar_op("MongoDB", f"findOne usuarios {alvo}")
    if perfil:
        redis_svc.cache_set(chave, perfil, config.CACHE_TTL_PERFIL)
        registrar_op("Redis", f"SET cache:{chave} EX {config.CACHE_TTL_PERFIL}")
    return perfil


aba_feed, aba_perfil = st.tabs(["Feed", "Perfil"])

with aba_feed:
    with st.form("novo_post", clear_on_submit=True):
        texto = st.text_area("Nova publicação", placeholder="Compartilhe uma boa prática de telessaúde (sem dados reais de pacientes).")
        tags_txt = st.text_input("Tags (separadas por vírgula)", placeholder="teleconsulta, lgpd")
        enviar = st.form_submit_button("Publicar")
    if enviar:
        try:
            tags = [t for t in tags_txt.split(",")]
            mongo.criar_post(uid, meu_nome, texto, tags)
            registrar_op("MongoDB", "insertOne posts")
            n = redis_svc.cache_invalidar("feed:")
            registrar_op("Redis", f"cache invalidado ({n} chaves feed:*)")
            st.rerun()
        except ValueError as erro:
            st.warning(str(erro))
        except Exception as erro:
            st.error(f"Erro ao publicar: {erro}")

    f1, f2 = st.columns(2)
    filtro_tag = f1.text_input("Filtrar por tag").strip().lower()
    filtro_busca = f2.text_input("Buscar no texto").strip()

    try:
        posts = carregar_feed(filtro_tag, filtro_busca)
    except Exception as erro:
        st.error(f"Erro ao carregar o feed: {erro}")
        posts = []

    if not posts:
        st.info("Nenhuma publicação encontrada.")
    for p in posts:
        with st.container(border=True):
            st.markdown(f"**{p['autor_nome']}** · {str(p['criado_em'])[:16]}")
            st.write(p["texto"])
            if p.get("tags"):
                st.caption(" ".join(f"#{t}" for t in p["tags"]))
            b1, b2, _ = st.columns([1, 1, 6])
            if b1.button(f"👍 {p['curtidas']}", key=f"like_{p['_id']}"):
                mongo.curtir_post(p["_id"])
                registrar_op("MongoDB", "findOneAndUpdate $inc curtidas")
                redis_svc.cache_invalidar("feed:")
                registrar_op("Redis", "cache invalidado (feed:*)")
                st.rerun()
            if p["autor_id"] == uid and b2.button("🗑️ Excluir", key=f"del_{p['_id']}"):
                mongo.excluir_post(p["_id"], uid)
                registrar_op("MongoDB", "deleteOne posts")
                redis_svc.cache_invalidar("feed:")
                registrar_op("Redis", "cache invalidado (feed:*)")
                st.rerun()

with aba_perfil:
    usuarios = mongo.listar_usuarios()
    nomes = {u["_id"]: u["nome"] for u in usuarios}
    ids = list(nomes)
    alvo = st.selectbox("Perfil", ids, index=ids.index(uid) if uid in ids else 0, format_func=lambda i: nomes[i])

    perfil = carregar_perfil(alvo)
    if not perfil:
        st.warning("Perfil não encontrado.")
    else:
        st.subheader(perfil["nome"])
        st.write(f"**{perfil['titulo']}** · {perfil['papel']}")
        st.write(perfil["bio"])
        st.markdown("**Experiências**")
        for e in perfil.get("experiencias", []):
            st.write(f"- {e['cargo']} em {e['instituicao']} ({e['inicio']}–{e.get('fim') or 'atual'})")
        st.markdown("**Formação**")
        for f in perfil.get("formacao", []):
            st.write(f"- {f['curso']} — {f['instituicao']} ({f['ano']})")
        st.markdown("**Certificações**")
        for c in perfil.get("certificacoes", []) or []:
            st.write(f"- {c['nome']} — {c['emissor']} ({c['ano']})")
        if not perfil.get("certificacoes"):
            st.caption("Nenhuma certificação cadastrada.")

        if alvo == uid:
            st.divider()
            st.markdown("**Editar meu perfil**")
            with st.form("editar_perfil"):
                novo_titulo = st.text_input("Título", value=perfil["titulo"])
                nova_bio = st.text_area("Bio", value=perfil["bio"])
                salvar = st.form_submit_button("Salvar")
            if salvar:
                mongo.atualizar_perfil(uid, {"titulo": novo_titulo, "bio": nova_bio})
                registrar_op("MongoDB", "updateOne $set perfil")
                redis_svc.cache_invalidar(f"perfil:{uid}")
                registrar_op("Redis", f"cache invalidado perfil:{uid}")
                st.rerun()

            with st.form("nova_experiencia", clear_on_submit=True):
                st.markdown("**Adicionar experiência**")
                inst = st.text_input("Instituição")
                cargo = st.text_input("Cargo")
                inicio = st.number_input("Ano de início", min_value=1980, max_value=2026, value=2024, step=1)
                desc = st.text_input("Descrição")
                add = st.form_submit_button("Adicionar")
            if add and inst and cargo:
                mongo.adicionar_experiencia(
                    uid, {"instituicao": inst, "cargo": cargo, "inicio": int(inicio), "fim": None, "descricao": desc}
                )
                registrar_op("MongoDB", "updateOne $push experiencias")
                redis_svc.cache_invalidar(f"perfil:{uid}")
                registrar_op("Redis", f"cache invalidado perfil:{uid}")
                st.rerun()

mostrar_log()
