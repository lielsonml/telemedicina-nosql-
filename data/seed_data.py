"""Dados FICTÍCIOS para demonstração. Nenhuma pessoa, instituição ou caso clínico é real."""


def _pessoa(id_, nome, papel, titulo, bio, habilidades, empresa, cargo, desde, formacao, cert=None):
    return {
        "id": id_,
        "nome": nome,
        "email": f"{id_}@telerede.exemplo",
        "papel": papel,
        "titulo": titulo,
        "bio": bio,
        "habilidades": habilidades,
        "empresa": empresa,
        "cargo": cargo,
        "experiencias": [
            {
                "instituicao": empresa,
                "cargo": cargo,
                "inicio": desde,
                "fim": None,
                "descricao": f"Atuação em {empresa} com foco em atendimento remoto.",
            }
        ],
        "formacao": [{"curso": formacao[0], "instituicao": formacao[1], "ano": formacao[2]}],
        "certificacoes": (
            [{"nome": cert[0], "emissor": cert[1], "ano": cert[2]}] if cert else []
        ),
    }


UNI = "Universidade Fictícia de Saúde"

PESSOAS = [
    _pessoa("p01", "Dra. Helena Duarte", "Médica", "Cardiologista e mentora em telemonitoramento",
            "Acompanha pacientes cardíacos à distância e orienta colegas em telemonitoramento.",
            [("Cardiologia", 5), ("Telemonitoramento", 5), ("Teleconsulta", 4)],
            "Telecor Cardio", "Coordenadora de Telecardiologia", 2019,
            ("Medicina", UNI, 2008), ("Telemedicina Avançada", "Instituto Telessaúde (fictício)", 2021)),
    _pessoa("p02", "Dr. Marcos Vieira", "Médico", "Clínico geral com foco em teleconsulta",
            "Atende demandas gerais por vídeo e participa da triagem de encaminhamentos.",
            [("Clínica Geral", 5), ("Teleconsulta", 5), ("Prontuário Eletrônico", 4)],
            "Clínica TeleVida", "Médico de Família Remoto", 2017, ("Medicina", UNI, 2012)),
    _pessoa("p03", "Enf. Beatriz Lima", "Enfermeira", "Enfermeira de telemonitoramento",
            "Faz o acompanhamento diário de pacientes crônicos por plataforma digital.",
            [("Enfermagem", 5), ("Telemonitoramento", 4), ("Prontuário Eletrônico", 3)],
            "Telecor Cardio", "Enfermeira de Monitoramento", 2020, ("Enfermagem", UNI, 2015)),
    _pessoa("p04", "Dr. Rafael Nogueira", "Médico", "Dermatologista em teledermatologia",
            "Avalia imagens enviadas por pacientes e profissionais da atenção primária.",
            [("Dermatologia", 5), ("Teleconsulta", 4), ("Segurança de Dados (LGPD)", 2)],
            "Núcleo Saúde Digital", "Dermatologista Consultor", 2018, ("Medicina", UNI, 2010)),
    _pessoa("p05", "Dra. Camila Torres", "Médica", "Pediatra em teleconsulta",
            "Atendimento pediátrico remoto e orientação a famílias.",
            [("Pediatria", 5), ("Teleconsulta", 4)],
            "Clínica TeleVida", "Pediatra", 2016, ("Medicina", UNI, 2011)),
    _pessoa("p06", "Psic. Lucas Almeida", "Psicólogo", "Psicólogo em saúde mental digital",
            "Atendimento psicológico online e protocolos de acolhimento remoto.",
            [("Psicologia", 5), ("Saúde Mental Digital", 5), ("Teleconsulta", 4)],
            "Núcleo Saúde Digital", "Psicólogo Clínico", 2019, ("Psicologia", UNI, 2014)),
    _pessoa("p07", "Dra. Sofia Barros", "Médica", "Endocrinologista",
            "Acompanhamento remoto de pacientes com doenças metabólicas.",
            [("Endocrinologia", 5), ("Telemonitoramento", 3)],
            "Hospital Virtual Aurora", "Endocrinologista", 2015, ("Medicina", UNI, 2009)),
    _pessoa("p08", "Farm. Gabriel Rocha", "Farmacêutico", "Farmacêutico clínico e privacidade de dados",
            "Revisão de prescrições e boas práticas de proteção de dados em saúde.",
            [("Farmácia Clínica", 5), ("Segurança de Dados (LGPD)", 4)],
            "Hospital Virtual Aurora", "Farmacêutico Clínico", 2018, ("Farmácia", UNI, 2013)),
    _pessoa("p09", "Dr. André Menezes", "Médico", "Neurologista",
            "Segunda opinião neurológica por teleinterconsulta.",
            [("Neurologia", 5), ("Teleconsulta", 3)],
            "Hospital Virtual Aurora", "Neurologista", 2014, ("Medicina", UNI, 2007)),
    _pessoa("p10", "Enf. Júlia Cardoso", "Enfermeira", "Enfermeira pediátrica",
            "Apoio a famílias e triagem pediátrica remota.",
            [("Enfermagem", 4), ("Pediatria", 4), ("Teleconsulta", 3)],
            "Clínica TeleVida", "Enfermeira de Triagem", 2021, ("Enfermagem", UNI, 2018)),
    _pessoa("p11", "Dr. Thiago Pacheco", "Médico", "Ortopedista",
            "Avaliação ortopédica remota e orientação de reabilitação.",
            [("Ortopedia", 5), ("Teleconsulta", 3)],
            "Núcleo Saúde Digital", "Ortopedista", 2016, ("Medicina", UNI, 2010)),
    _pessoa("p12", "Dra. Larissa Freitas", "Médica", "Geriatra",
            "Cuidado de idosos com apoio de telemonitoramento domiciliar.",
            [("Geriatria", 5), ("Telemonitoramento", 4), ("Saúde Mental Digital", 3)],
            "Hospital Virtual Aurora", "Geriatra", 2013, ("Medicina", UNI, 2006)),
]

# Cada par é criado uma única vez, na direção (a)->(b); as consultas tratam a relação como mútua.
CONEXOES = [
    ("p01", "p02"), ("p01", "p03"), ("p01", "p07"),
    ("p02", "p04"), ("p02", "p05"),
    ("p03", "p10"), ("p05", "p10"),
    ("p04", "p06"), ("p06", "p09"),
    ("p07", "p12"), ("p08", "p12"),
    ("p09", "p11"), ("p08", "p11"),
]

POSTS = [
    ("p01", "Boas práticas para teleconsulta cardiológica: confirme sempre a identidade e o contexto do paciente.", ["teleconsulta", "cardiologia"], 7),
    ("p03", "Roteiro de telemonitoramento diário: sinais de alerta e quando escalar para o médico responsável.", ["telemonitoramento", "enfermagem"], 5),
    ("p04", "Exemplo (fictício) de como fotografar lesões de pele para teledermatologia com boa iluminação.", ["dermatologia", "teleconsulta"], 4),
    ("p06", "Acolhimento em saúde mental online: combine canal alternativo caso a conexão caia.", ["saude-mental", "teleconsulta"], 6),
    ("p08", "Lembrete de LGPD: nunca compartilhe dados de pacientes por aplicativos de mensagem pessoais.", ["lgpd", "seguranca"], 9),
    ("p05", "Dicas para teleconsulta pediátrica: peça que um adulto acompanhe e posicione bem a câmera.", ["pediatria", "teleconsulta"], 3),
    ("p12", "Telemonitoramento domiciliar de idosos: equilíbrio entre autonomia e segurança.", ["geriatria", "telemonitoramento"], 2),
    ("p02", "Quando encaminhar um caso: critérios de triagem para especialista em teleinterconsulta.", ["encaminhamento", "clinica-geral"], 4),
]
