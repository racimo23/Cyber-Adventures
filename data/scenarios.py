SCENARIOS = [
    {
        "id": "scene_1",
        "day": 1,
        "title": "Premier email d'activation",
        "category": "phishing",
        "difficulty": "Facile",
        "subtitle": "Jour 1 — Premier email d’activation chez NovaCorp",
        "scene_card": {
            "title": "🏢 Bienvenue chez NovaCorp",
            "body": (
                "Tu incarnes Alice, une nouvelle employée qui commence sa première journée. "
                "Elle découvre les outils internes, les procédures et ses premiers accès."
            ),
        },
        "dialogues": [
            {
                "speaker": "Bob",
                "text": (
                    "Salut Alice, bienvenue chez NovaCorp ! Le support IT va sûrement "
                    "t’envoyer un email pour activer ton compte. Fais-le rapidement, "
                    "sinon tu risques de ne pas pouvoir accéder aux outils."
                ),
            },
            {
                "speaker": "Narrateur",
                "text": "Quelques minutes plus tard, Alice reçoit un email marqué comme urgent.",
            },
        ],
        "artifact": {
            "type": "email",
            "sender": "support-it@novacorp-login.com",
            "recipient": "alice@novacorp.local",
            "subject": "Activation urgente de votre compte",
            "body": (
                "Bonjour Alice,<br><br>"
                "Votre compte NovaCorp sera désactivé dans <strong>30 minutes</strong> "
                "si vous ne confirmez pas vos informations.<br><br>"
                "Cliquez ici pour activer votre accès :<br>"
                "<strong>https://novacorp-login.com/activate</strong><br><br>"
                "Cordialement,<br>Support IT"
            ),
        },
        "choices": [
            {
                "label": "A. Cliquer sur le lien",
                "score_delta": -25,
                "risk_delta": 45,
                "outcome": "danger",
                "feedback": "Tu as cliqué sur un lien de phishing.",
                "consequence_title": "Compte compromis",
                "consequence_story": (
                    "Le lien ouvre un faux portail NovaCorp. Alice saisit ses identifiants. "
                    "Quelques minutes plus tard, Eve utilise ces identifiants pour tenter "
                    "une connexion au VPN de l’entreprise. Une alerte est déclenchée : "
                    "le compte d’Alice est considéré comme compromis."
                ),
                "lesson": (
                    "Ne clique jamais sur un lien d’activation reçu par email sans vérifier le domaine. "
                    "En cas de doute, accède au service via l’adresse officielle ou contacte l’IT."
                ),
            },
            {
                "label": "B. Vérifier le domaine et contacter l’IT",
                "score_delta": 10,
                "risk_delta": -10,
                "outcome": "success",
                "feedback": "Tu as identifié un domaine suspect.",
                "consequence_title": "Menace évitée",
                "consequence_story": (
                    "Alice remarque que le domaine novacorp-login.com ne correspond pas au domaine officiel. "
                    "Elle contacte Charlie du support IT via l’annuaire interne. Charlie confirme qu’il s’agit "
                    "d’une tentative de phishing et bloque le domaine dans la passerelle de messagerie."
                ),
                "lesson": (
                    "Les attaquants utilisent souvent des domaines ressemblants. "
                    "Il faut vérifier l’expéditeur, le lien, le ton du message et l’urgence imposée."
                ),
            },
            {
                "label": "C. Répondre avec ses identifiants",
                "score_delta": -35,
                "risk_delta": 60,
                "outcome": "danger",
                "feedback": "Tu as transmis des informations sensibles par email.",
                "consequence_title": "Identifiants exposés",
                "consequence_story": (
                    "Alice répond à l’email avec son identifiant. L’attaquant confirme que la boîte mail est active "
                    "et tente ensuite d’obtenir le mot de passe via un second message. "
                    "Le risque de compromission augmente fortement."
                ),
                "lesson": (
                    "Aucun support IT légitime ne doit demander un mot de passe ou des informations sensibles par email. "
                    "Les identifiants doivent rester strictement personnels."
                ),
            },
        ],
    }
]