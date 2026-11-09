"""Serviço MongoDB: perfis estendidos, posts da linha do tempo e log de eventos."""
import re
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument
from pymongo.errors import PyMongoError

import config

CAMPOS_EDITAVEIS = {"nome", "titulo", "bio"}


def agora():
    return datetime.now(timezone.utc)


def _oid(valor):
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        return None


class MongoService:
    def __init__(self, uri=None, db_name=None, client=None):
        self.client = client or MongoClient(
            uri or config.MONGO_URI, serverSelectionTimeoutMS=5000
        )
        self.db = self.client[db_name or config.MONGO_DB]
        self.usuarios = self.db["usuarios"]
        self.posts = self.db["posts"]
        self.eventos = self.db["eventos"]

    # --- infraestrutura ---
    def ping(self):
        try:
            self.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    def criar_indices(self):
        self.usuarios.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
        self.posts.create_index(
            [("autor_id", ASCENDING), ("criado_em", DESCENDING)], name="posts_autor_data"
        )
        self.posts.create_index([("tags", ASCENDING)], name="posts_tags")
        self.eventos.create_index([("criado_em", DESCENDING)], name="eventos_data")

    def resetar(self):
        self.usuarios.delete_many({})
        self.posts.delete_many({})
        self.eventos.delete_many({})

    def contagens(self):
        return {
            "usuarios": self.usuarios.count_documents({}),
            "posts": self.posts.count_documents({}),
            "eventos": self.eventos.count_documents({}),
        }

    # --- usuários (perfil estendido) ---
    def salvar_usuario(self, doc):
        self.usuarios.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    def obter_usuario(self, uid):
        return self.usuarios.find_one({"_id": uid})

    def listar_usuarios(self):
        cursor = self.usuarios.find({}, {"nome": 1, "titulo": 1, "papel": 1})
        return list(cursor.sort("nome", ASCENDING))

    def atualizar_perfil(self, uid, campos):
        validos = {k: v for k, v in campos.items() if k in CAMPOS_EDITAVEIS}
        if not validos:
            return False
        res = self.usuarios.update_one({"_id": uid}, {"$set": validos})
        return res.matched_count == 1

    def adicionar_experiencia(self, uid, experiencia):
        res = self.usuarios.update_one({"_id": uid}, {"$push": {"experiencias": experiencia}})
        return res.matched_count == 1

    def adicionar_certificacao(self, uid, certificacao):
        res = self.usuarios.update_one({"_id": uid}, {"$push": {"certificacoes": certificacao}})
        return res.matched_count == 1

    # --- posts (linha do tempo) ---
    def criar_post(self, autor_id, autor_nome, texto, tags=None, anexos=None):
        texto = (texto or "").strip()
        if not texto:
            raise ValueError("O texto do post não pode ser vazio.")
        doc = {
            "autor_id": autor_id,
            "autor_nome": autor_nome,
            "texto": texto,
            "tags": [t.strip().lower() for t in (tags or []) if t.strip()],
            "anexos": anexos or [],
            "curtidas": 0,
            "criado_em": agora(),
        }
        return str(self.posts.insert_one(doc).inserted_id)

    def listar_posts(self, limite=20, autor_id=None, tag=None, busca=None):
        filtro = {}
        if autor_id:
            filtro["autor_id"] = autor_id
        if tag:
            filtro["tags"] = tag.strip().lower()
        if busca:
            filtro["texto"] = {"$regex": re.escape(busca), "$options": "i"}
        docs = list(self.posts.find(filtro).sort("criado_em", DESCENDING).limit(limite))
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    def curtir_post(self, post_id):
        oid = _oid(post_id)
        if oid is None:
            return None
        doc = self.posts.find_one_and_update(
            {"_id": oid}, {"$inc": {"curtidas": 1}}, return_document=ReturnDocument.AFTER
        )
        return doc["curtidas"] if doc else None

    def excluir_post(self, post_id, autor_id):
        oid = _oid(post_id)
        if oid is None:
            return False
        res = self.posts.delete_one({"_id": oid, "autor_id": autor_id})
        return res.deleted_count == 1

    # --- eventos (log) ---
    def registrar_evento(self, tipo, usuario_id, detalhes=None):
        doc = {
            "tipo": tipo,
            "usuario_id": usuario_id,
            "detalhes": detalhes or {},
            "criado_em": agora(),
        }
        return str(self.eventos.insert_one(doc).inserted_id)

    def listar_eventos(self, limite=10):
        docs = list(self.eventos.find({}).sort("criado_em", DESCENDING).limit(limite))
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs
