# TeleRede Saúde — Projeto Final NoSQL (UNIPÊ)

Rede profissional de **telemedicina** (adaptação do Estudo de Caso 02 do manual) com **persistência poliglota**:

| Banco | Papel no projeto |
|---|---|
| **MongoDB** | Perfil estendido (experiências, formação, certificações), posts da linha do tempo e log de eventos |
| **Redis** | Sessões (TTL), presença online/offline (TTL), contador de notificações não lidas e cache de leituras |
| **Neo4j** | Rede `(:Pessoa)-[:CONECTADO_COM]->(:Pessoa)`, habilidades, instituições, `shortestPath` e mentores |

> Protótipo acadêmico. Todos os dados são fictícios e o sistema não realiza diagnóstico.

## Requisitos
- Python 3.10+ e Git
- Uma instância de cada banco (nuvem gratuita **ou** `docker-compose.yml`):
  MongoDB Atlas (M0), Redis Cloud (free) e Neo4j AuraDB Free.

## Instalação (Windows / PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1      # se bloquear: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env             # preencha MONGO_URI, REDIS_URL, NEO4J_*
```

## Inicialização dos bancos
```powershell
python -m scripts.check_connections   # deve mostrar OK nos três
python -m scripts.init_mongo          # índices + usuários + posts (use --reset para recarregar)
python -m scripts.init_redis          # presença/notificações iniciais
python -m scripts.init_neo4j          # constraints + grafo (use --reset para recarregar)
```

## Executar
```powershell
streamlit run app.py
```

## Testes
```powershell
pytest -v
```
Os testes usam o banco `<MONGO_DB>_teste` no Mongo e ids iniciados por `t_` no Redis/Neo4j, e removem o que criam.
Testes de um banco indisponível são pulados.

## Estrutura
```
app.py                       login (sessão no Redis) + painel dos três bancos
pages/1_Feed_e_Perfil.py     MongoDB + cache Redis
pages/2_Presenca_e_Notificacoes.py   Redis
pages/3_Rede_e_Mentores.py   Neo4j + integração com Mongo e Redis
services/                    mongo_service.py · redis_service.py · neo4j_service.py
scripts/                     init_mongo · init_redis · init_neo4j · check_connections
data/seed_data.py            dados fictícios
utils/ui.py                  serviços compartilhados, login e log de operações
tests/                       testes por banco + integração
```

## Chaves do Redis
`sessao:<token>` · `presenca:<id>` · `notif:nao_lidas:<id>` · `notif:lista:<id>` · `cache:feed:*` · `cache:perfil:<id>` · `stats:cache:hit|miss`
