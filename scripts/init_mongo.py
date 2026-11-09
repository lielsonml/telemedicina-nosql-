"""Cria coleções, índices e carrega usuários/posts fictícios no MongoDB.

Uso: python -m scripts.init_mongo [--reset]
"""
import sys
from datetime import timedelta

from bson import ObjectId

from data.seed_data import PESSOAS, POSTS
from services.mongo_service import MongoService, agora


def montar_usuario(p, criado_em):
    return {
        "_id": p["id"],
        "nome": p["nome"],
        "email": p["email"],
        "papel": p["papel"],
        "titulo": p["titulo"],
        "bio": p["bio"],
        "experiencias": p["experiencias"],
        "formacao": p["formacao"],
        "certificacoes": p["certificacoes"],
        "criado_em": criado_em,
    }


def main():
    reset = "--reset" in sys.argv
    mongo = MongoService()
    if not mongo.ping():
        print("ERRO: não foi possível conectar ao MongoDB. Verifique MONGO_URI no .env.")
        sys.exit(1)

    if reset:
        mongo.resetar()
        print("Coleções limpas.")

    mongo.criar_indices()
    base = agora()
    for p in PESSOAS:
        mongo.salvar_usuario(montar_usuario(p, base))

    if mongo.posts.count_documents({}) == 0:
        nomes = {p["id"]: p["nome"] for p in PESSOAS}
        for i, (autor, texto, tags, curtidas) in enumerate(POSTS):
            id_post = mongo.criar_post(autor, nomes[autor], texto, tags)
            mongo.posts.update_one(
                {"_id": ObjectId(id_post)},
                {"$set": {"curtidas": curtidas, "criado_em": base - timedelta(hours=5 * i)}},
            )

    print("MongoDB pronto:", mongo.contagens())


if __name__ == "__main__":
    main()
